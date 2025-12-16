from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Callable

from .json_utils import safe_json_loads
from .llm_client import OllamaClient
from .memory_store import NovelState, NovelStore
from . import prompts


@dataclass
class PipelineModels:
    planner: str
    writer: str
    editor: str
    evaluator: str


@dataclass
class PipelineConfig:
    chapters: int = 30
    scenes_per_chapter_default: int = 4
    scene_words: int = 900
    tail_chars: int = 1200


def build_prior_memory(state: NovelState, last_n: int = 5) -> str:
    """把最近 N 章摘要+事实作为“稳定记忆”。"""
    mem = state.chapter_memory[-last_n:]
    if not mem:
        return "（无）"

    blocks = []
    for m in mem:
        blocks.append(f"第{m.get('chapter_idx')}章《{m.get('chapter_title')}》摘要：{m.get('summary')}\n事实：" + "；".join(m.get("facts") or []))
        loops = m.get("open_loops") or []
        if loops:
            blocks.append("未解悬念：" + "；".join(loops))
    return "\n\n".join(blocks)


class LongNovelPipeline:
    def __init__(
        self,
        client: OllamaClient,
        store: NovelStore,
        models: PipelineModels,
        config: Optional[PipelineConfig] = None,
    ):
        self.client = client
        self.store = store
        self.models = models
        self.config = config or PipelineConfig()

    def ensure_outline(self, state: NovelState) -> Dict:
        if state.outline_json and state.outline_json.get("chapters"):
            return state.outline_json

        prompt = prompts.prompt_outline(
            requirement=state.requirement,
            story_bible=state.story_bible,
            target_words=state.target_words,
            chapters=self.config.chapters,
        )
        text = self.client.generate(self.models.planner, prompt, temperature=0.4, options={"num_ctx": 8192}, timeout_s=600)
        outline = safe_json_loads(text, default={})
        if not outline or not isinstance(outline.get("chapters"), list):
            # 兜底：至少给一个空章节列表
            outline = outline or {}
            outline.setdefault("chapters", [])
        state.outline_json = outline
        self.store.save_state(state)
        return outline

    def run(
        self,
        state: NovelState,
        on_story_chunk: Callable[[str], None],
        on_think_chunk: Callable[[str], None],
        is_cancelled: Callable[[], bool],
        log: Callable[[str], None],
    ) -> None:
        outline = self.ensure_outline(state)
        chapters: List[Dict] = outline.get("chapters") or []
        if not chapters:
            # 没拿到结构化章节，降级为固定章结构
            chapters = [
                {
                    "idx": i + 1,
                    "title": f"第{i+1}章",
                    "goal": "推进主线并制造新的情感张力",
                    "conflict": "外部阻碍与内心矛盾交织",
                    "turning": "出现新的信息或误会",
                    "hook": "留下下一章的悬念",
                    "scene_count": self.config.scenes_per_chapter_default,
                }
                for i in range(self.config.chapters)
            ]
            outline["chapters"] = chapters
            state.outline_json = outline
            self.store.save_state(state)

        # 从已写章节继续
        already = len(state.chapters)
        total_written_chars = 0
        for m in state.chapters:
            total_written_chars += int(m.get("chars", 0))

        for chap in chapters[already:]:
            if is_cancelled():
                log("已停止：用户取消")
                break

            chap_idx = int(chap.get("idx") or (already + 1))
            log(f"开始生成：第{chap_idx}章 {chap.get('title','')}")

            prior_memory = build_prior_memory(state, last_n=5)

            # 1) 生成场景卡
            scene_prompt = prompts.prompt_scene_list(
                requirement=state.requirement,
                story_bible=state.story_bible,
                style_guide=state.style_guide,
                chapter=chap,
                prior_memory=prior_memory,
            )
            scene_text = self.client.generate(self.models.planner, scene_prompt, temperature=0.4, options={"num_ctx": 8192}, timeout_s=600)
            scene_json = safe_json_loads(scene_text, default={})
            scenes = scene_json.get("scenes") if isinstance(scene_json, dict) else None
            if not scenes:
                # 兜底：生成固定场景卡
                sc = int(chap.get("scene_count") or self.config.scenes_per_chapter_default)
                scenes = [
                    {
                        "scene_idx": i + 1,
                        "goal": "推进情节并推动关系变化",
                        "conflict": "信息不对称或外部压力",
                        "setting": "（由作者自行补全具体时空）",
                        "characters": [],
                        "must_include": [],
                        "end_hook": "留下下一步行动的动力",
                        "target_words": self.config.scene_words,
                    }
                    for i in range(sc)
                ]

            # 2) 逐场景写作（流式）
            chapter_draft_parts: List[str] = []
            recent_tail = ""
            for scene in scenes:
                if is_cancelled():
                    log("已停止：用户取消")
                    break

                scene.setdefault("target_words", self.config.scene_words)
                write_prompt = prompts.prompt_write_scene(
                    requirement=state.requirement,
                    story_bible=state.story_bible,
                    style_guide=state.style_guide,
                    chapter=chap,
                    scene=scene,
                    prior_memory=prior_memory,
                    recent_tail=recent_tail[-self.config.tail_chars :] if recent_tail else "（无）",
                )

                buf = []
                for item in self.client.generate_stream(self.models.writer, write_prompt, temperature=0.7, options={"num_ctx": 8192}):
                    if is_cancelled():
                        break
                    chunk = item.get("response", "")
                    if chunk:
                        # 这里不解析 think，由 UI 侧负责（为了复用现有逻辑）
                        buf.append(chunk)
                        on_story_chunk(chunk)
                    if item.get("done"):
                        break

                if is_cancelled():
                    break

                scene_text_out = "".join(buf).strip()
                if scene_text_out:
                    chapter_draft_parts.append(scene_text_out)
                    recent_tail = scene_text_out

            if is_cancelled():
                break

            chapter_draft = "\n\n".join([p for p in chapter_draft_parts if p.strip()]).strip()
            if not chapter_draft:
                log("本章生成为空，跳过")
                continue

            # 3) 章节编辑润色（非流式）
            edit_prompt = prompts.prompt_edit_chapter(
                requirement=state.requirement,
                story_bible=state.story_bible,
                style_guide=state.style_guide,
                chapter=chap,
                draft_text=chapter_draft,
                prior_memory=prior_memory,
            )
            edited = self.client.generate(self.models.editor, edit_prompt, temperature=0.3, options={"num_ctx": 8192}, timeout_s=900)
            chapter_final = (edited or chapter_draft).strip()

            # 4) 写入文件 & 更新 state
            self.store.save_chapter_text(state.novel_id, chap_idx, chapter_final)
            state.chapters.append({"idx": chap_idx, "title": chap.get("title", ""), "chars": len(chapter_final)})

            # 5) 章节摘要记忆（JSON）
            sum_prompt = prompts.prompt_summarize_chapter(
                requirement=state.requirement,
                story_bible=state.story_bible,
                chapter_idx=chap_idx,
                chapter_title=chap.get("title", ""),
                chapter_text=chapter_final,
            )
            sum_text = self.client.generate(self.models.editor, sum_prompt, temperature=0.2, options={"num_ctx": 8192}, timeout_s=600)
            mem = safe_json_loads(sum_text, default={})
            if isinstance(mem, dict) and mem.get("summary"):
                state.chapter_memory.append(mem)

            self.store.save_state(state)

            # 6) 按章评估（可在 UI 上展示）
            eval_prompt = prompts.prompt_evaluate_chapter(state.requirement, state.story_bible, chapter_final)
            eval_text = self.client.generate(self.models.evaluator, eval_prompt, temperature=0.2, options={"num_ctx": 8192}, timeout_s=600)
            log(f"第{chap_idx}章评估：\n{eval_text}")

            total_written_chars += len(chapter_final)
            if state.target_words and total_written_chars >= state.target_words:
                log("已达到目标字数，停止后续章节")
                break

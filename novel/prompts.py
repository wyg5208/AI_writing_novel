from typing import List, Dict


def prompt_outline(requirement: str, story_bible: str, target_words: int, chapters: int) -> str:
    return f"""
你是资深长篇小说策划编辑，请为一部长篇言情小说制定可执行的大纲。

【硬性要求】
- 使用中文。
- 保持人物、设定、时间线自洽，不要随意新增与既有设定冲突的信息。
- 输出必须为严格 JSON（不要额外解释），字段结构如下：
{{
  \"logline\": str,
  \"theme\": str,
  \"tone\": str,
  \"pov\": str,
  \"style_notes\": str,
  \"chapters\": [
    {{\"idx\": int, \"title\": str, \"goal\": str, \"conflict\": str, \"turning\": str, \"hook\": str, \"scene_count\": int}}
  ]
}}

【用户写作要求】
{requirement}

【故事圣经（不可违背设定）】
{story_bible}

【目标】
- 预计总字数：约 {target_words} 字
- 章节数：{chapters} 章（每章约 {max(800, target_words // max(1, chapters))} 字，允许浮动）

请开始输出 JSON。
""".strip()


def prompt_scene_list(requirement: str, story_bible: str, style_guide: str, chapter: Dict, prior_memory: str) -> str:
    return f"""
你是长篇小说分镜编剧，请为指定章节产出\"场景卡\"列表，用于逐场景写作。

【硬性要求】
- 使用中文。
- 不要空泛，不要重复前情；每个场景必须推进情节/信息/关系至少一项。
- 输出必须为严格 JSON（不要额外解释），结构：
{{
  \"chapter_idx\": int,
  \"chapter_title\": str,
  \"scenes\": [
    {{
      \"scene_idx\": int,
      \"goal\": str,
      \"conflict\": str,
      \"setting\": str,
      \"characters\": [str],
      \"must_include\": [str],
      \"end_hook\": str,
      \"target_words\": int
    }}
  ]
}}

【用户写作要求】
{requirement}

【故事圣经（不可违背设定）】
{story_bible}

【风格/人称/节奏约束】
{style_guide}

【前文记忆（摘要+事实清单）】
{prior_memory}

【本章信息】
idx: {chapter.get('idx')}\ntitle: {chapter.get('title')}\ngoal: {chapter.get('goal')}\nconflict: {chapter.get('conflict')}\nturning: {chapter.get('turning')}\nhook: {chapter.get('hook')}

请开始输出 JSON。
""".strip()


def prompt_write_scene(requirement: str, story_bible: str, style_guide: str, chapter: Dict, scene: Dict, prior_memory: str, recent_tail: str) -> str:
    must_include = "\n".join([f"- {x}" for x in (scene.get("must_include") or [])])
    chars = "、".join(scene.get("characters") or [])
    return f"""
你是职业畅销言情小说作者。请\"只写\"本场景的正文，不要任何解释、不要标题列表、不要输出 JSON。

【硬性要求】
- 使用中文。
- 人称/时态/口吻保持一致：{style_guide}
- 不要复述前情，不要注水；对话要推动关系与信息。
- 不要改写\"故事圣经\"里不可违背的设定。
- 本场景结尾要自然导向：{scene.get('end_hook')}

【用户写作要求】
{requirement}

【故事圣经（不可违背设定）】
{story_bible}

【前文记忆（摘要+事实清单）】
{prior_memory}

【本章目标】
{chapter.get('title')}：{chapter.get('goal')}（冲突：{chapter.get('conflict')}，转折：{chapter.get('turning')}）

【本场景卡】
- 场景目标：{scene.get('goal')}
- 场景冲突：{scene.get('conflict')}
- 时空：{scene.get('setting')}
- 出场人物：{chars}
- 必须出现的信息/道具/伏笔：
{must_include if must_include else '-（无）'}
- 目标字数：约 {scene.get('target_words', 900)} 字

【最近正文末尾（用于承接语气与动作，不要复述）】
{recent_tail}

现在开始写正文：
""".strip()


def prompt_edit_chapter(requirement: str, story_bible: str, style_guide: str, chapter: Dict, draft_text: str, prior_memory: str) -> str:
    return f"""
你是资深小说责任编辑。请在\"不改设定、不改主线\"的前提下，对本章进行编辑润色与一致性修补。

【硬性要求】
- 使用中文。
- 只输出\"修改后的完整章节正文\"，不要解释、不要对比、不要列清单。
- 修复：逻辑跳跃、人物动机突变、时间线不连贯、重复啰嗦、对白不自然。
- 保留：关键事件与信息点（伏笔/转折/钩子）。

【用户写作要求】
{requirement}

【故事圣经（不可违背设定）】
{story_bible}

【风格约束】
{style_guide}

【前文记忆（摘要+事实清单）】
{prior_memory}

【本章信息】
{chapter}

【本章初稿】
{draft_text}
""".strip()


def prompt_summarize_chapter(requirement: str, story_bible: str, chapter_idx: int, chapter_title: str, chapter_text: str) -> str:
    return f"""
你是长篇小说\"记忆整理\"助手。请把本章压缩为稳定的上下文记忆，便于后续续写保持一致。

【硬性要求】
- 使用中文。
- 不要编造未发生内容。
- 输出必须为严格 JSON（不要额外解释），结构：
{{
  \"chapter_idx\": int,
  \"chapter_title\": str,
  \"summary\": str,              // 200-400字
  \"facts\": [str],              // 8-15条，可核验事实（人物/关系/地点/道具/决定/结果）
  \"open_loops\": [str]          // 3-8条未解决悬念/待回收伏笔
}}

【用户写作要求】
{requirement}

【故事圣经（不可违背设定）】
{story_bible}

【本章正文】
{chapter_text}

请开始输出 JSON。
""".strip()


def prompt_evaluate_chapter(requirement: str, story_bible: str, chapter_text: str) -> str:
    return f"""
你是专业小说审稿编辑，请对\"这一章\"做可执行的质量评估。

【硬性要求】
- 使用中文。
- 先指出\"具体问题点\"（引用短句/段落特征），再给\"可操作修改建议\"。
- 重点检查：人物一致性、时间线/因果、节奏与信息密度、对白是否推动关系与情节。

【输出格式】
- 总体评分: X/10
- 连贯性: X/10
- 人物一致性: X/10
- 节奏/信息密度: X/10
- 语言表达: X/10

## 问题清单（按严重程度）
1. ...

## 修改建议（尽量具体到如何改）
- ...

【用户写作要求】
{requirement}

【故事圣经（不可违背设定）】
{story_bible}

【章节正文】
{chapter_text}
""".strip()

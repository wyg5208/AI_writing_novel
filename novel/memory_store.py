import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


def _now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


@dataclass
class ChapterMemory:
    idx: int
    title: str
    summary: str
    facts: List[str] = field(default_factory=list)
    open_loops: List[str] = field(default_factory=list)


@dataclass
class NovelState:
    novel_id: str
    requirement: str
    target_words: int
    style_guide: str
    story_bible: str
    outline_json: Dict[str, Any] = field(default_factory=dict)
    chapters: List[Dict[str, Any]] = field(default_factory=list)  # metadata
    chapter_memory: List[Dict[str, Any]] = field(default_factory=list)


class NovelStore:
    def __init__(self, base_dir: str = "generated_novels"):
        self.base_dir = base_dir

    def create_new(self, requirement: str, target_words: int, story_bible: str, style_guide: str) -> NovelState:
        novel_id = f"novel_{_now_ts()}"
        state = NovelState(
            novel_id=novel_id,
            requirement=requirement,
            target_words=target_words,
            story_bible=story_bible,
            style_guide=style_guide,
        )
        self.save_state(state)
        return state

    def novel_dir(self, novel_id: str) -> str:
        return os.path.join(self.base_dir, novel_id)

    def state_path(self, novel_id: str) -> str:
        return os.path.join(self.novel_dir(novel_id), "state.json")

    def ensure_dirs(self, novel_id: str) -> None:
        os.makedirs(self.novel_dir(novel_id), exist_ok=True)
        os.makedirs(os.path.join(self.novel_dir(novel_id), "chapters"), exist_ok=True)

    def save_state(self, state: NovelState) -> None:
        self.ensure_dirs(state.novel_id)
        path = self.state_path(state.novel_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state.__dict__, f, ensure_ascii=False, indent=2)

    def load_state(self, novel_id: str) -> Optional[NovelState]:
        path = self.state_path(novel_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return NovelState(**data)

    def list_novels(self) -> List[str]:
        if not os.path.exists(self.base_dir):
            return []
        items = []
        for name in os.listdir(self.base_dir):
            if name.startswith("novel_") and os.path.isdir(os.path.join(self.base_dir, name)):
                items.append(name)
        return sorted(items, reverse=True)

    def save_chapter_text(self, novel_id: str, chapter_idx: int, text: str) -> str:
        self.ensure_dirs(novel_id)
        path = os.path.join(self.novel_dir(novel_id), "chapters", f"chapter_{chapter_idx:03d}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def load_chapter_text(self, novel_id: str, chapter_idx: int) -> str:
        path = os.path.join(self.novel_dir(novel_id), "chapters", f"chapter_{chapter_idx:03d}.md")
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

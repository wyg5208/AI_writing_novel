import json
import re
from typing import Any, Optional


def extract_first_json(text: str) -> Optional[str]:
    """从模型输出中尽量提取第一段 JSON（支持 ```json 包裹）。"""
    if not text:
        return None

    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", text, re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()

    # 尝试找到第一段 { ... } 或 [ ... ] 的平衡片段（简化版）
    start_obj = text.find("{")
    start_arr = text.find("[")
    if start_obj == -1 and start_arr == -1:
        return None

    start = start_obj if (start_arr == -1 or (start_obj != -1 and start_obj < start_arr)) else start_arr
    open_ch = text[start]
    close_ch = "}" if open_ch == "{" else "]"

    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
            continue

        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start : i + 1].strip()

    return None


def safe_json_loads(text: str, default: Any = None) -> Any:
    """尽量把文本解析为 JSON，失败返回 default。"""
    if text is None:
        return default

    try:
        return json.loads(text)
    except Exception:
        extracted = extract_first_json(text)
        if not extracted:
            return default
        try:
            return json.loads(extracted)
        except Exception:
            return default

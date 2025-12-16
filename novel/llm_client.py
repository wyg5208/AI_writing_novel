import json
from dataclasses import dataclass
from typing import Dict, Iterator, Optional

import requests


@dataclass
class LLMConfig:
    base_url: str = "http://localhost:11434"
    timeout_s: int = 120


class OllamaClient:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()

    def generate_stream(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        options: Optional[Dict] = None,
    ) -> Iterator[Dict]:
        """流式生成：yield {response:str, done:bool, raw:dict}。"""
        url = f"{self.config.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": True,
        }
        if options:
            payload["options"] = options

        resp = requests.post(url, json=payload, stream=True, timeout=self.config.timeout_s)
        resp.raise_for_status()

        for line in resp.iter_lines():
            if not line:
                continue
            data = json.loads(line.decode("utf-8"))
            yield {
                "response": data.get("response", ""),
                "done": bool(data.get("done", False)),
                "raw": data,
            }

    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.3,
        options: Optional[Dict] = None,
        timeout_s: Optional[int] = None,
    ) -> str:
        """非流式生成。"""
        url = f"{self.config.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
        }
        if options:
            payload["options"] = options

        resp = requests.post(url, json=payload, timeout=timeout_s or self.config.timeout_s)
        resp.raise_for_status()
        return (resp.json().get("response") or "").strip()

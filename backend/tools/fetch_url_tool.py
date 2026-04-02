from __future__ import annotations

import json
from typing import ClassVar

import html2text
import requests
from pydantic import BaseModel, Field, PrivateAttr

from langchain_core.tools import BaseTool


class FetchUrlInput(BaseModel):
    url: str = Field(..., description="需要抓取的 URL")


class FetchUrlTool(BaseTool):
    name: str = "fetch_url"
    description: str = "抓取网页或 JSON 接口内容并返回简化后的文本。"
    args_schema: ClassVar[type[BaseModel]] = FetchUrlInput
    timeout_seconds: int = 15
    max_output_chars: int = 5000
    _converter: html2text.HTML2Text = PrivateAttr()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._converter = html2text.HTML2Text()
        self._converter.ignore_links = False
        self._converter.ignore_images = True

    def _run(self, url: str) -> str:
        response = requests.get(url, timeout=self.timeout_seconds, headers={"User-Agent": "mini-openclaw/1.0"})
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            payload = response.json()
            text = json.dumps(payload, ensure_ascii=False, indent=2)
        elif "text/html" in content_type or "<html" in response.text.lower():
            text = self._converter.handle(response.text)
        else:
            text = response.text

        return text[: self.max_output_chars] + ("\n...[truncated]" if len(text) > self.max_output_chars else "")

    async def _arun(self, url: str) -> str:
        return self._run(url)

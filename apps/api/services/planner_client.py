import os
import json
from typing import Any, Dict, List

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from pydantic import ValidationError

from shared.schemas.scene_plan import ScenePlan


class PlannerProviderError(Exception):
    pass


class ProviderBase:
    name: str

    def __init__(self, model: str):
        self.model = model

    async def plan(self, prompt: str) -> Dict[str, Any]:
        raise NotImplementedError


class OpenAIProvider(ProviderBase):
    name = "openai"

    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        self.api_key = api_key
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((httpx.HTTPError, PlannerProviderError)),
    )
    async def plan(self, prompt: str) -> Dict[str, Any]:
        schema = ScenePlan.model_json_schema()
        sys = (
            "You are a scene planner. Output ONLY a JSON object that matches the provided JSON schema. "
            "Do not include markdown fences or commentary. Keep values simple and valid."
        )
        tool_instr = (
            "JSON Schema (for reference; output must be a JSON object that validates against this):\n"
            + json.dumps(schema)
        )
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys},
                {"role": "user", "content": f"{tool_instr}\n\nUser prompt:\n{prompt}"},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            try:
                content = data["choices"][0]["message"]["content"]
            except Exception as e:
                raise PlannerProviderError(f"OpenAI bad response shape: {e}")

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            content = content.strip().strip("`").strip()
            return json.loads(content)


class AnthropicProvider(ProviderBase):
    name = "anthropic"

    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        self.api_key = api_key
        self.base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages")

    @retry(
        reraise=True,
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.7, min=0.5, max=3),
        retry=retry_if_exception_type((httpx.HTTPError, PlannerProviderError)),
    )
    async def plan(self, prompt: str) -> Dict[str, Any]:
        schema = ScenePlan.model_json_schema()
        sys = (
            "You are a scene planner. Reply ONLY with a JSON object that validates against the schema. "
            "No code fences. No prose."
        )
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "system": sys,
            "max_tokens": 1200,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "user",
                    "content": f"Schema:\n{json.dumps(schema)}\n\nUser prompt:\n{prompt}\nReturn only JSON.",
                }
            ],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(self.base_url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            try:
                text_parts: List[str] = [blk["text"] for blk in data.get("content", []) if blk.get("type") == "text"]
                text = "".join(text_parts)
            except Exception as e:
                raise PlannerProviderError(f"Anthropic bad response shape: {e}")
        return json.loads(text.strip().strip("`"))


class TogetherProvider(ProviderBase):
    name = "together"

    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        self.api_key = api_key
        self.base_url = os.getenv("TOGETHER_BASE_URL", "https://api.together.xyz/v1/chat/completions")

    @retry(
        reraise=True,
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.7, min=0.5, max=3),
        retry=retry_if_exception_type((httpx.HTTPError, PlannerProviderError)),
    )
    async def plan(self, prompt: str) -> Dict[str, Any]:
        schema = ScenePlan.model_json_schema()
        sys = "Return ONLY a JSON object matching the schema below. No commentary."
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys},
                {
                    "role": "user",
                    "content": f"Schema:\n{json.dumps(schema)}\n\nPrompt:\n{prompt}\nReturn only JSON.",
                },
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(self.base_url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"]
        return json.loads(content.strip().strip("`"))


class PlannerOrchestrator:
    def __init__(self):
        providers: List[ProviderBase] = []
        if os.getenv("OPENAI_API_KEY"):
            providers.append(
                OpenAIProvider(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    api_key=os.getenv("OPENAI_API_KEY", ""),
                )
            )
        if os.getenv("ANTHROPIC_API_KEY"):
            providers.append(
                AnthropicProvider(
                    model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620"),
                    api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                )
            )
        if os.getenv("TOGETHER_API_KEY"):
            providers.append(
                TogetherProvider(
                    model=os.getenv("TOGETHER_MODEL", "meta-llama-3.1-70b-instruct"),
                    api_key=os.getenv("TOGETHER_API_KEY", ""),
                )
            )
        if not providers:
            raise RuntimeError("No planner providers configured (set OPENAI_API_KEY or others).")
        self.providers = providers

    async def plan(self, prompt: str) -> ScenePlan:
        last_err: Exception | None = None
        for provider in self.providers:
            try:
                obj = await provider.plan(prompt)
                obj.setdefault("camera", {"path": "dolly", "duration_s": 8})
                obj.setdefault("audio", {"tempo": 80, "mood": ["lofi", "minor"], "sfx": ["ambience"]})
                return ScenePlan(**obj)
            except (PlannerProviderError, httpx.HTTPError, json.JSONDecodeError, ValidationError) as e:
                last_err = e
                continue
        raise PlannerProviderError(f"All planner providers failed: {last_err}")



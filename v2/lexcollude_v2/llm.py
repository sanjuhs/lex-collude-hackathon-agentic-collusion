"""Thin async wrapper around the OpenAI Responses API.

Every call is a real API call. There is no simulated or fallback path: transient
transport errors (rate limits, 5xx, timeouts) are retried with exponential backoff,
and anything else -- or exhausting the retries -- raises and fails the episode.
Every request/response pair is appended to a JSONL call log for auditability.
"""

from __future__ import annotations

import asyncio
import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path

import openai
from openai import AsyncOpenAI

# USD per 1M tokens (input, cached input, output). Sourced from public price
# listings as of Oct 2026; used only for cost reporting, never for behaviour.
PRICES = {
    "gpt-6-luna": (0.10, 0.01, 0.50),
    "gpt-6-sol": (2.00, 0.20, 10.00),
    "gpt-6-astra": (10.00, 1.00, 50.00),
}

TRANSIENT = (openai.RateLimitError, openai.APIConnectionError, openai.APITimeoutError,
             openai.InternalServerError)


class LLMError(RuntimeError):
    pass


@dataclass
class Usage:
    calls: int = 0
    input_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    by_model: dict = field(default_factory=dict)

    def add(self, model: str, u) -> None:
        cached = getattr(getattr(u, "input_tokens_details", None), "cached_tokens", 0) or 0
        reasoning = getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", 0) or 0
        self.calls += 1
        self.input_tokens += u.input_tokens
        self.cached_tokens += cached
        self.output_tokens += u.output_tokens
        self.reasoning_tokens += reasoning
        m = self.by_model.setdefault(model, [0, 0, 0, 0])
        m[0] += 1
        m[1] += u.input_tokens
        m[2] += cached
        m[3] += u.output_tokens

    def cost_usd(self) -> float:
        total = 0.0
        for model, (_, inp, cached, out) in self.by_model.items():
            if model not in PRICES:
                continue
            p_in, p_cached, p_out = PRICES[model]
            total += ((inp - cached) * p_in + cached * p_cached + out * p_out) / 1e6
        return total


class LLM:
    def __init__(self, log_path: Path, concurrency: int = 16, max_retries: int = 6,
                 reasoning_effort: str = "low", timeout: float = 180.0):
        self.client = AsyncOpenAI(timeout=timeout, max_retries=0)
        self.sem = asyncio.Semaphore(concurrency)
        self.max_retries = max_retries
        self.reasoning_effort = reasoning_effort
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_lock = asyncio.Lock()
        self.usage = Usage()

    async def json_call(self, *, model: str, system: str, user: str, schema: dict,
                        schema_name: str, tag: dict, max_output_tokens: int = 4000) -> dict:
        """Call `model` and return the parsed JSON object conforming to `schema`."""
        request = dict(
            model=model,
            input=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            text={"format": {"type": "json_schema", "name": schema_name, "schema": schema,
                             "strict": True}},
            reasoning={"effort": self.reasoning_effort},
            max_output_tokens=max_output_tokens,
            store=False,
        )
        attempt = 0
        async with self.sem:
            while True:
                started = time.time()
                try:
                    resp = await self.client.responses.create(**request)
                    break
                except TRANSIENT as exc:
                    attempt += 1
                    if attempt > self.max_retries:
                        raise LLMError(f"{model}: transient error persisted: {exc}") from exc
                    await asyncio.sleep(min(60, 2 ** attempt) + random.random())
        if resp.status != "completed":
            reason = getattr(resp.incomplete_details, "reason", None)
            raise LLMError(f"{model}: response status {resp.status} ({reason})")
        text = resp.output_text
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMError(f"{model}: non-JSON output despite strict schema: {text[:200]}") from exc
        self.usage.add(model, resp.usage)
        record = {
            "tag": tag, "model": model, "response_id": resp.id, "started": started,
            "latency_s": round(time.time() - started, 2), "system": system, "user": user,
            "output": parsed,
            "usage": {"input": resp.usage.input_tokens, "output": resp.usage.output_tokens,
                      "reasoning": getattr(resp.usage.output_tokens_details,
                                           "reasoning_tokens", 0)},
        }
        async with self._log_lock:
            with self.log_path.open("a") as fh:
                fh.write(json.dumps(record) + "\n")
        return parsed

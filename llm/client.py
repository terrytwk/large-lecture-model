"""Anthropic Claude client with prompt caching and streaming."""
from __future__ import annotations
import os
from anthropic import Anthropic

_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


class LLMClient:
    def __init__(self, model: str = "claude-sonnet-4-6", max_tokens: int = 2048) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.client = get_client()

    def complete(self, system: str, user: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            # cache_control marks the system prompt for prompt caching
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text  # type: ignore[union-attr]

    def stream(self, system: str, messages: list[dict]):
        """Yield text deltas for streaming responses."""
        with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
        ) as stream:
            yield from stream.text_stream

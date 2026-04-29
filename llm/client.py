"""LLM backend: Anthropic SDK when API key is present, `claude -p` CLI otherwise."""
from __future__ import annotations
import json
import os
import shutil
import subprocess
from typing import Iterator


# ── Anthropic SDK backend ──────────────────────────────────────────────────────

class _AnthropicBackend:
    def __init__(self, model: str, max_tokens: int) -> None:
        from anthropic import Anthropic
        self._client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model
        self.max_tokens = max_tokens

    def _system_block(self, system: str) -> list[dict]:
        return [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]

    def complete(self, system: str, user: str) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self._system_block(system),
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text  # type: ignore[union-attr]

    def stream(self, system: str, messages: list[dict]) -> Iterator[str]:
        with self._client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self._system_block(system),
            messages=messages,
        ) as s:
            yield from s.text_stream


# ── claude CLI backend ─────────────────────────────────────────────────────────

class _CliBackend:
    """Shells out to `claude -p` — no API key needed, uses your logged-in session."""

    def __init__(self, model: str) -> None:
        self.model = model
        cli = shutil.which("claude")
        if not cli:
            raise RuntimeError(
                "`claude` CLI not found on PATH. "
                "Install Claude Code or set ANTHROPIC_API_KEY."
            )
        self._cli = cli

    def _base_cmd(self) -> list[str]:
        # --dangerously-skip-permissions: non-interactive, no tool confirmations needed
        return [self._cli, "--print", "--dangerously-skip-permissions", "--model", self.model]

    def complete(self, system: str, user: str) -> str:
        cmd = self._base_cmd() + ["--system-prompt", system, user]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "(no output)"
            raise RuntimeError(f"claude CLI failed (exit {result.returncode}): {detail}")
        return result.stdout.strip()

    def stream(self, system: str, messages: list[dict]) -> Iterator[str]:
        user_prompt = _messages_to_prompt(messages)
        cmd = self._base_cmd() + [
            "--system-prompt", system,
            "--verbose",
            "--output-format", "stream-json",
            "--include-partial-messages",
            user_prompt,
        ]
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        )
        yielded = 0
        for raw in proc.stdout:  # type: ignore[union-attr]
            raw = raw.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            etype = event.get("type")
            if etype == "stream_event":
                ev = event.get("event", {})
                if ev.get("type") == "content_block_delta":
                    delta = ev.get("delta", {})
                    if delta.get("type") == "text_delta":
                        text: str = delta.get("text", "")
                        if text:
                            yield text
                            yielded += len(text)
            elif etype == "result" and yielded == 0:
                # Fallback if no streaming deltas were received
                tail: str = event.get("result", "")
                if tail:
                    yield tail
        proc.wait()


# ── public interface ───────────────────────────────────────────────────────────

def _messages_to_prompt(messages: list[dict]) -> str:
    """Flatten a multi-turn history list into a plain-text prompt for the CLI."""
    parts: list[str] = []
    for m in messages:
        role = m["role"].capitalize()
        content = m["content"]
        if isinstance(content, list):
            content = " ".join(
                b.get("text", "") for b in content if isinstance(b, dict)
            )
        parts.append(f"{role}: {content}")
    return "\n\n".join(parts)


class LLMClient:
    def __init__(self, model: str = "claude-sonnet-4-6", max_tokens: int = 2048) -> None:
        self.model = model
        self.max_tokens = max_tokens
        if os.environ.get("ANTHROPIC_API_KEY"):
            self._backend: _AnthropicBackend | _CliBackend = _AnthropicBackend(model, max_tokens)
            print("[llm] using Anthropic API")
        else:
            self._backend = _CliBackend(model)
            print("[llm] ANTHROPIC_API_KEY not set — using `claude -p` CLI")

    def complete(self, system: str, user: str) -> str:
        return self._backend.complete(system, user)

    def stream(self, system: str, messages: list[dict]) -> Iterator[str]:
        yield from self._backend.stream(system, messages)

"""LLM provider abstraction.

Provider preference defaults to OpenAI API, then Codex CLI, then Anthropic API,
then Claude CLI. Callers should use LLMClient rather than provider-specific APIs.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterator, Protocol

DEFAULT_PROVIDER = "auto"
DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"


class _Backend(Protocol):
    def complete(self, system: str, user: str) -> str: ...

    def stream(self, system: str, messages: list[dict]) -> Iterator[str]: ...


# ── OpenAI API backend ────────────────────────────────────────────────────────


class _OpenAIBackend:
    def __init__(self, model: str, max_tokens: int) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        resp = self._client.responses.create(
            model=self.model,
            instructions=system,
            input=user,
            max_output_tokens=self.max_tokens,
        )
        text = getattr(resp, "output_text", None)
        if text:
            return text
        return _openai_response_text(resp)

    def stream(self, system: str, messages: list[dict]) -> Iterator[str]:
        input_text = _messages_to_openai_input(messages)
        with self._client.responses.stream(
            model=self.model,
            instructions=system,
            input=input_text,
            max_output_tokens=self.max_tokens,
        ) as stream:
            for event in stream:
                if getattr(event, "type", "") == "response.output_text.delta":
                    delta = getattr(event, "delta", "")
                    if delta:
                        yield delta


def _openai_response_text(resp: object) -> str:
    """Extract text from Responses API objects even if output_text is absent."""
    chunks: list[str] = []
    for item in getattr(resp, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)
    return "".join(chunks)


# ── Anthropic SDK backend ─────────────────────────────────────────────────────


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


# ── CLI backends ──────────────────────────────────────────────────────────────


class _CodexCliBackend:
    """Shells out to `codex exec` using the local logged-in Codex session."""

    def __init__(self, model: str, cwd: str | Path | None = None) -> None:
        self.model = model
        self.cwd = str(cwd or Path.cwd())
        cli = shutil.which("codex")
        if not cli:
            raise RuntimeError(
                "`codex` CLI not found on PATH. Install Codex CLI or set OPENAI_API_KEY."
            )
        self._cli = cli

    def _base_cmd(self) -> list[str]:
        return [
            self._cli,
            "exec",
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--cd",
            self.cwd,
            "--model",
            self.model,
            "-",
        ]

    def complete(self, system: str, user: str) -> str:
        prompt = _cli_prompt(system, user)
        result = subprocess.run(
            self._base_cmd(),
            input=prompt,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "(no output)"
            raise RuntimeError(f"codex exec failed (exit {result.returncode}): {detail}")
        return result.stdout.strip()

    def stream(self, system: str, messages: list[dict]) -> Iterator[str]:
        # `codex exec --json` is event-oriented and version-sensitive. Yielding the
        # final answer preserves the streaming interface without binding to it.
        yield self.complete(system, _messages_to_prompt(messages))


class _ClaudeCliBackend:
    """Shells out to `claude -p` using the local logged-in Claude session."""

    def __init__(self, model: str) -> None:
        self.model = model
        cli = shutil.which("claude")
        if not cli:
            raise RuntimeError(
                "`claude` CLI not found on PATH. Install Claude Code or set ANTHROPIC_API_KEY."
            )
        self._cli = cli

    def _base_cmd(self) -> list[str]:
        return [self._cli, "--print", "--dangerously-skip-permissions", "--model", self.model]

    def complete(self, system: str, user: str) -> str:
        system = system.replace("\x00", "")
        user = user.replace("\x00", "")
        cmd = self._base_cmd() + ["--system-prompt", system, user]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "(no output)"
            raise RuntimeError(f"claude CLI failed (exit {result.returncode}): {detail}")
        return result.stdout.strip()

    def stream(self, system: str, messages: list[dict]) -> Iterator[str]:
        system = system.replace("\x00", "")
        user_prompt = _messages_to_prompt(messages).replace("\x00", "")
        cmd = self._base_cmd() + [
            "--system-prompt",
            system,
            "--verbose",
            "--output-format",
            "stream-json",
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
                tail: str = event.get("result", "")
                if tail:
                    yield tail
        proc.wait()


# ── public interface ──────────────────────────────────────────────────────────


def _messages_to_prompt(messages: list[dict]) -> str:
    """Flatten a multi-turn history list into a plain-text prompt for CLI backends."""
    parts: list[str] = []
    for m in messages:
        role = m["role"].capitalize()
        content = _message_content_to_text(m.get("content", ""))
        parts.append(f"{role}: {content}")
    return "\n\n".join(parts)


def _messages_to_openai_input(messages: list[dict]) -> list[dict]:
    """Normalize local chat messages into Responses API input items."""
    normalized: list[dict] = []
    for message in messages:
        role = message.get("role", "user")
        if role not in {"user", "assistant", "developer", "system"}:
            role = "user"
        normalized.append(
            {
                "role": role,
                "content": _message_content_to_text(message.get("content", "")),
            }
        )
    return normalized


def _message_content_to_text(content: object) -> str:
    if isinstance(content, list):
        return " ".join(
            str(block.get("text", "")) for block in content if isinstance(block, dict)
        )
    return str(content)


def _cli_prompt(system: str, user: str) -> str:
    system = system.replace("\x00", "")
    user = user.replace("\x00", "")
    return f"System instructions:\n{system}\n\nUser request:\n{user}"


def _provider_available(provider: str) -> bool:
    if provider == "openai":
        return bool(os.environ.get("OPENAI_API_KEY"))
    if provider == "codex":
        return shutil.which("codex") is not None
    if provider == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    if provider == "claude":
        return shutil.which("claude") is not None
    return False


def _select_provider(provider: str) -> str:
    requested = (provider or DEFAULT_PROVIDER).lower()
    if requested != "auto":
        return requested
    for candidate in ("openai", "codex", "anthropic", "claude"):
        if _provider_available(candidate):
            return candidate
    raise RuntimeError(
        "No LLM provider available. Set OPENAI_API_KEY, install/log in to `codex`, "
        "set ANTHROPIC_API_KEY, or install/log in to `claude`."
    )


def _model_for_provider(model: str | None, provider: str) -> str:
    if model:
        return model
    if provider in {"anthropic", "claude"}:
        return DEFAULT_ANTHROPIC_MODEL
    return DEFAULT_MODEL


class LLMClient:
    def __init__(
        self,
        model: str | None = None,
        max_tokens: int = 2048,
        provider: str = DEFAULT_PROVIDER,
        cwd: str | Path | None = None,
    ) -> None:
        self.provider = _select_provider(provider)
        self.model = _model_for_provider(model, self.provider)
        self.max_tokens = max_tokens
        self._backend = self._build_backend(cwd)
        print(f"[llm] using {self.provider} backend ({self.model})")

    @classmethod
    def from_config(cls, config: dict, cwd: str | Path | None = None) -> "LLMClient":
        return cls(
            provider=config.get("provider", DEFAULT_PROVIDER),
            model=config.get("model"),
            max_tokens=config.get("max_tokens", 2048),
            cwd=cwd,
        )

    def _build_backend(self, cwd: str | Path | None) -> _Backend:
        if self.provider == "openai":
            return _OpenAIBackend(self.model, self.max_tokens)
        if self.provider == "codex":
            return _CodexCliBackend(self.model, cwd=cwd)
        if self.provider == "anthropic":
            return _AnthropicBackend(self.model, self.max_tokens)
        if self.provider == "claude":
            return _ClaudeCliBackend(self.model)
        raise ValueError(
            "Unsupported LLM provider. Expected one of: auto, openai, codex, anthropic, claude."
        )

    def complete(self, system: str, user: str) -> str:
        return self._backend.complete(system, user)

    def stream(self, system: str, messages: list[dict]) -> Iterator[str]:
        yield from self._backend.stream(system, messages)

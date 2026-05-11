from __future__ import annotations

from types import SimpleNamespace

import pytest

from llm import client


def test_auto_provider_prefers_openai_over_cli_and_anthropic(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(client.shutil, "which", lambda name: f"/usr/bin/{name}")

    assert client._select_provider("auto") == "openai"


def test_auto_provider_prefers_codex_before_anthropic(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(
        client.shutil,
        "which",
        lambda name: "/usr/bin/codex" if name == "codex" else None,
    )

    assert client._select_provider("auto") == "codex"


def test_auto_provider_falls_back_to_claude(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(
        client.shutil,
        "which",
        lambda name: "/usr/bin/claude" if name == "claude" else None,
    )

    assert client._select_provider("auto") == "claude"


def test_auto_provider_errors_when_nothing_available(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(client.shutil, "which", lambda name: None)

    with pytest.raises(RuntimeError, match="No LLM provider available"):
        client._select_provider("auto")


def test_codex_cli_complete_uses_read_only_exec(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(client.shutil, "which", lambda name: "/usr/bin/codex")
    seen: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        seen["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="answer\n", stderr="")

    monkeypatch.setattr(client.subprocess, "run", fake_run)

    backend = client._CodexCliBackend("gpt-test", cwd="/tmp/project")
    assert backend.complete("be terse", "hello") == "answer"

    assert seen["cmd"] == [
        "/usr/bin/codex",
        "exec",
        "--sandbox",
        "read-only",
        "--ephemeral",
        "--cd",
        "/tmp/project",
        "--model",
        "gpt-test",
        "-",
    ]
    kwargs = seen["kwargs"]
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert "System instructions:\nbe terse" in kwargs["input"]
    assert "User request:\nhello" in kwargs["input"]


def test_message_flattening_handles_text_blocks():
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "first"}, {"text": "second"}]},
        {"role": "assistant", "content": "reply"},
    ]

    assert client._messages_to_prompt(messages) == "User: first second\n\nAssistant: reply"
    assert client._messages_to_openai_input(messages) == [
        {"role": "user", "content": "first second"},
        {"role": "assistant", "content": "reply"},
    ]


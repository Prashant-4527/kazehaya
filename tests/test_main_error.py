from types import SimpleNamespace

import anthropic
from rich.console import Console

from alduin import main


def test_llm_failure_rolls_back_the_turn(monkeypatch):
    seen_lengths = []

    def fake_call(client, console, system_prompt, messages, tool_schemas):
        seen_lengths.append(len(messages))
        if len(seen_lengths) == 1:
            raise anthropic.APIConnectionError(request=SimpleNamespace())
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text="hi")],
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        )

    inputs = iter(["first", "second"])

    def fake_input(prompt=""):
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr(main.llm, "call", fake_call)
    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(main.ui, "clear_previous_line", lambda: None)

    main.agent_loop(client=None, console=Console(quiet=True))
    assert seen_lengths == [1, 1]

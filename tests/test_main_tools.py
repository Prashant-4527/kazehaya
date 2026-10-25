from rich.console import Console

from alduin import main


def test_denied_bash_does_not_run(monkeypatch):
    ran = []

    def bash(command: str) -> str:
        ran.append(command)
        return "ok"

    monkeypatch.setattr(main.ui, "confirm", lambda console, message: False)
    result = main.execute_tool(Console(quiet=True), "bash", {"bash": bash}, {"command": "rm x"})
    assert result.startswith("Error")
    assert ran == []

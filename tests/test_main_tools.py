from rich.console import Console

from alduin import main
import io


def test_denied_bash_does_not_run(monkeypatch):
    ran = []

    def bash(command: str) -> str:
        ran.append(command)
        return "ok"

    monkeypatch.setattr(main.ui, "confirm", lambda console, message: False)
    result = main.execute_tool(Console(quiet=True), "bash", {"bash": bash}, {"command": "rm x"})
    assert result.startswith("Error")
    assert ran == []



def test_tool_error_is_shown_as_error():
    console = Console(file=io.StringIO(), record=True, width=90)
    main.execute_tool(console, "read_file", {"read_file": lambda path: "Error: nope"}, {"path": "x"})
    shown = console.export_text()
    assert "Tool Error" in shown
    assert "Tool Result" not in shown
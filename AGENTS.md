# Project: kaoruko (alduin) CLI coding agent

- Source code is in the `alduin/` folder: `main.py` (agent loop), `tool.py` (tools), `llm.py` (model call), `ui.py` (terminal output).
- Tests are in `tests/`. Run them with `uv run python -m pytest`.
- File paths are relative to the project root, for example `alduin/main.py`, never just `main.py`.
- Before reading or editing a file you have not seen, call `list_files` on its folder first.
- To change a file, use `edit_file` with an `old_str` that appears exactly once. Do not print code in chat instead of editing.
- Never write outside the project folder.
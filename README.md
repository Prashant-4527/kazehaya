# Kazehaya

A small command-line coding agent that runs fully on a laptop with a local model. You type a request, the model decides which tool to call (read a file, list a folder, edit a file, run a shell command), the program runs the tool, and the result goes back to the model until the task is done.

Kazehaya is built on the **alduin** workshop skeleton by [Prashant Anand](https://github.com/primaprashant/alduin) (MIT). The workshop's phase-by-phase structure and UI code are his; the Python package is still named `alduin` because of that. Everything described under "What I added" and "Failure analysis" is my own work on top of it.

<!-- [FILL: add one screenshot or GIF of a real session here, for example the approval prompt for a bash command] -->

## What it does

| Tool | Purpose | Safety rule |
|---|---|---|
| `read_file` | Read a file | Only inside the project folder |
| `list_files` | List a folder | Only inside the project folder |
| `edit_file` | Create a file, or replace text in one | Only inside the project folder; the text to replace must match exactly once; never overwrites a non-empty file |
| `bash` | Run a shell command | Needs a yes/no from the user every time; 30 second timeout; output cut at 10,000 characters |

The agent loop stops after 15 tool rounds per request. If the model server fails, the whole turn is rolled back so the conversation stays valid. A project-level `AGENTS.md` is loaded once at startup and added to the system prompt.

## Run it

You need Python 3.12, [uv](https://docs.astral.sh/uv/) and [Ollama](https://ollama.com/).

```bash
ollama pull qwen3:4b
uv sync
cp .env.sample .env        # then edit it, see below
uv run python -m alduin.main
```

`.env` for a local model (the API key can be any non-empty text):

```
ANTHROPIC_API_KEY="ollama"
ANTHROPIC_BASE_URL="http://127.0.0.1:11434"
```

Ollama exposes an Anthropic-compatible endpoint, so the official `anthropic` client works unchanged. To use the real Claude API instead, put your key in `ANTHROPIC_API_KEY`, remove `ANTHROPIC_BASE_URL`, and change `MODEL` in `alduin/llm.py`.

Run the tests with `uv run python -m pytest` (11 tests).

## What I added on top of the workshop

- Runs on a local open model instead of a paid API.
- The folder sandbox covers reads and listings as well as writes, and resolves the working folder before comparing paths.
- `bash` works on Windows (Git Bash, else PowerShell) and on Linux/macOS.
- A denied `bash` command is never executed, and the model is told it was denied.
- If the LLM call fails, the turn is rolled back instead of crashing the session.
- A test suite for the sandbox, the exactly-one-match edit rule, bash, the approval gate, `AGENTS.md` loading and the rollback.

## Bugs I found in my own code

I audited the repo after finishing all seven phases and found these. Each one now has a regression test.

1. **Denying a command did not stop it.** The approval check printed an error but had no `return`, so the command ran anyway and the model received its output.
2. **Two `bash` functions in one file.** The empty workshop stub, defined later, silently replaced my working one, so the tool returned `None`.
3. **Reads were not sandboxed.** `read_file("../secret.txt")` returned the file even though writes outside the project were blocked. This matters most when the model is a cloud API, because the file content would be sent to it.
4. **A connection error killed the session.** An Ollama restart produced a traceback and lost the conversation.

## Failure analysis (qwen3:4b)

Things I observed while running the agent with a 4-billion-parameter model:

1. **It followed instructions hidden inside a file.** Asked to read `README.md`, it acted on text written in the file instead of my request. Tool results are untrusted data, but the model cannot tell data from instructions. The approval gate and the sandbox limit the damage; they do not remove the cause.
2. **It printed a tool call as plain text** instead of emitting a real tool call, so the loop saw no tool use and nothing ran.
3. **It worked around a block silently.** The sandbox refused to create `../../outside.txt`. The model then created `outside.txt` inside the project and reported success. The sandbox worked; the model's behaviour is the problem.
4. **It could not extend itself.** Asked to add `AGENTS.md` loading to its own code, it printed generic code in the chat, guessed the path `main.py` instead of `alduin/main.py`, and never called `list_files`.

`AGENTS.md` (project layout, "list the folder before reading", "edit, do not print code") is my response to failure 4. Result: [FILL: what happened with and without `AGENTS.md` on the same prompt, one or two sentences].

[FILL optional: qwen3:4b vs qwen3:8b on the same 5 prompts, one small table].

## Limitations and next steps

- `edit_file` can modify `AGENTS.md`, and that file goes into the system prompt on the next start. A prompt injection could therefore persist across sessions. Fix to try: require approval for edits to `AGENTS.md`.
- The sandbox only guards the file tools. An approved `bash` command can touch anything on the machine, so the approval prompt is the real safeguard there.
- Conversation history is never trimmed, so a long session will eventually exceed the model's context window.
- Small local models make mistakes on multi-step tasks; the safety design assumes that.

## How it was built

I wrote the code by hand, phase by phase, following the workshop. I used Claude to explain concepts and to review the finished repo; the audit above came from that review. The design decisions and the bugs are things I can walk through line by line.

## License

MIT. See `LICENSE`. The workshop skeleton is © 2026 Prashant Anand; my changes are © 2026 Prashant Sulaniya.

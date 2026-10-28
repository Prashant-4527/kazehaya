"""Alduin - A minimal CLI coding agent."""

import os
from pathlib import Path
from typing import Any

import anthropic
import dotenv
from rich.console import Console

from alduin import llm, schema_converter, system_prompt, theme, tool, ui

MAX_TOOL_ROUNDS = 15
TOOLS_NEEDING_APPROVAL = {"bash"}


def load_agents_md() -> str:
    agents_file = Path.cwd() / "AGENTS.md"
    if not agents_file.is_file():
        return ""
    return agents_file.read_text(encoding="utf-8")


def execute_tool(console, name: str, tool_lookup, args: dict[str, Any]) -> str:
    ui.print_tool_request(console, name, args)
    if name in TOOLS_NEEDING_APPROVAL and not ui.confirm(console, args.get("command", "")):
        message = "Error: the user denied this command"
        ui.print_tool_error(console, name, message)
        return message

    # Find request function
    tool_fn = tool_lookup.get(name)

    if tool_fn is None:
        error = f"Error: Unknown tool '{name}'"
        ui.print_tool_error(console, name, error)
        return error

    try:
        result = str(tool_fn(**args))
        if result.startswith("Error"):
            ui.print_tool_error(console, name, result)
        else:
            ui.print_tool_result(console, name, result)
        return result

    except Exception as e:
        error = f"Error executing tool '{name}': '{e}'"
        ui.print_tool_error(console, name, error)
        return error


def agent_loop(client: anthropic.Anthropic, console: Console) -> None:
    """Run the main agent loop: read input, call LLM, execute tools, repeat.

    Args:
        client: The initialized Anthropic client.
        console: The Rich Console for logging and UI.
    """

    conversation: list[dict[str, Any]] = []

    active_tools = [tool.read_file, tool.list_files, tool.edit_file, tool.bash]

    tool_lookup = {fn.__name__: fn for fn in active_tools}

    tool_schemas = schema_converter.generate_tool_schema(active_tools)

    memory = load_agents_md()
    full_prompt = system_prompt.get()
    if memory:
        full_prompt += f"\n\n# Project instructions (AGENTS.md)\n{memory}"
        ui.print_debug(console, f"Loaded AGENTS.md ({len(memory)} characters)")

    while True:
        try:
            user_input = input("🧑‍💻 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            ui.clear_previous_line()
            ui.print_goodbye(console)
            return

        if not user_input:
            continue

        conversation.append({"role": "user", "content": user_input})

        ui.clear_previous_line()
        ui.print_user_message(console, user_input)

        tool_rounds = 0
        turn_start = len(conversation) - 1
        while True:
            try:
                llm_response = llm.call(
                    client=client,
                    console=console,
                    system_prompt=full_prompt,
                    messages=conversation,
                    tool_schemas=tool_schemas,
                )
            except anthropic.APIError as exc:
                ui.print_error(console, f"LLM call failed: {exc}")
                del conversation[turn_start:]
                break

            conversation.append({"role": "assistant", "content": llm_response.content})

            tool_results = []
            for block in llm_response.content:
                if block.type == "text":
                    ui.print_assistant_reply(
                        console=console,
                        text=block.text,
                        input_tokens=llm_response.usage.input_tokens,
                        output_tokens=llm_response.usage.output_tokens,
                    )
                elif block.type == "tool_use":
                    result = execute_tool(console, block.name, tool_lookup, block.input)
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})

            if not tool_results:
                break

            conversation.append({"role": "user", "content": tool_results})

            tool_rounds += 1
            if tool_rounds >= MAX_TOOL_ROUNDS:
                ui.print_error(console, "Stopped: maximum tool rounds reached.")
                conversation.append({"role": "assistant", "content": "Stopped: maximum tool rounds reached."})
                break


def main() -> None:
    """Entry point for the Alduin CLI agent.

    Initializes console, checks API key, and starts the agent loop.
    """

    dotenv.load_dotenv()
    console = Console(theme=theme.ALDUIN_THEME)
    ui.print_banner(console)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        ui.print_error(console, "ANTHROPIC_API_KEY environment variable is not set.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    agent_loop(client=client, console=console)


if __name__ == "__main__":
    main()

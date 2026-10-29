from typing import Any

import anthropic
from rich.console import Console
from rich.status import Status

from alduin import ui

MODEL = "qwen3:4b"
MAX_TOKENS = 8096


def call(
    client: anthropic.Anthropic,
    console: Console,
    system_prompt: str,
    messages: list[dict[str, Any]],
    tool_schemas: list[dict[str, Any]],
) -> anthropic.types.Message:
    """Send messages to the Anthropic API and return the LLM response.

    Args:
        client: The initialized Anthropic client.
        console: The Rich Console for logging debug info.
        system_prompt: The system prompt to set the context for the LLM.
        messages: The list of messages in the conversation history.
        tool_schemas: The list of tool schemas to provide to the LLM for tool calls.

    Returns:
        The LLM's response.
    """

    ui.print_debug(console, f"Calling {MODEL} with {len(messages)} messages")

    with Status("📜 Consulting the Elder Scrolls...", console=console, spinner="point"):
        return client.messages.create(
            model=MODEL,
            system=system_prompt,
            messages=messages,
            tools=tool_schemas,
            max_tokens=MAX_TOKENS,
        )


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    client = anthropic.Anthropic()

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
    )

    reply = "".join(block.text for block in response.content if block.type == "text")
    print(f"Response from {MODEL}: {reply}")
    print("Model is reachable.")

"""Module for tool implementations for the coding agent."""

import subprocess
import sys
from pathlib import Path


def _inside_project(path: str) -> Path | None:
    """Return the resolved path if it is inside the current folder, else None."""
    resolved = Path(path).resolve()
    if resolved.is_relative_to(Path.cwd().resolve()):
        return resolved
    return None


def _shell_args(command: str) -> list[str]:
    """Pick a shell that exists on this machine."""
    if sys.platform == "win32":
        git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        if git_bash.exists():
            return [str(git_bash), "-c", command]
        return ["powershell", "-NoProfile", "-Command", command]
    return ["bash", "-c", command]


def bash(command: str) -> str:
    """Run a shell command in the project folder and return its output.

    The user must approve every command before it runs. The command is stopped after 30 seconds
    and the output is cut at 10,000 characters.

    Args:
        command: The shell command to run.

    Returns:
        The exit code followed by the combined stdout and stderr, or an error message.
    """

    try:
        completed = subprocess.run(
            _shell_args(command),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=Path.cwd(),
        )
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30 seconds"

    output = completed.stdout + completed.stderr
    if len(output) > 10_000:
        output = output[:10_000] + "\n... (output truncated)"
    return f"exit code: {completed.returncode}\n{output}"


def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: The path to the file to read.

    Returns:
        The contents of the file, or an error message if it fails.
    """

    file_path = _inside_project(path)
    if file_path is None:
        return "Error: path is outside the project folder"

    if not file_path.is_file():
        return f"Error: file not found: {path}"

    return file_path.read_text(encoding="utf-8")


def edit_file(path: str, old_str: str, new_str: str) -> str:
    """Create or edit a file by replacing occurrences of a string.

    This tool can be used to do both, create a new file (if old_str is empty) or edit an existing file.

    Args:
        path: The path to the file to edit.
        old_str: The string to be replaced.
        new_str: The replacement string.

    Returns:
        A success message, or an error message if it fails.
    """

    file_path = _inside_project(path)
    if file_path is None:
        return "Error: path is outside the project folder"

    if old_str == "":
        if file_path.exists() and file_path.read_text(encoding="utf-8") != "":
            return f"Error: {path} already exists and is not empty"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(new_str, encoding="utf-8")
        return f"Created {path}"

    if not file_path.is_file():
        return f"Error: file not found: {path}"

    text = file_path.read_text(encoding="utf-8")
    count = text.count(old_str)
    if count == 0:
        return "Error: old_str not found in the file"
    if count > 1:
        return f"Error: old_str appears {count} times; give a more unique string"

    file_path.write_text(text.replace(old_str, new_str), encoding="utf-8")
    return f"Edited {path}"


def list_files(path: str) -> str:
    """List files in a directory.

    Args:
        path: The path to the directory to list files in.

    Returns:
        A newline-separated list of file names, or an error message.
    """

    p = _inside_project(path)
    if p is None:
        return "Error: path is outside the project folder"
    if not p.is_dir():
        return f"Error: not a directory: {path}"

    contents = sorted(p.iterdir())
    if not contents:
        return "Directory is empty."

    lines = [f"{item.name}/" if item.is_dir() else item.name for item in contents]
    return "\n".join(lines)

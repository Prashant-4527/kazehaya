from alduin import tool

def test_read_file_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert tool.read_file("nope.txt").startswith("Erro")



def test_edit_blocks_outside_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    outside = tmp_path.parent / "outside.txt"
    result = tool.edit_file(str(outside), "", "hacked")
    assert result.startswith("Error")
    assert not outside.exists()


def test_edit_needs_exactly_one_match(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text("x x", encoding="utf-8")
    assert tool.edit_file("a.txt", "x", "y").startswith("Error")
    assert tool.edit_file("a.txt", "z", "y").startswith("Error")
    assert tool.edit_file("a.txt", "x x", "y").startswith("Edited")
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "y"




def test_bash_echo():
    result = tool.bash("echo hello")
    assert result.startswith("exit code: 0")
    assert "hello" in result


def test_bash_exit_code():
    assert tool.bash("exit 3").startswith("exit code: 3")



def test_read_blocks_outside_path(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (tmp_path / "secret.txt").write_text("TOP-SECRET", encoding="utf-8")
    monkeypatch.chdir(project)
    result = tool.read_file("../secret.txt")
    assert result.startswith("Error")
    assert "TOP-SECRET" not in result
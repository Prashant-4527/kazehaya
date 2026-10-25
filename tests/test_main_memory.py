from alduin import main


def test_load_agents_md_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main.load_agents_md() == ""


def test_load_agents_md_reads_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("be brief", encoding="utf-8")
    assert main.load_agents_md() == "be brief"

import pytest

from docco.config import (
    _merge_configs,
    find_document_config,
    find_project_config,
    load_config,
    load_project_config,
)


def test_find_project_config(tmp_path):
    toml = tmp_path / "docco.toml"
    toml.write_text('file = "doc.md"\n', encoding="utf-8")
    sub = tmp_path / "sub" / "deep"
    sub.mkdir(parents=True)

    assert find_project_config(sub, stop_at=tmp_path) == toml


def test_find_project_config_not_found(tmp_path):
    assert find_project_config(tmp_path) is None


def test_find_project_config_does_not_traverse_above_cwd(tmp_path, monkeypatch):
    """Config above cwd is not found when start is inside cwd."""
    toml = tmp_path / "docco.toml"
    toml.write_text('file = "doc.md"\n', encoding="utf-8")
    sub = tmp_path / "project"
    sub.mkdir()
    monkeypatch.chdir(sub)

    assert find_project_config(sub) is None


def test_find_document_config(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("# test", encoding="utf-8")
    sidecar = tmp_path / "doc.toml"
    sidecar.write_text('[vars]\ntitle = "Test"\n', encoding="utf-8")

    assert find_document_config(md) == sidecar


def test_find_document_config_missing(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("# test", encoding="utf-8")
    assert find_document_config(md) is None


def test_merge_configs_scalar_override():
    base = {"a": 1, "b": 2}
    override = {"b": 3, "c": 4}
    assert _merge_configs(base, override) == {"a": 1, "b": 3, "c": 4}


def test_merge_configs_list_append():
    base = {"css": ["a.css"]}
    override = {"css": ["b.css"]}
    assert _merge_configs(base, override) == {"css": ["a.css", "b.css"]}


def test_merge_configs_nested_dict():
    base = {"html": {"css": ["a.css"], "template": "base.html"}}
    override = {"html": {"css": ["b.css"]}}
    result = _merge_configs(base, override)
    assert result == {"html": {"css": ["a.css", "b.css"], "template": "base.html"}}


def test_load_project_config_explicit_path(tmp_path):
    config_file = tmp_path / "docco.toml"
    config_file.write_text('file = "doc.md"\n\n[pdf]\ndpi = 300\n', encoding="utf-8")

    result, config_dir = load_project_config(config_path=config_file)
    assert result["pdf"]["dpi"] == 300
    assert config_dir == config_file.parent


def test_load_project_config_discovery(tmp_path):
    config_file = tmp_path / "docco.toml"
    config_file.write_text('file = "doc.md"\n', encoding="utf-8")
    sub = tmp_path / "docs"
    sub.mkdir()

    result, config_dir = load_project_config(start=sub)
    assert result["file"] == "doc.md"
    assert config_dir == config_file.parent


def test_load_project_config_no_config_raises(tmp_path):
    with pytest.raises(ValueError, match="No docco.toml found"):
        load_project_config(start=tmp_path)


def test_load_config_merges_sidecar(tmp_path):
    project = {"html": {"css": ["base.css"]}}
    md = tmp_path / "doc.md"
    md.write_text("# test", encoding="utf-8")
    sidecar = tmp_path / "doc.toml"
    sidecar.write_text('[html]\ncss = ["extra.css"]\n', encoding="utf-8")

    result = load_config(md, project)
    assert result["html"]["css"] == ["base.css", "extra.css"]


def test_load_config_no_sidecar(tmp_path):
    project = {"file": "doc.md"}
    md = tmp_path / "test.md"
    md.write_text("# test", encoding="utf-8")

    result = load_config(md, project)
    assert result == project


def test_load_config_normalizes_sidecar_with_normalizers(tmp_path):
    project = {}
    md = tmp_path / "doc.md"
    md.write_text("# test", encoding="utf-8")
    sidecar = tmp_path / "doc.toml"
    sidecar.write_text('[html]\ncss = "style.css"\n', encoding="utf-8")

    resolved = str((tmp_path / "style.css").resolve())
    normalizers = {
        "html": lambda s, base: {**s, "css": [str((base / s["css"]).resolve())]}
    }
    result = load_config(md, project, normalizers=normalizers)
    assert result["html"]["css"] == [resolved]

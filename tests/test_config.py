# Edge-case tests only. The happy path is covered by tests/test_regression.py.
import pytest

from docco.config import (
    _merge_configs,
    find_document_config,
    find_project_config,
    load_config,
    load_project_config,
)


def test_find_project_config_not_found(tmp_path):
    assert find_project_config(tmp_path) is None


def test_find_project_config_does_not_traverse_above_cwd(tmp_path, monkeypatch):
    (tmp_path / "docco.toml").write_text('file = "doc.md"\n', encoding="utf-8")
    sub = tmp_path / "project"
    sub.mkdir()
    monkeypatch.chdir(sub)
    assert find_project_config(sub) is None


def test_find_document_config_missing(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("# test", encoding="utf-8")
    assert find_document_config(md) is None


def test_merge_configs_list_append():
    assert _merge_configs({"css": ["a.css"]}, {"css": ["b.css"]}) == {
        "css": ["a.css", "b.css"]
    }


def test_load_project_config_discovery(tmp_path):
    (tmp_path / "docco.toml").write_text('file = "doc.md"\n', encoding="utf-8")
    sub = tmp_path / "docs"
    sub.mkdir()
    result, config_dir = load_project_config(start=sub)
    assert result["file"] == "doc.md"
    assert config_dir == tmp_path


def test_load_project_config_no_config_raises(tmp_path):
    with pytest.raises(ValueError, match="No docco.toml found"):
        load_project_config(start=tmp_path)


def test_load_config_merges_sidecar(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("# test", encoding="utf-8")
    (tmp_path / "doc.toml").write_text(
        '[html]\ncss = ["extra.css"]\n', encoding="utf-8"
    )
    result = load_config(md, {"html": {"css": ["base.css"]}})
    assert result["html"]["css"] == ["base.css", "extra.css"]


def test_load_config_no_sidecar(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# test", encoding="utf-8")
    project = {"file": "test.md"}
    assert load_config(md, project) == project


def test_load_project_config_with_normalizers(tmp_path):
    cfg = tmp_path / "docco.toml"
    cfg.write_text('[html]\ncss = "style.css"\n', encoding="utf-8")
    normalizers = {
        "html": lambda s, base: {**s, "css": [str((base / s["css"]).resolve())]}
    }
    result, _ = load_project_config(config_path=cfg, normalizers=normalizers)
    assert result["html"]["css"] == [str((tmp_path / "style.css").resolve())]


def test_load_config_normalizes_sidecar(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("# test", encoding="utf-8")
    (tmp_path / "doc.toml").write_text('[html]\ncss = "style.css"\n', encoding="utf-8")
    resolved = str((tmp_path / "style.css").resolve())
    normalizers = {
        "html": lambda s, base: {**s, "css": [str((base / s["css"]).resolve())]}
    }
    result = load_config(md, {}, normalizers=normalizers)
    assert result["html"]["css"] == [resolved]

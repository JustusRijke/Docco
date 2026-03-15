from docco.context import ContentType, Context


def test_from_file(tmp_md, tmp_path, tmp_config):
    ctx = Context.from_file(tmp_md, tmp_path / "out", tmp_config)
    assert ctx.content_type == ContentType.MARKDOWN
    assert ctx.content == "# Hello\n\nWorld\n"
    assert ctx.source_path == tmp_md
    assert ctx.artifacts == {}
    assert ctx.config is tmp_config

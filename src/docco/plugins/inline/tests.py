import pytest

from docco.context import Context
from docco.plugins.inline import Stage


def make_ctx(tmp_path, content):
    md = tmp_path / "doc.md"
    md.write_text(content, encoding="utf-8")
    config = {}
    return Context.from_file(md, tmp_path / "out", config)


def test_inline_md(tmp_path):
    frag = tmp_path / "frag.md"
    frag.write_text("# Fragment\n", encoding="utf-8")
    ctx = make_ctx(tmp_path, '<!-- inline src="frag.md" -->')
    result = Stage().process(ctx)
    assert "# Fragment" in result.str_content


def test_inline_html(tmp_path):
    frag = tmp_path / "frag.html"
    frag.write_text("  <p>Hello</p>  \n", encoding="utf-8")
    ctx = make_ctx(tmp_path, '<!-- inline src="frag.html" -->')
    result = Stage().process(ctx)
    assert "<p>Hello</p>" in result.str_content


def test_placeholder_substitution(tmp_path):
    frag = tmp_path / "frag.md"
    frag.write_text("Hello {{name}}!", encoding="utf-8")
    ctx = make_ctx(tmp_path, '<!-- inline src="frag.md" name="World" -->')
    result = Stage().process(ctx)
    assert "Hello World!" in result.str_content


def test_file_not_found(tmp_path):
    ctx = make_ctx(tmp_path, '<!-- inline src="missing.md" -->')
    with pytest.raises(FileNotFoundError, match="missing.md"):
        Stage().process(ctx)


def test_no_directives_passthrough(tmp_path):
    ctx = make_ctx(tmp_path, "No inlines here")
    result = Stage().process(ctx)
    assert result.content == "No inlines here"


def test_code_block_protected(tmp_path):
    content = '```\n<!-- inline src="missing.md" -->\n```'
    ctx = make_ctx(tmp_path, content)
    result = Stage().process(ctx)
    assert "missing.md" in result.str_content


def test_nested_inline(tmp_path):
    inner = tmp_path / "inner.md"
    inner.write_text("Inner\n", encoding="utf-8")
    outer = tmp_path / "outer.md"
    outer.write_text('<!-- inline src="inner.md" -->', encoding="utf-8")
    ctx = make_ctx(tmp_path, '<!-- inline src="outer.md" -->')
    result = Stage().process(ctx)
    assert "Inner" in result.str_content


def test_max_iterations_exceeded(tmp_path, monkeypatch):
    # Create a self-referencing file to force infinite loop
    loop = tmp_path / "loop.md"
    loop.write_text('<!-- inline src="loop.md" -->', encoding="utf-8")
    ctx = make_ctx(tmp_path, '<!-- inline src="loop.md" -->')
    with pytest.raises(ValueError, match="Max iterations"):
        Stage().process(ctx)


def test_unused_arg_warning(tmp_path, caplog):
    import logging

    frag = tmp_path / "frag.md"
    frag.write_text("Hello", encoding="utf-8")
    ctx = make_ctx(tmp_path, '<!-- inline src="frag.md" unused="x" -->')
    with caplog.at_level(logging.WARNING, logger="docco.plugins.inline"):
        Stage().process(ctx)
    assert "Unused" in caplog.text


def test_unfulfilled_placeholder_warning(tmp_path, caplog):
    import logging

    frag = tmp_path / "frag.md"
    frag.write_text("Hello {{name}}", encoding="utf-8")
    ctx = make_ctx(tmp_path, '<!-- inline src="frag.md" -->')
    with caplog.at_level(logging.WARNING, logger="docco.plugins.inline"):
        Stage().process(ctx)
    assert "Unfulfilled" in caplog.text


def test_inline_code_block_protected(tmp_path):
    # Backtick inline code containing a directive-like string should not be processed
    content = 'Use `<!-- inline src="missing.md" -->` syntax'
    ctx = make_ctx(tmp_path, content)
    result = Stage().process(ctx)
    assert "missing.md" in result.str_content


def test_fenced_block_leading_and_no_trailing_newline(tmp_path):
    # Fenced block with a leading newline alongside a directive
    frag = tmp_path / "frag.md"
    frag.write_text("World", encoding="utf-8")
    content = 'text\n```\ncode\n```\n<!-- inline src="frag.md" -->'
    ctx = make_ctx(tmp_path, content)
    result = Stage().process(ctx)
    assert "code" in result.str_content
    assert "World" in result.str_content


def test_inline_code_restored(tmp_path):
    # Inline backtick code is extracted and then restored
    frag = tmp_path / "frag.md"
    frag.write_text("World", encoding="utf-8")
    content = 'Use `code` here\n<!-- inline src="frag.md" -->'
    ctx = make_ctx(tmp_path, content)
    result = Stage().process(ctx)
    assert "`code`" in result.str_content
    assert "World" in result.str_content


def test_malformed_directive_raises(tmp_path):
    ctx = make_ctx(tmp_path, '<!-- inline : "frag.md" -->')
    with pytest.raises(ValueError, match="Malformed 'inline' directive"):
        Stage().process(ctx)


def test_rebase_absolute_path_preserved(tmp_path):
    # An inline directive with an absolute path inside an inlined file should not be rebased
    inner = tmp_path / "inner.md"
    inner_abs = str(tmp_path / "frag.md")
    frag = tmp_path / "frag.md"
    frag.write_text("Fragment", encoding="utf-8")
    inner.write_text(f'<!-- inline src="{inner_abs}" -->', encoding="utf-8")
    ctx = make_ctx(tmp_path, '<!-- inline src="inner.md" -->')
    result = Stage().process(ctx)
    assert "Fragment" in result.str_content

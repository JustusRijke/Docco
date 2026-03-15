import logging

import pytest

from docco.context import ContentType, Context, Phase
from docco.pipeline import (
    Stage,
    _topo_sort,
    _validate_config_keys,
    _validate_content_type,
    build_pipeline,
    run_pipeline,
)

# --- parse_directives ---


def test_parse_directives_valid():
    results = Stage.parse_directives("foo", '<!-- foo key="val" other="x" -->')
    assert len(results) == 1
    _, attrs = results[0]
    assert attrs == {"key": "val", "other": "x"}


def test_parse_directives_empty_attrs():
    results = Stage.parse_directives("foo", "<!-- foo -->")
    assert len(results) == 1
    assert results[0][1] == {}


def test_parse_directives_flag():
    results = Stage.parse_directives("foo", "<!-- foo bar -->")
    assert len(results) == 1
    assert results[0][1] == {"bar": "true"}


def test_parse_directives_flag_and_kv():
    results = Stage.parse_directives("foo", '<!-- foo bar baz="x" -->')
    assert len(results) == 1
    assert results[0][1] == {"bar": "true", "baz": "x"}


def test_parse_directives_kv_overrides_flag():
    results = Stage.parse_directives("foo", '<!-- foo bar bar="val" -->')
    assert len(results) == 1
    assert results[0][1] == {"bar": "val"}


def test_parse_directives_malformed_raises():
    with pytest.raises(ValueError, match="Malformed 'foo' directive"):
        Stage.parse_directives("foo", "<!-- foo = -->")


def test_parse_directives_no_match():
    assert Stage.parse_directives("foo", "no directives here") == []


def test_parse_directives_multiple():
    content = '<!-- foo a="1" --> text <!-- foo b="2" -->'
    results = Stage.parse_directives("foo", content)
    assert len(results) == 2
    assert results[0][1] == {"a": "1"}
    assert results[1][1] == {"b": "2"}


def test_parse_directives_caches_pattern():
    # Second call with same name should use cached pattern
    Stage.parse_directives("cached_name", "no match")
    Stage.parse_directives("cached_name", "no match again")


def test_parse_directives_allowed_known_args_pass():
    results = Stage.parse_directives(
        "foo", '<!-- foo key="val" -->', frozenset({"key"})
    )
    assert results[0][1] == {"key": "val"}


def test_parse_directives_allowed_unknown_raises():
    with pytest.raises(ValueError, match="Unknown arg"):
        Stage.parse_directives("foo", '<!-- foo bad="x" -->', frozenset({"key"}))


def test_parse_directives_allowed_none_skips_validation():
    # allowed=None (default) does not raise for any arg names
    results = Stage.parse_directives("foo", '<!-- foo anything="x" -->', None)
    assert results[0][1] == {"anything": "x"}


def test_parse_directives_allowed_empty_set_rejects_all():
    with pytest.raises(ValueError, match="Unknown arg"):
        Stage.parse_directives("foo", "<!-- foo flag -->", frozenset())


class PassthroughStage(Stage):
    name = "passthrough"
    consumes = ContentType.MARKDOWN
    produces = ContentType.MARKDOWN
    phase = Phase.PREPROCESS

    def process(self, context):
        assert isinstance(context.content, str)
        context.content = context.content + " [passthrough]"
        return context


class MarkdownToHtmlStage(Stage):
    name = "to_html"
    consumes = ContentType.MARKDOWN
    produces = ContentType.HTML
    phase = Phase.CONVERT

    def process(self, context):
        assert isinstance(context.content, str)
        context.content = f"<p>{context.content}</p>"
        context.content_type = ContentType.HTML
        return context


class ForkingStage(Stage):
    name = "forker"
    consumes = ContentType.HTML
    produces = ContentType.HTML
    phase = Phase.ENRICH

    def process(self, context):
        assert isinstance(context.content, str)
        ctx_a = Context(
            source_path=context.source_path,
            output_dir=context.output_dir,
            config=context.config,
            content=context.content + " [a]",
            content_type=ContentType.HTML,
        )
        ctx_b = Context(
            source_path=context.source_path,
            output_dir=context.output_dir,
            config=context.config,
            content=context.content + " [b]",
            content_type=ContentType.HTML,
        )
        return [ctx_a, ctx_b]


class HtmlPassthroughStage(Stage):
    name = "html_pass"
    consumes = ContentType.HTML
    produces = ContentType.HTML
    phase = Phase.ENRICH
    after = ("forker",)

    def process(self, context):
        assert isinstance(context.content, str)
        context.content = context.content + " [html_pass]"
        return context


class RenderStage(Stage):
    name = "render"
    consumes = ContentType.HTML
    produces = ContentType.PDF
    phase = Phase.RENDER

    def process(self, context):
        context.content = b"pdf"
        context.content_type = ContentType.PDF
        return context


# --- Stage ABC ---


def test_get_directives_calls_parse_with_name():
    results = PassthroughStage().get_directives('<!-- passthrough key="val" -->')
    assert len(results) == 1
    assert results[0][1] == {"key": "val"}


def test_stage_abc_cannot_instantiate():
    with pytest.raises(TypeError):
        Stage()


def test_normalize_config_section_base_is_noop(tmp_path):
    section = {"key": "value"}
    assert PassthroughStage.normalize_config_section(section, tmp_path) is section


def test_init_subclass_sets_logger():
    assert PassthroughStage.log.name == "docco.plugins.passthrough"


def test_init_subclass_no_name():
    class _Intermediate(Stage):
        pass

    assert not hasattr(_Intermediate, "log")


def test_get_config(markdown_context):
    markdown_context.config = {"passthrough": {"key": "val"}}
    assert PassthroughStage().get_config(markdown_context) == {"key": "val"}


def test_get_config_missing(markdown_context):
    markdown_context.config = {}
    assert PassthroughStage().get_config(markdown_context) == {}


# --- Content type validation ---


def test_validate_content_type_match(markdown_context):
    _validate_content_type(PassthroughStage(), markdown_context)


def test_validate_content_type_any(markdown_context):
    stage = PassthroughStage()
    stage.consumes = ContentType.ANY
    _validate_content_type(stage, markdown_context)


def test_validate_content_type_mismatch(markdown_context):
    with pytest.raises(
        TypeError, match="expects content_type 'html'.*received 'markdown'"
    ):
        _validate_content_type(HtmlPassthroughStage(), markdown_context)


# --- _topo_sort ---


def test_topo_sort_respects_after():
    result = _topo_sort([HtmlPassthroughStage, ForkingStage])
    assert result == [ForkingStage, HtmlPassthroughStage]


def test_topo_sort_ignores_missing_deps():
    # html_pass has after=("forker",) but forker is not in the list
    result = _topo_sort([HtmlPassthroughStage])
    assert result == [HtmlPassthroughStage]


def test_topo_sort_alphabetical_tiebreak():
    class A(Stage):
        name = "aaa"
        consumes = ContentType.HTML
        produces = ContentType.HTML
        phase = Phase.ENRICH

        def process(self, c):  # ty: ignore[invalid-method-override]
            return c

    class B(Stage):
        name = "bbb"
        consumes = ContentType.HTML
        produces = ContentType.HTML
        phase = Phase.ENRICH

        def process(self, c):  # ty: ignore[invalid-method-override]
            return c

    result = _topo_sort([B, A])
    assert [c.name for c in result] == ["aaa", "bbb"]


def test_topo_sort_multiple_deps():
    class A(Stage):
        name = "a"
        consumes = ContentType.HTML
        produces = ContentType.HTML
        phase = Phase.ENRICH

        def process(self, c):  # ty: ignore[invalid-method-override]
            return c

    class B(Stage):
        name = "b"
        consumes = ContentType.HTML
        produces = ContentType.HTML
        phase = Phase.ENRICH

        def process(self, c):  # ty: ignore[invalid-method-override]
            return c

    class C(Stage):
        name = "c"
        consumes = ContentType.HTML
        produces = ContentType.HTML
        phase = Phase.ENRICH
        after = ("a", "b")

        def process(self, c):  # ty: ignore[invalid-method-override]
            return c

    result = _topo_sort([C, A, B])
    names = [cls.name for cls in result]
    assert names.index("a") < names.index("c")
    assert names.index("b") < names.index("c")


def test_topo_sort_circular_dependency():
    class X(Stage):
        name = "x"
        consumes = ContentType.HTML
        produces = ContentType.HTML
        phase = Phase.ENRICH
        after = ("y",)

        def process(self, c):  # ty: ignore[invalid-method-override]
            return c

    class Y(Stage):
        name = "y"
        consumes = ContentType.HTML
        produces = ContentType.HTML
        phase = Phase.ENRICH
        after = ("x",)

        def process(self, c):  # ty: ignore[invalid-method-override]
            return c

    with pytest.raises(ValueError, match="Circular dependency"):
        _topo_sort([X, Y])


# --- config key validation ---


def test_validate_config_keys_unknown_top_level():
    available: dict[str, type[Stage]] = {"passthrough": PassthroughStage}
    with pytest.raises(ValueError, match="Unknown config key"):
        _validate_config_keys({"bogus": True}, available)


def test_build_pipeline_unknown_plugin_config_key():
    class StrictStage(Stage):
        name = "strict"
        consumes = ContentType.MARKDOWN
        produces = ContentType.MARKDOWN
        phase = Phase.PREPROCESS
        valid_config_keys = frozenset({"allowed"})

        def process(self, c):  # ty: ignore[invalid-method-override]
            return c

    with pytest.raises(ValueError, match=r"\[strict\] unknown config key"):
        build_pipeline({"strict": {"disallowed": True}}, {"strict": StrictStage})


# --- build_pipeline ---


def test_build_pipeline_auto_ordering():
    available: dict[str, type[Stage]] = {
        "passthrough": PassthroughStage,
        "to_html": MarkdownToHtmlStage,
        "html_pass": HtmlPassthroughStage,
        "render": RenderStage,
    }
    stages = build_pipeline({}, available)
    names = [s.name for s in stages]
    assert names == ["passthrough", "to_html", "html_pass", "render"]


def test_build_pipeline_html_input_skips_preprocess_and_convert():
    available: dict[str, type[Stage]] = {
        "passthrough": PassthroughStage,
        "to_html": MarkdownToHtmlStage,
        "html_pass": HtmlPassthroughStage,
        "render": RenderStage,
    }
    stages = build_pipeline({}, available, input_type=ContentType.HTML)
    names = [s.name for s in stages]
    assert "passthrough" not in names
    assert "to_html" not in names
    assert "html_pass" in names
    assert "render" in names


# --- run_pipeline ---


def test_run_pipeline_single_stage(markdown_context):
    results = run_pipeline([PassthroughStage()], markdown_context)
    assert len(results) == 1
    assert results[0].str_content.endswith(" [passthrough]")


def test_run_pipeline_multi_stage(markdown_context):
    results = run_pipeline(
        [PassthroughStage(), MarkdownToHtmlStage()], markdown_context
    )
    assert len(results) == 1
    assert results[0].content_type == ContentType.HTML
    assert "[passthrough]" in results[0].str_content


def test_run_pipeline_type_mismatch(markdown_context):
    with pytest.raises(TypeError, match="expects content_type 'html'"):
        run_pipeline([HtmlPassthroughStage()], markdown_context)


def test_run_pipeline_stops_on_error_log(markdown_context):
    log = logging.getLogger("docco.test_stage")

    class ErrorLogStage(Stage):
        name = "error_logger"
        consumes = ContentType.MARKDOWN
        produces = ContentType.MARKDOWN
        phase = Phase.PREPROCESS

        def process(self, context):
            log.error("something went wrong")
            return context

    class NeverRunStage(Stage):
        name = "never_run"
        consumes = ContentType.MARKDOWN
        produces = ContentType.MARKDOWN
        phase = Phase.PREPROCESS

        def process(self, context):
            raise AssertionError("should not run")

    with pytest.raises(
        RuntimeError, match="Pipeline stopped after stage 'error_logger'"
    ):
        run_pipeline([ErrorLogStage(), NeverRunStage()], markdown_context)


def test_run_pipeline_stops_on_stage_exception(markdown_context):
    class RaisingStage(Stage):
        name = "raiser"
        consumes = ContentType.MARKDOWN
        produces = ContentType.MARKDOWN
        phase = Phase.PREPROCESS

        def process(self, context):
            raise ValueError("boom")

    with pytest.raises(RuntimeError, match="Pipeline stopped after stage 'raiser'"):
        run_pipeline([RaisingStage()], markdown_context)


def test_run_pipeline_forking(markdown_context):
    stages: list[Stage] = [
        MarkdownToHtmlStage(),
        ForkingStage(),
        HtmlPassthroughStage(),
    ]
    results = run_pipeline(stages, markdown_context)
    assert len(results) == 2
    assert "[a] [html_pass]" in results[0].str_content
    assert "[b] [html_pass]" in results[1].str_content

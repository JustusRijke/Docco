# Edge-case tests only. The happy path is covered by tests/test_regression.py.
import logging
from pathlib import Path

import pytest

from docco.context import ContentType, Phase
from docco.pipeline import (
    Stage,
    _topo_sort,
    _validate_config_keys,
    _validate_content_type,
    build_pipeline,
    run_pipeline,
)


class PassthroughStage(Stage):
    name = "passthrough"
    consumes = ContentType.MARKDOWN
    produces = ContentType.MARKDOWN
    phase = Phase.PREPROCESS

    def process(self, context):
        return context


class MarkdownToHtmlStage(Stage):
    name = "to_html"
    consumes = ContentType.MARKDOWN
    produces = ContentType.HTML
    phase = Phase.CONVERT

    def process(self, context):  # pragma: no cover
        context.content_type = ContentType.HTML
        return context


class HtmlPassthroughStage(Stage):
    name = "html_pass"
    consumes = ContentType.HTML
    produces = ContentType.HTML
    phase = Phase.ENRICH

    def process(self, context):  # pragma: no cover
        return context


# --- parse_directives ---


def test_parse_directives_malformed_raises():
    with pytest.raises(ValueError, match="Malformed 'foo' directive"):
        Stage.parse_directives("foo", "<!-- foo = -->")


def test_parse_directives_allowed_unknown_raises():
    with pytest.raises(ValueError, match="Unknown arg"):
        Stage.parse_directives("foo", '<!-- foo bad="x" -->', frozenset({"key"}))


def test_parse_directives_caches_pattern():
    Stage.parse_directives("cached_name", "no match")
    Stage.parse_directives("cached_name", "no match again")


# --- Stage ABC ---


def test_stage_abc_cannot_instantiate():
    with pytest.raises(TypeError):
        Stage()


def test_init_subclass_no_name():
    class _Intermediate(Stage):
        pass

    assert not hasattr(_Intermediate, "log")


def test_get_config_with_config_key(markdown_context):
    class KeyedStage(PassthroughStage):
        name = "keyed"
        config_key = "mykey"

    markdown_context.config = {"mykey": {"x": 1}}
    assert KeyedStage().get_config(markdown_context) == {"x": 1}


def test_normalize_config_section_default():
    section = {"key": "value"}
    assert PassthroughStage().normalize_config_section(section, Path()) == section


# --- _validate_content_type ---


def test_validate_content_type_mismatch(markdown_context):
    with pytest.raises(
        TypeError, match="expects content_type 'html'.*received 'markdown'"
    ):
        _validate_content_type(HtmlPassthroughStage(), markdown_context)


# --- _topo_sort ---


def test_topo_sort_circular_dependency():
    class X(Stage):
        name = "x"
        consumes = ContentType.HTML
        produces = ContentType.HTML
        phase = Phase.ENRICH
        after = ("y",)

        def process(self, context):  # pragma: no cover
            return context

    class Y(Stage):
        name = "y"
        consumes = ContentType.HTML
        produces = ContentType.HTML
        phase = Phase.ENRICH
        after = ("x",)

        def process(self, context):  # pragma: no cover
            return context

    with pytest.raises(ValueError, match="Circular dependency"):
        _topo_sort([X, Y])


# --- config key validation ---


def test_validate_config_keys_unknown_top_level():
    with pytest.raises(ValueError, match="Unknown config key"):
        _validate_config_keys({"bogus": True}, {"passthrough": PassthroughStage})


def test_build_pipeline_unknown_plugin_config_key():
    class StrictStage(Stage):
        name = "strict"
        consumes = ContentType.MARKDOWN
        produces = ContentType.MARKDOWN
        phase = Phase.PREPROCESS
        valid_config_keys = frozenset({"allowed"})

        def process(self, context):  # pragma: no cover
            return context

    with pytest.raises(ValueError, match=r"\[strict\] unknown config key"):
        build_pipeline({"strict": {"disallowed": True}}, {"strict": StrictStage})


def test_build_pipeline_html_input_skips_preprocess_and_convert():
    available = {
        "passthrough": PassthroughStage,
        "to_html": MarkdownToHtmlStage,
        "html_pass": HtmlPassthroughStage,
    }
    stages = build_pipeline({}, available, input_type=ContentType.HTML)  # ty: ignore[invalid-argument-type]
    names = [s.name for s in stages]
    assert "passthrough" not in names
    assert "to_html" not in names
    assert "html_pass" in names


# --- run_pipeline ---


def test_run_pipeline_passthrough(markdown_context):
    result = run_pipeline([PassthroughStage()], markdown_context)
    assert result[0].content == markdown_context.content


def test_run_pipeline_type_mismatch(markdown_context):
    with pytest.raises(TypeError, match="expects content_type 'html'"):
        run_pipeline([HtmlPassthroughStage()], markdown_context)


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


def test_run_pipeline_stops_on_error_log(markdown_context):
    class ErrorLogStage(Stage):
        name = "error_logger"
        consumes = ContentType.MARKDOWN
        produces = ContentType.MARKDOWN
        phase = Phase.PREPROCESS

        def process(self, context):
            logging.getLogger("docco.test_stage").error("something went wrong")
            return context

    with pytest.raises(
        RuntimeError, match="Pipeline stopped after stage 'error_logger'"
    ):
        run_pipeline([ErrorLogStage()], markdown_context)

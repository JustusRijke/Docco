import logging
import re
import time
from abc import ABC, abstractmethod
from importlib.metadata import entry_points
from pathlib import Path

from docco.context import ContentType, Context, Phase

_ATTR_RE = re.compile(r'(\w+)="([^"]*)"')  # matches key="value" attribute pairs
_FLAG_RE = re.compile(r"\b(\w+)\b")  # matches bare-word flags
_COMMENT_RE_CACHE: dict[
    str, re.Pattern
] = {}  # name -> compiled <!-- name ... --> pattern


class PipelineError(RuntimeError):
    def __init__(self, message: str, contexts: list[Context]) -> None:
        super().__init__(message)
        self.contexts = contexts


class _ErrorFlag(logging.Handler):
    triggered: bool = False

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            self.triggered = True


log = logging.getLogger("docco.pipeline")

STAGES_GROUP = "docco.stages"

_PHASE_ORDER = list(Phase)


class Stage(ABC):
    name: str
    consumes: ContentType
    produces: ContentType
    phase: Phase
    after: tuple[str, ...] = ()
    config_key: str = ""
    valid_config_keys: frozenset[str] = frozenset()
    log: logging.Logger

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "name"):
            cls.log = logging.getLogger(f"docco.plugins.{cls.name}")

    @classmethod
    def normalize_config_section(cls, section: dict, base_dir: Path) -> dict:
        """Normalize a raw config section dict relative to base_dir.

        Called on the raw section before config merging. Override to resolve
        relative paths, coerce types, etc. Return the normalised section.
        """
        return section

    def get_config(self, context: Context) -> dict:
        return context.config.get(self.config_key or self.name, {})

    def validate_config(self, config: dict) -> None:
        key = self.config_key or self.name
        section = config.get(key, {})
        unknown = sorted(set(section) - self.valid_config_keys)
        if unknown:
            msg = f"[{key}] unknown config key(s): {', '.join(unknown)}"
            raise ValueError(msg)

    @staticmethod
    def parse_directives(
        name: str,
        content: str,
        allowed: frozenset[str] | None = None,
    ) -> list[tuple[str, dict[str, str]]]:
        """Find all <!-- name ... --> directives and return list of (full_match, attrs_dict).

        Supports key="value" pairs and bare-word flags (e.g. ``quiet`` sets ``{"quiet": "true"}``).
        Raises ValueError for any directive that contains unparseable content.
        If ``allowed`` is not None, raises ValueError for any unknown arg/flag names.
        """
        pattern = _COMMENT_RE_CACHE.get(name)
        if pattern is None:
            pattern = re.compile(rf"<!--\s*{re.escape(name)}(.*?)-->", re.DOTALL)
            _COMMENT_RE_CACHE[name] = pattern
        results = []
        for m in pattern.finditer(content):
            raw = m.group(1).strip()
            kv_attrs = dict(_ATTR_RE.findall(raw))
            cleaned = _ATTR_RE.sub("", raw).strip()
            flag_attrs = {f: "true" for f in _FLAG_RE.findall(cleaned)}
            remainder = _FLAG_RE.sub("", cleaned).strip()
            if remainder:
                raise ValueError(f"Malformed {name!r} directive: {m.group(0)!r}")
            attrs = {**flag_attrs, **kv_attrs}
            if allowed is not None:
                unknown = sorted(set(attrs) - allowed)
                if unknown:
                    raise ValueError(
                        f"Unknown arg(s) {unknown!r} in {name!r} directive: {m.group(0)!r}"
                    )
            results.append((m.group(0), attrs))
        return results

    def get_directives(
        self,
        content: str,
        allowed: frozenset[str] | None = None,
    ) -> list[tuple[str, dict[str, str]]]:
        """Find all <!-- <self.name> ... --> directives in content."""
        return self.parse_directives(self.name, content, allowed)

    @abstractmethod
    def process(self, context: Context) -> Context | list[Context]: ...


def discover_stages() -> dict[str, type[Stage]]:
    stages: dict[str, type[Stage]] = {}
    for ep in entry_points(group=STAGES_GROUP):
        stages[ep.name] = ep.load()
        log.debug("Discovered stage: %s", ep.name)
    return stages


def _topo_sort(stages: list[type[Stage]]) -> list[type[Stage]]:
    """Topological sort within a phase using `after` constraints."""
    name_to_cls = {cls.name: cls for cls in stages}
    in_degree = {cls.name: 0 for cls in stages}
    graph: dict[str, list[str]] = {cls.name: [] for cls in stages}

    for cls in stages:
        for dep in cls.after:
            if dep in name_to_cls:
                graph[dep].append(cls.name)
                in_degree[cls.name] += 1

    queue = sorted(n for n, d in in_degree.items() if d == 0)
    result: list[type[Stage]] = []
    while queue:
        node = queue.pop(0)
        result.append(name_to_cls[node])
        for neighbor in sorted(graph[node]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                queue.sort()

    if len(result) != len(stages):
        cycle = sorted(n for n, d in in_degree.items() if d > 0)
        msg = f"Circular dependency in phase: {cycle}"
        raise ValueError(msg)

    return result


_RESERVED_KEYS = {"file", "log", "error"}


def _validate_config_keys(config: dict, available: dict[str, type[Stage]]) -> None:
    known = _RESERVED_KEYS | {cls.config_key or name for name, cls in available.items()}
    unknown = sorted(set(config) - known)
    if unknown:
        msg = f"Unknown config key(s): {', '.join(unknown)}"
        raise ValueError(msg)


def build_pipeline(
    config: dict,
    available: dict[str, type[Stage]],
    input_type: ContentType = ContentType.MARKDOWN,
) -> list[Stage]:
    _validate_config_keys(config, available)
    stages = dict(available)

    # Skip phases that don't apply to the input type
    if input_type == ContentType.HTML:
        stages = {
            n: c
            for n, c in stages.items()
            if c.phase not in (Phase.PREPROCESS, Phase.CONVERT)
        }

    by_phase: dict[Phase, list[type[Stage]]] = {p: [] for p in _PHASE_ORDER}
    for cls in stages.values():
        by_phase[cls.phase].append(cls)

    ordered: list[type[Stage]] = []
    for phase in _PHASE_ORDER:
        ordered.extend(_topo_sort(by_phase[phase]))

    names = [cls.name for cls in ordered]
    log.debug("Auto-ordered pipeline: %s", names)

    pipeline = [cls() for cls in ordered]
    for stage in pipeline:
        stage.validate_config(config)
    return pipeline


def _validate_content_type(stage: Stage, context: Context) -> None:
    if stage.consumes not in (ContentType.ANY, context.content_type):
        msg = (
            f"Stage '{stage.name}' expects content_type '{stage.consumes}' "
            f"but received '{context.content_type}'"
        )
        raise TypeError(msg)


def run_pipeline(stages: list[Stage], context: Context) -> list[Context]:
    contexts: list[Context] = [context]

    flag = _ErrorFlag()
    logging.getLogger("docco").addHandler(flag)
    try:
        for stage in stages:
            pre_stage_contexts = contexts
            next_contexts: list[Context] = []
            for ctx in contexts:
                _validate_content_type(stage, ctx)
                log.debug("Running stage: %s", stage.name)
                start = time.perf_counter()
                try:
                    result = stage.process(ctx)
                except Exception as e:  # noqa: BLE001
                    log.error("Stage '%s' failed: %s", stage.name, e)
                    flag.triggered = True
                    break
                elapsed = time.perf_counter() - start
                log.debug("Stage '%s' completed in %.3fs", stage.name, elapsed)

                if isinstance(result, Context):
                    next_contexts.append(result)
                else:
                    next_contexts.extend(result)
            contexts = next_contexts

            if flag.triggered:
                msg = f"Pipeline stopped after stage '{stage.name}' due to error(s)"
                raise PipelineError(msg, pre_stage_contexts)
    finally:
        logging.getLogger("docco").removeHandler(flag)

    return contexts

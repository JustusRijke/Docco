import re
from pathlib import Path

from docco.context import ContentType, Context, Phase
from docco.pipeline import _ATTR_RE, Stage as BaseStage

MAX_ITERATIONS = 10

_DIRECTIVE_RE = re.compile(r'<!--\s*inline\s+src="([^"]+)"(.*?)-->')
_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")
_INLINE_PATH_RE = re.compile(r'(<!--\s*inline\s+src=")([^"]+)(")')


def _rebase_inline_paths(content: str, file_dir: Path) -> str:
    def rewrite(m: re.Match) -> str:
        prefix, path, suffix = m.group(1), m.group(2), m.group(3)
        if path.startswith("/"):
            return m.group(0)
        return f"{prefix}{(file_dir / path).resolve()}{suffix}"

    return _INLINE_PATH_RE.sub(rewrite, content)


def _has_directives(content: str) -> bool:
    return bool(_DIRECTIVE_RE.search(content))


def _process_one_pass(content: str, base_dir: Path) -> str:
    def replace_directive(m: re.Match) -> str:
        filepath_str = m.group(1)
        args_str = m.group(2).strip()
        args = dict(_ATTR_RE.findall(args_str))

        full_path = (base_dir / filepath_str).resolve()
        if not full_path.exists():
            msg = f"Inline file not found: {filepath_str}"
            raise FileNotFoundError(msg)

        file_content = full_path.read_text(encoding="utf-8")
        if full_path.suffix == ".html":
            file_content = "\n".join(line.strip() for line in file_content.splitlines())
        file_content = _rebase_inline_paths(file_content, full_path.parent)

        placeholders = set(_PLACEHOLDER_RE.findall(file_content))
        for key, value in args.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in file_content:
                file_content = file_content.replace(placeholder, value)

        unused = set(args) - placeholders
        unfulfilled = placeholders - set(args)
        if unused:
            log.warning(
                "Unused inline args for %s: %s", filepath_str, ", ".join(sorted(unused))
            )
        if unfulfilled:
            log.warning(
                "Unfulfilled placeholders in %s: %s",
                filepath_str,
                ", ".join(sorted(unfulfilled)),
            )

        return file_content

    return _DIRECTIVE_RE.sub(replace_directive, content)


class Stage(BaseStage):
    name = "inline"
    consumes = ContentType.MARKDOWN
    produces = ContentType.MARKDOWN
    phase = Phase.PREPROCESS
    after = ("vars",)

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        base_dir = context.source_path.parent
        self.parse_directives("inline", context.content, allowed=None)
        iteration = 0
        while _has_directives(context.content) and iteration < MAX_ITERATIONS:
            iteration += 1
            self.log.debug("Inline processing iteration %d", iteration)
            context.content = _process_one_pass(context.content, base_dir)

        if iteration >= MAX_ITERATIONS and _has_directives(context.content):
            msg = f"Max iterations ({MAX_ITERATIONS}) exceeded in inline processing"
            raise ValueError(msg)

        if iteration:
            self.log.info("Inlined files in %d pass(es)", iteration)
        else:
            self.log.info("No inline directives found")
        return context


log = Stage.log

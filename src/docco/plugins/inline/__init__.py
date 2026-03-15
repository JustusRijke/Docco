import re
from pathlib import Path

from docco.context import ContentType, Context, Phase
from docco.pipeline import _ATTR_RE, Stage as BaseStage

MAX_ITERATIONS = 10

_FENCED_RE = re.compile(r"(?:^|\n)```.*?```(?:\n|$)", re.DOTALL | re.MULTILINE)
_INLINE_CODE_RES = [
    re.compile(r"````[^`]*````"),
    re.compile(r"```(?!`).*?```(?!`)"),
    re.compile(r"``(?!`).*?``(?!`)"),
    re.compile(r"`(?!`).*?`(?!`)"),
]
_DIRECTIVE_RE = re.compile(r'<!--\s*inline\s+src="([^"]+)"(.*?)-->')
_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")
_INLINE_PATH_RE = re.compile(r'(<!--\s*inline\s+src=")([^"]+)(")')


def _extract_code_blocks(content: str) -> tuple[str, dict[str, str]]:
    blocks: dict[str, str] = {}
    counter = [0]

    def replace_fenced(m: re.Match) -> str:
        original = m.group(0)
        key = f"___FENCED_{counter[0]}___"
        blocks[key] = original.strip("\n")
        counter[0] += 1
        result = key
        if original.startswith("\n"):
            result = "\n" + result
        if original.endswith("\n"):
            result = result + "\n"
        return result

    def replace_inline(m: re.Match) -> str:
        key = f"___INLINE_{counter[0]}___"
        blocks[key] = m.group(0)
        counter[0] += 1
        return key

    out = _FENCED_RE.sub(replace_fenced, content)
    for pattern in _INLINE_CODE_RES:
        out = pattern.sub(replace_inline, out)
    return out, blocks


def _restore_code_blocks(content: str, blocks: dict[str, str]) -> str:
    for key, original in blocks.items():
        content = content.replace(key, original)
    return content


def _rebase_inline_paths(content: str, file_dir: Path) -> str:
    def rewrite(m: re.Match) -> str:
        prefix, path, suffix = m.group(1), m.group(2), m.group(3)
        if path.startswith("/"):
            return m.group(0)
        return f"{prefix}{(file_dir / path).resolve()}{suffix}"

    protected, blocks = _extract_code_blocks(content)
    return _restore_code_blocks(_INLINE_PATH_RE.sub(rewrite, protected), blocks)


def _has_directives(content: str) -> bool:
    protected, _ = _extract_code_blocks(content)
    return bool(_DIRECTIVE_RE.search(protected))


def _process_one_pass(content: str, base_dir: Path) -> str:
    protected, code_blocks = _extract_code_blocks(content)

    def replace_directive(m: re.Match) -> str:
        filepath_str = m.group(1)
        args_str = m.group(2).strip()
        args = dict(_ATTR_RE.findall(args_str))

        full_path = (base_dir / filepath_str).resolve()
        if not full_path.exists():
            msg = f"Inline file not found: {filepath_str}"
            raise FileNotFoundError(msg)

        file_content = full_path.read_text(encoding="utf-8")
        file_content = _rebase_inline_paths(file_content, full_path.parent)

        # Substitute {{placeholders}}
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

        suffix = full_path.suffix.lower()
        if suffix == ".html":
            return "\n".join(line.strip() for line in file_content.splitlines())
        return file_content

    result = _DIRECTIVE_RE.sub(replace_directive, protected)
    return _restore_code_blocks(result, code_blocks)


class Stage(BaseStage):
    name = "inline"
    consumes = ContentType.MARKDOWN
    produces = ContentType.MARKDOWN
    phase = Phase.PREPROCESS
    after = ("vars",)

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        base_dir = context.source_path.parent
        protected, _ = _extract_code_blocks(context.content)
        self.parse_directives("inline", protected, allowed=None)
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

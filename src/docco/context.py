from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class ContentType(StrEnum):
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    ANY = "any"


class Phase(StrEnum):
    PREPROCESS = "preprocess"
    CONVERT = "convert"
    ENRICH = "enrich"
    RENDER = "render"
    POSTPROCESS = "postprocess"


@dataclass
class Context:
    source_path: Path
    output_dir: Path
    config: dict[str, Any]
    content: str | bytes
    content_type: ContentType
    config_dir: Path = field(default_factory=Path.cwd)
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def str_content(self) -> str:
        assert isinstance(self.content, str)
        return self.content

    @classmethod
    def from_file(
        cls,
        source_path: Path,
        output_dir: Path,
        config: dict[str, Any],
        config_dir: Path | None = None,
    ) -> Context:
        content = source_path.read_text(encoding="utf-8")
        return cls(
            source_path=source_path,
            output_dir=output_dir,
            config=config,
            content=content,
            content_type=ContentType.MARKDOWN,
            config_dir=config_dir or source_path.parent,
        )

    @classmethod
    def from_html_file(
        cls,
        source_path: Path,
        output_dir: Path,
        config: dict[str, Any],
        config_dir: Path | None = None,
    ) -> Context:
        content = source_path.read_text(encoding="utf-8")
        return cls(
            source_path=source_path,
            output_dir=output_dir,
            config=config,
            content=content,
            content_type=ContentType.HTML,
            config_dir=config_dir or source_path.parent,
        )

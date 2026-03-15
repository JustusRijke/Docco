from enum import StrEnum

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage


class Arg(StrEnum):
    IMAGE = "image"
    X = "x"
    Y = "y"
    SIZE = "size"


def _replacement(image: str, x: str, y: str, size: str, counter: int) -> str:
    classname = f"page_bg_{counter}"
    return (
        f"<style>\n"
        f"div.pagedjs_page_content:has(.{classname}) {{\n"
        f'    background: url("{image}") no-repeat;\n'
        f"    background-position: {x} {y};\n"
        f"    background-size: {size};\n"
        f"}}\n"
        f"</style>\n"
        f'<div class="{classname}"></div>'
    )


class Stage(BaseStage):
    name = "page-bg"
    consumes = ContentType.HTML
    produces = ContentType.HTML
    phase = Phase.ENRICH

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        content = context.content
        counter = 0

        for full_match, attrs in self.get_directives(content, frozenset(Arg)):
            image = attrs.get(Arg.IMAGE)
            if not image:
                raise ValueError(
                    f"Missing 'image' in page-bg directive: {full_match!r}"
                )
            result = _replacement(
                image=image,
                x=attrs.get(Arg.X, "50%"),
                y=attrs.get(Arg.Y, "0"),
                size=attrs.get(Arg.SIZE, "contain"),
                counter=counter,
            )
            content = content.replace(full_match, result, 1)
            counter += 1

        context.content = content
        if counter:
            self.log.info("Processed %d page-bg directive(s)", counter)
        else:
            self.log.info("No page-bg directives found")
        return context

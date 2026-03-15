import re
from datetime import UTC, datetime

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage

RESERVED_VARS = {"PATH", "DAY", "MONTH", "YEAR"}


def _apply_variables(content: str, variables: dict[str, str]) -> str:
    for name, value in variables.items():
        content = content.replace(f"$${name}$$", value)
    return content


class Stage(BaseStage):
    name = "vars"
    consumes = ContentType.HTML
    produces = ContentType.HTML
    phase = Phase.ENRICH

    def validate_config(self, config: dict) -> None:
        pass  # all keys are user-defined variables

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        vars_config: dict[str, str] = self.get_config(context)

        today = datetime.now(tz=UTC).date()
        variables: dict[str, str] = {
            "PATH": str(context.source_path.parent),
            "DAY": f"{today.day:02d}",
            "MONTH": f"{today.month:02d}",
            "YEAR": str(today.year),
        }
        for name, value in vars_config.items():
            if name in RESERVED_VARS:
                self.log.warning(
                    "Variable '%s' is reserved and cannot be redeclared", name
                )
            else:
                variables[name] = str(value)

        user_vars = set(variables) - RESERVED_VARS
        original = context.content
        context.content = _apply_variables(original, variables)

        undefined = re.findall(r"\$\$(\w+)\$\$", context.content)
        if undefined:
            msg = f"Undefined variables: {', '.join(undefined)}"
            raise ValueError(msg)

        unused = sorted(name for name in user_vars if f"$${name}$$" not in original)
        if unused:
            self.log.warning("Unused variable(s): %s", ", ".join(unused))

        self.log.info("Applied %d variable(s)", len(variables))
        return context

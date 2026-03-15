import shutil
import subprocess

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage
from docco.utils import tmp_file

_INSTALL_URL = "https://github.com/htmlhint/htmlhint#global-installation-and-usage"
_LEVELS = frozenset({"info", "warning", "error"})


class Stage(BaseStage):
    name = "htmlhint"
    consumes = ContentType.HTML
    produces = ContentType.HTML
    phase = Phase.RENDER
    after = ("page", "urls")
    valid_config_keys = frozenset({"enable", "level"})

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        cfg = self.get_config(context)
        if not cfg.get("enable", False):
            self.log.info("Skipped (disabled)")
            return context

        if not shutil.which("htmlhint"):
            msg = f"htmlhint not found. Install it: {_INSTALL_URL}"
            raise RuntimeError(msg)

        level = cfg.get("level", "error")
        if level not in _LEVELS:
            msg = f"[htmlhint] invalid level '{level}', must be one of: {', '.join(sorted(_LEVELS))}"
            raise ValueError(msg)

        with tmp_file(".html", context.content) as tmp_path:
            result = subprocess.run(
                ["htmlhint", str(tmp_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

        output = result.stdout.strip()
        context.artifacts["htmlhint"] = {
            "returncode": result.returncode,
            "output": output,
        }

        if result.returncode != 0:
            getattr(self.log, level)("htmlhint found issues:\n%s", output)
        else:
            self.log.info("No issues found")

        return context

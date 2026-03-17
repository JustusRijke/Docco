from pathlib import Path

from playwright.sync_api import ConsoleMessage, sync_playwright

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage
from docco.utils import tmp_file

_RENDERING_COMPLETE_JS = (
    Path(__file__).parent / "scripts" / "rendering_complete.js"
).read_text(encoding="utf-8")


def _handle_console(msg: ConsoleMessage) -> None:  # pragma: no cover
    text = f"Chromium: {msg.text}"
    match msg.type:
        case "info":
            log.info(text)
        case "warning":
            log.warning(text)
        case "error":
            log.error(text)
        case _:
            log.debug("Chromium %s: %s", msg.type, msg.text)


class Stage(BaseStage):
    name = "pdf"
    consumes = ContentType.HTML
    produces = ContentType.PDF
    phase = Phase.RENDER
    after = ("htmlhint", "urls")
    valid_config_keys = frozenset({"keep_html"})

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        self.log.info("Converting HTML to PDF...")
        html = context.content
        script_tag = f"<script>\n{_RENDERING_COMPLETE_JS}</script>\n"
        if "</head>" in html:
            html = html.replace("</head>", f"{script_tag}</head>", 1)
        elif "</body>" in html:
            html = html.replace("</body>", f"{script_tag}</body>", 1)
        else:
            html += script_tag

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
            )
            page = browser.new_page()
            page.on("console", _handle_console)
            page.on("pageerror", lambda exc: log.error("Chromium error: %s", exc))

            with tmp_file(".html", html) as tmp_html_path:
                page.goto(tmp_html_path.as_uri(), wait_until="networkidle")

            page.wait_for_function(
                "window.pagedJsRenderingComplete === true",
                timeout=5 * 60 * 1000,
            )  # Long timeout (5 minutes) due to slow github runner

            pdf_bytes = page.pdf(print_background=True, prefer_css_page_size=True)
            browser.close()

        context.content = pdf_bytes
        context.content_type = ContentType.PDF
        self.log.info("Rendered HTML to PDF")

        if self.get_config(context).get("keep_html"):
            out = context.output_dir / f"{context.source_path.stem}.html"
            out.write_text(html, encoding="utf-8")
            self.log.debug("Written intermediate HTML: %s", out)

        return context


log = Stage.log

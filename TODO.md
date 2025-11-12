# Must have
- warnings weasyprint are outputted when using weasyprint.exe, but errors/warnings are not shown (logged) when using the weasyprint python module. fix this.
- allow multiple .po files (so i can add translations for inlined stuff, like standard dislaimers etc)
- notify user if pot file changed / user needs to update translations or when translations are missing
- path var (of: global var, voor bijv titles)
- how to define a table/div or section thingy that fills a whole page? so like a table with 100% width and 100% height (taking into consideration header/footer and page margins, so only the "body" of the page)

# Nice to have
- add cli option "watch", where docco will watch for changes in a folder in the given md/css file, and regenerate the pdf immediately, or (must more complex) create a vscode plugin
- style.css: adjust page margins for double sided printing, take both portrait and landscape into consideration; note that is not a docco functionality, simply an example of using css, so no need to update readme.md/claude.me, but do note this subtle thing in the feature showcase (and mention that is is defined in style.css)
- use git version tag and/or branch+commit id instead of hardcoded version info (both pyproject.toml and the cli version info), or suggest a better way (best practice)
- coverage: GitHub dependabot/actions (win&deb)
- laat Claude inspireren door [GitHub - ljpengelen/markdown-to-pdf: A script to convert Markdown to PDF](https://github.com/ljpengelen/markdown-to-pdf)
- reset CSS (* margins 0)
- zie sectie over image optimalisation [Common Use Cases - WeasyPrint 66.0 documentation](https://doc.courtbouillon.org/weasyprint/stable/common_use_cases.html)
- comments mogelijk maken, en optioneel zichtbaar in pdf (geel gearceerde) en log output

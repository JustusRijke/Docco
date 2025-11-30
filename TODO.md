# Must have
- allow multiple .po files (so i can add translations for inlined stuff, like standard dislaimers etc)
- na afronden PT manual, zooi overnemen naar examples
-- documenteren downloaden fonts
- bug: 0 dpi resultaat (svg?)
- check if PDF file is open (can be written), weasyprint melding lelijk

# Nice to have
- syntax aanpassen directives, aan laten sluiten op functies markdown-py, pandoc, quarto, ...
- html tester (valid html?), ook toepassen op inlines
- pdf beveiligen (geen copy/paste? flatten?)
- if/endif directives icm arguments gebruiken uit frontmatter, tbv meerdere modellen maken met 1 md file

# Won't have
- add cli option "watch", where docco will watch for changes in a folder in the given md/css file, and regenerate the pdf immediately, or (must more complex) create a vscode plugin
- use git version tag and/or branch+commit id instead of hardcoded version info (both pyproject.toml and the cli version info), or suggest a better way (best practice)
- coverage: GitHub dependabot/actions (win&deb)
- laat Claude inspireren door [GitHub - ljpengelen/markdown-to-pdf: A script to convert Markdown to PDF](https://github.com/ljpengelen/markdown-to-pdf)
- comments mogelijk maken, en optioneel zichtbaar in pdf (geel gearceerde) en log output


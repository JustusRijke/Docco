---
languages: EN DE
css:
  - "css/page.css"
  - "css/header_footer.css"
header:
  file: "header.html"
  title: "Multilingual Document"
  author: "Docco Team"
footer:
  file: "footer_multilingual.html"
  title: "Docco"
---

# Multilingual Document Example

This document demonstrates Docco's multi-language support capabilities.

## Shared Content

This section is available in all languages and serves as common content across the document.

## Language-Specific Sections

<!-- lang:EN -->
### English Version

This is English-specific content that demonstrates language filtering.

Features:
- Multi-language support
- Language-tagged content blocks
- Automatic generation of separate files per language
- YAML frontmatter for language configuration

Use `<!-- lang:EN -->...<!-- /lang -->` to mark English-only content.
<!-- /lang -->

<!-- lang:DE -->
### Deutsche Version

Dies ist deutschsprachiger Inhalt, der die Sprachfilterung demonstriert.

Funktionen:
- Multi-Sprachen-Unterstützung
- Sprachgekennzeichnete Inhaltsblöcke
- Automatische Erstellung separater Dateien pro Sprache
- YAML-Frontmatter für Sprachkonfiguration

Verwenden Sie `<!-- lang:DE -->...<!-- /lang -->`, um nur auf Deutsch verfügbare Inhalte zu markieren.
<!-- /lang -->

## Conclusion

This multilingual document showcases how Docco enables content delivery in multiple languages from a single source file.

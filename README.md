# Python-Based Documentation Builder
## Technical Specification

---

## Project Goal

Develop a Python tool to generate professional product documentation (A4 PDF) using HTML/CSS for layout. The tool must allow flexible, modular content creation with reusable parts and automatic document structure handling.

---

## 1. Functional Requirements

### 1.1 PDF Output

* Output format: **A4 PDF**
* Consistent header, footer, and page numbering
* Must support **mixed orientations** (portrait + landscape pages)
* Layout and typography fully defined via **CSS** (modern print styling)
* TOC and page numbering must remain accurate across orientations

**Context**: Documents must be A4-sized PDFs, primarily portrait, with some addendum sections (e.g., drawings) in landscape. Mixed orientations in one PDF are needed for flexibility.

### 1.2 Document Structure

* Hierarchical sectioning: numbered headings (`1`, `1.1`, `1.1.1`, …)
* Support for **addendum sections** (`A:`, `B:` …) with independent numbering
* Automatic **Table of Contents** generation with correct page numbers
* Reusable content modules (e.g., disclaimer, intro) importable from Python files
* Content composed via **Python string construction**, not templates

**Context**: Sections require auto-numbered headers (e.g., "1 Intro", "1.1 Specifications") for clarity. Addendum sections use letters (e.g., "A: Overview Drawing"). Numbers should be managed programmatically.

### 1.3 Content Authoring

* Core text authored in **Markdown** (bold, italic, links, lists, tables)
* Markdown converted to HTML before rendering
* Embedded **images** (PNG/JPG/SVG) with:
  * Automatic resizing using Pillow to avoid bloated PDFs
  * Optional captions below images
* Support for **nested tables** and simple layout tables

**Context**: Paragraphs use Markdown for simplicity, supporting basic formatting to keep content authoring lightweight. Documents include tables (potentially nested) for product specs, requiring clean styling and proper pagination.

### 1.4 Simplicity & Maintainability

* Keep the code **simple, explicit, and readable** – no unnecessary abstraction layers
* Focus on maintainability over automation complexity
* Initial implementation as a **single script with supporting content module**
* Clean separation of layout (CSS) and logic (Python)
* Refactor and re-evaluate architecture after achieving a working example

**Context**: Code must be easy to understand years later, avoiding complex abstractions to ensure maintainability. Documents are small (~50 pages max), so performance optimization is not a primary concern.

---

## 2. Non-Functional Requirements

| Aspect              | Requirement                                             |
| ------------------- | ------------------------------------------------------- |
| **Performance**     | Documents up to ~50 pages should render quickly (<10s) |
| **Portability**     | Must run on standard Python environment (≥3.10)        |
| **Dependencies**    | All open source, permissive licenses                   |
| **Maintainability** | Clear code organization and minimal "magic"            |
|
---

## 3. Required Libraries

| Purpose          | Library            | License | Notes                                                                    |
| ---------------- | ------------------ | ------- | ------------------------------------------------------------------------ |
| PDF rendering    | **WeasyPrint**     | BSD     | Primary rendering engine; supports `@page`, headers/footers, mixed orientation, automatic TOC |
| Markdown parsing | **markdown-it-py** | MIT     | Fast, clean conversion for Markdown subset                               |
| Image handling   | **Pillow**         | HPND    | Resize, compress, and re-encode images                                   |

**Installation (Debian)**: 
`pip install weasyprint markdown-it-py pillow`
`apt install weasyprint`

**Note on TOC**: WeasyPrint's built-in CSS Paged Media support will be used for automatic TOC generation. This should be tested early in the project to verify it meets requirements.

---

## 4. Suggested Architecture (Initial Implementation)

Start with a minimal structure and refactor after achieving a working example:

```
docs_tool/
├── content/               # reusable content modules
│   └── standard.py       # disclaimers, common sections
├── assets/
│   ├── style.css         # print layout, headers, footers, TOC
│   └── images/           # source images
├── output/
│   ├── optimized_images/ # resized images for PDF
│   ├── debug.html        # optional: for browser debugging
│   └── final.pdf
└── main.py               # single script: content → HTML → PDF
```

### Architecture Principles

The system follows a **3-stage pipeline**:

1. **Asset Preparation**: Optimize images with Pillow, save to `output/optimized_images/`
2. **Document Assembly**: Build complete HTML document via Python string construction
   - Manage hierarchical numbering (sections: `1.1.2`, addendums: `A`, `B`)
   - Convert Markdown fragments to HTML
   - Concatenate all content into single HTML string
3. **PDF Rendering**: Pass HTML + CSS to WeasyPrint for final PDF generation

---

## 5. Processing Flow

1. **Prepare assets**: Resize and optimize images using Pillow
2. **Assemble document content** from modular Python functions
3. **Apply section numbering**: Track and apply hierarchical numbers programmatically
4. **Convert Markdown** fragments to HTML using markdown-it-py
5. **Compose full HTML document** (sections, tables, images) via string construction
6. **Render PDF** with WeasyPrint (single pass, relying on CSS for TOC)
7. **(Optional)** Save intermediate HTML for browser-based layout debugging

---

## 6. Key Implementation Details

### 6.1 HTML Generation
- Use Python string construction (direct concatenation or f-strings)
- No templating engine required initially
- Keep HTML generation logic simple and explicit

### 6.2 Section Numbering
- Python logic manages hierarchical counters (e.g., `[1, 1, 2]` for section 1.1.2)
- Separate letter-based counter for addendum sections
- Numbers inserted directly into HTML heading tags

### 6.3 Table of Contents
- **Trust WeasyPrint's built-in TOC capabilities** via CSS Paged Media
- Test this early to verify it handles:
  - Correct page numbers
  - Mixed orientations
  - PDF bookmarks
- Fall back to 2-pass approach only if needed

### 6.4 Image Handling
- Resize images to reasonable dimensions (~300px width or as appropriate)
- Optimize before embedding to control PDF file size
- Support optional captions via HTML `<figure>` and `<figcaption>` tags

### 6.5 Reusable Content
- Store common content (disclaimers, standard sections) in `content/` module
- Import as Python strings or functions
- Allow both raw Markdown and pre-formatted HTML

---

## 7. Deliverables

* Python project with `requirements.txt` for dependencies
* Single script entry point (`main.py`) that generates complete PDF from defined sections
* Example CSS file with A4 layout, headers, footers, TOC styling
* Example content module with reusable sections
* Short README with:
  - Setup instructions
  - Basic usage example
  - Notes on testing TOC generation early

---

## 8. Development Strategy

1. **Phase 1**: Implement minimal working example
   - Single portrait page with one section
   - Basic Markdown conversion
   - Simple PDF output
   - **Test WeasyPrint TOC generation**

2. **Phase 2**: Add core features
   - Hierarchical section numbering
   - Image optimization and embedding
   - Tables support
   - Headers/footers

3. **Phase 3**: Advanced features
   - Mixed portrait/landscape orientation
   - Addendum sections
   - Reusable content modules

4. **Phase 4**: Refactor and optimize
   - Evaluate single-script approach
   - Refactor into modules if needed
   - Optimize performance if required

---

## Notes for Development Team

* **Prioritize simplicity**: Start with the simplest implementation that works
* **Test TOC early**: Verify WeasyPrint's automatic TOC meets all requirements before implementing alternatives
* **Debug in browser**: Save intermediate HTML and verify layout in browser before PDF conversion
* **Image sizing**: Experiment with optimal image dimensions for quality vs. file size
* **CSS first**: Define all layout, spacing, and styling in CSS rather than programmatically
* **Refactor later**: Don't over-engineer the initial implementation; refactor after achieving working prototype

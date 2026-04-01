---
name: md2pdf
description: >
  Convert Markdown documents to professionally typeset PDF files with reportlab.
  Handles CJK/Latin mixed text, fenced code blocks, tables, blockquotes, cover pages,
  clickable TOC, PDF bookmarks, watermarks, and page numbers. Supports multiple
  color themes (Warm Academic, Nord, GitHub Light, Solarized, etc.) and is
  battle-tested for Chinese technical reports. Use this skill whenever the user
  wants to turn a .md file into a styled PDF, generate a report PDF from markdown,
  or create a print-ready document from markdown content — especially if CJK
  characters, code blocks, or tables are involved. Also trigger when the user
  mentions "markdown to PDF", "md转pdf", "报告生成", or asks for a "typeset" or
  "professionally formatted" PDF from markdown source.
license: MIT
compatibility: >
  Requires Python 3.8+ and reportlab (`pip install reportlab`).
  macOS: uses Palatino, Songti SC, Menlo (pre-installed).
  Linux: uses Carlito, Liberation Serif, Droid Sans Fallback, DejaVu Sans Mono.
metadata:
  author: lovstudio
  version: "1.0.0"
  tags: markdown pdf cjk reportlab typesetting
---

# md2pdf — Markdown to Professional PDF

This skill converts any Markdown file into a publication-quality PDF using Python's
reportlab library. It was developed through extensive iteration on real Chinese
technical reports and solves several hard problems that naive MD→PDF converters
get wrong.

## When to Use

- User wants to convert `.md` → `.pdf`
- User has a markdown report/document and wants professional typesetting
- Document contains CJK characters (Chinese/Japanese/Korean) mixed with Latin text
- Document has fenced code blocks, markdown tables, or nested lists
- User wants a cover page, table of contents, or watermark in their PDF

## Quick Start

```bash
python md2pdf/scripts/md2pdf.py \
  --input report.md \
  --output report.pdf \
  --title "My Report" \
  --author "Author Name" \
  --theme warm-academic
```

All parameters except `--input` are optional — sensible defaults are applied.

## Interactive Workflows

When converting a document, the skill should interactively ask the user about
optional enhancements before running the conversion.

### Workflow: Frontispiece Image

Ask the user if they want a frontispiece (扉页) image inserted after the cover page:

1. **Skip** — No frontispiece image
2. **Local image** — User provides a local file path (png/jpg)
3. **AI generate** — Generate one using an image generation tool based on document content

If "AI generate": read the document title and first few paragraphs, craft a prompt
matching the document's topic, generate the image, show it for approval, then pass
via `--frontispiece /path/to/image.png`.

### Workflow: Watermark

Ask the user if they want a watermark (水印) on every page:

1. **Skip** — No watermark
2. **Custom text** — User provides watermark text (e.g. "DRAFT", "内部资料", "仅供学习")

If provided, pass via `--watermark "文字内容"`. The watermark renders as a faint
diagonal overlay on content pages. Common patterns:
- Draft/review: "DRAFT", "草稿", "待审阅"
- Access control: "内部资料 请勿外传", "Confidential"
- Attribution: Author name or organization name

### Workflow: Back Cover Promotional Materials

Ask the user if they want promotional materials (宣传物料) on the back cover:

1. **Skip** — No promotional materials
2. **Image** — Business card, QR code, or branding image (png/jpg)
3. **Text-only** — Name, website, slogan, etc.

If image: pass via `--banner <path>`. If text: use `--disclaimer` and `--copyright`.
Common materials: WeChat QR code, business card, brand logo, multi-platform QR composite.

## Architecture

```
Markdown → Preprocess (split merged headings) → Parse (code-fence-aware) → Story (reportlab flowables) → PDF build
```

Key components:
1. **Font system**: Palatino (Latin body), Songti SC (CJK body), Menlo (code) on macOS; auto-fallback on Linux
2. **CJK wrapper**: `_font_wrap()` wraps CJK character runs in `<font>` tags for automatic font switching
3. **Mixed text renderer**: `_draw_mixed()` handles CJK/Latin mixed text on canvas (cover, headers, footers)
4. **Code block handler**: `esc_code()` preserves indentation and line breaks in reportlab Paragraphs
5. **Smart table widths**: Proportional column widths based on content length, with 18mm minimum
6. **Bookmark system**: `ChapterMark` flowable creates PDF sidebar bookmarks + named anchors
7. **Heading preprocessor**: `_preprocess_md()` splits merged headings like `# Part## Chapter` into separate lines

## Hard-Won Lessons

### CJK Characters Rendering as □

reportlab's `Paragraph` only uses the font in ParagraphStyle. If `fontName="Mono"` but
text contains Chinese, they render as □. **Fix**: Always apply `_font_wrap()` to ALL text
that might contain CJK, including code blocks.

### Code Blocks Losing Line Breaks

reportlab treats `\n` as whitespace. **Fix**: `esc_code()` converts `\n` → `<br/>` and
leading spaces → `&nbsp;`, applied BEFORE `_font_wrap()`.

### CJK/Latin Word Wrapping

Default reportlab breaks lines only at spaces, causing ugly splits like "Claude\nCode".
**Fix**: Set `wordWrap='CJK'` on body/bullet styles to allow breaks at CJK character boundaries.

### Canvas Text with CJK (Cover/Footer)

`drawString()` / `drawCentredString()` with a Latin font can't render 年/月/日 etc.
**Fix**: Use `_draw_mixed()` for ALL user-content canvas text (dates, stats, disclaimers).

## Configuration Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | (required) | Path to markdown file |
| `--output` | `output.pdf` | Output PDF path |
| `--title` | From first H1 | Document title for cover page |
| `--subtitle` | `""` | Subtitle text |
| `--author` | `""` | Author name |
| `--date` | Today | Date string |
| `--version` | `""` | Version string for cover |
| `--watermark` | `""` | Watermark text (empty = none) |
| `--theme` | `warm-academic` | Color theme name |
| `--theme-file` | `""` | Custom theme JSON file path |
| `--cover` | `true` | Generate cover page |
| `--toc` | `true` | Generate table of contents |
| `--page-size` | `A4` | Page size (A4 or Letter) |
| `--frontispiece` | `""` | Full-page image after cover |
| `--banner` | `""` | Back cover banner image |
| `--header-title` | `""` | Report title in page header |
| `--footer-left` | author | Brand/author in footer |
| `--stats-line` | `""` | Stats on cover |
| `--stats-line2` | `""` | Second stats line |
| `--edition-line` | `""` | Edition line at cover bottom |
| `--disclaimer` | `""` | Back cover disclaimer |
| `--copyright` | `""` | Back cover copyright |
| `--code-max-lines` | `30` | Max lines per code block |

## Themes

Available: `warm-academic`, `nord-frost`, `github-light`, `solarized-light`,
`paper-classic`, `ocean-breeze`.

Each theme defines: page background, ink color, accent color, faded text, border, code background, watermark tint.

## Dependencies

```bash
pip install reportlab --break-system-packages
```

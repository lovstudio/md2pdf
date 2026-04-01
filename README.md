# md2pdf

Markdown to professionally typeset PDF — an [agent skill](https://agentskills.io) for AI coding assistants.

## Features

- **CJK/Latin mixed text** with automatic font switching (Palatino + Songti SC)
- Fenced code blocks with preserved indentation and syntax highlighting colors
- Markdown tables with smart proportional column widths
- Cover page, clickable TOC, PDF bookmarks, page numbers
- Frontispiece (full-page image), back cover with branding
- Running headers with report title + chapter name
- Watermark support (diagonal text overlay)
- 6 color themes (Warm Academic, Nord, GitHub Light, Solarized, Paper Classic, Ocean Breeze)
- macOS and Linux font auto-detection

## Install

```bash
npx skills add lovstudio/md2pdf -g
```

## Usage

The skill is automatically activated when you ask your AI assistant to convert Markdown to PDF.

**Direct CLI usage:**

```bash
pip install reportlab

python md2pdf/scripts/md2pdf.py \
  --input report.md \
  --output report.pdf \
  --title "My Report" \
  --subtitle "A Comprehensive Analysis" \
  --author "Author Name" \
  --theme warm-academic
```

## Themes

| Theme | Description |
|-------|-------------|
| `warm-academic` | Terracotta accent on warm ivory — scholarly and warm |
| `nord-frost` | Steel blue on arctic gray — clean and modern |
| `github-light` | Blue accent on white — familiar developer aesthetic |
| `solarized-light` | Orange accent on cream — easy on the eyes |
| `paper-classic` | Red accent on white — traditional print look |
| `ocean-breeze` | Teal accent on seafoam — fresh and calming |

## License

MIT

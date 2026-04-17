# Changes — fix/frontmatter-and-pdf-layout

## Summary

Five fixes to `lovstudio-any2pdf/scripts/md2pdf.py` addressing blank pages,
header title mismatch, code block alignment, and a new frontmatter feature
that makes markdown files self-contained.

---

## 1. YAML Frontmatter Support (new feature)

**Problem:** All document metadata (title, author, theme, etc.) had to be
passed as CLI arguments. The markdown file itself carried no metadata, making
it hard to reproduce a build without remembering the exact command.

**Fix:** The script now parses a YAML-style frontmatter block at the top of
the markdown file:

```markdown
---
title: My Document
subtitle: Version 1.0 · Platform: Linux
author: Acme Corp
footer-left: Acme Corp
copyright: © Acme Corp
theme: ieee-journal
watermark: DRAFT
---

## Chapter 1
...
```

All CLI parameters are supported as frontmatter keys (using the same names as
the `--` flags, e.g. `footer-left`, `code-max-lines`). **CLI arguments always
take precedence** over frontmatter values, so existing workflows are unaffected.

With frontmatter, the minimal invocation becomes:

```bash
python md2pdf.py --input report.md --output report.pdf
```

---

## 2. Blank Page After TOC (bug fix)

**Problem:** When a markdown file contains a `# Title` heading and a cover
page is generated via `--title` (or frontmatter), the H1 heading produces a
full chapter-divider page (PageBreak + large Spacer + title Paragraph +
decorations). This page appeared between the TOC and the first `##` chapter,
creating a blank-looking page.

**Fix:** When a cover title is provided, strip all visual elements generated
by the H1 heading (Spacer, title Paragraph, decoration flowables, and the
following H2's leading PageBreak). The H1 `ChapterMark` flowable is **kept**
so TOC anchor links remain valid.

The stripping only triggers when:
- `cover=True` (default), AND
- The first `ChapterMark` in `story_content` is level 0 (H1)

Documents without a `# Title` heading are unaffected.

---

## 3. Header Title One-Page Lag (bug fix)

**Problem:** The right side of the page header displayed the current chapter
name via `_cur_chapter[0]`. Because reportlab's `onPage` callback fires
*before* the page's flowables are rendered, `_cur_chapter[0]` always held the
*previous* page's chapter — causing a one-page lag (e.g. page 3 showed
"Chapter 1" while its content was already "Chapter 2").

**Affected locations:**
- `_draw_page_decoration()` — `top-band` style (used by `ieee-journal`)
- `_normal_page()` — `full` header style

**Fix:** Replace `_cur_chapter[0]` with the fixed document title
(`self.cfg.get("title", "")`). The header now consistently shows the document
title on every page, which is the correct behaviour for a technical manual or
report. Dynamic chapter tracking would require a two-pass build to resolve
correctly; the fixed title is the pragmatic solution.

---

## 4. Code Block Mid-Line Space Collapsing (bug fix)

**Problem:** `esc_code()` only converted *leading* spaces to `&nbsp;`. Spaces
in the middle of a line (e.g. padded columns in ASCII diagrams, table output,
or aligned assignments) were left as regular HTML spaces and collapsed to a
single space by reportlab's Paragraph renderer.

**Before:**
```python
stripped = e.lstrip(' ')
indent = len(e) - len(stripped)
out.append('&nbsp;' * indent + stripped)
```

**After:**
```python
out.append(e.replace(' ', '&nbsp;'))
```

This preserves both indentation and mid-line alignment for all code blocks.

---

## 5. H2 Chapter Spacer Reduction (style fix)

**Problem:** Each `##` heading inserted `Spacer(1, self.body_h * 0.30)` —
30% of the page height (~74 mm on A4). This is appropriate for book-style
chapter openers but creates excessive whitespace in technical manuals and
reports where chapters are short and numerous.

**Fix:** Changed to a fixed `Spacer(1, 8*mm)`, which provides a clean visual
break without wasting half a page.

---

## Usage Example

```markdown
---
title: xxx manual
subtitle: Version 0.1.0 · Platform: Linux
author: Acme Biotech Ltd.
footer-left: Acme Biotech Ltd.
copyright: © Acme Biotech Ltd.
theme: ieee-journal
---

## 1. Overview
...
```

```bash
# With uv (recommended — no pip install needed, isolated env)
uv run --with reportlab /path/to/md2pdf.py --input report.md --output report.pdf

# With pip
python md2pdf.py --input report.md --output report.pdf

# CLI args override frontmatter
python md2pdf.py --input manual.md --output manual.pdf --theme warm-academic
```

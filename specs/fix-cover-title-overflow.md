---
title: Fix Cover Page Title Overflow
status: done
date: 2026-04-02
---

# Problem

Cover page titles rendered via `_draw_mixed()` use a fixed font size (38pt centered,
34pt left-aligned, 32pt minimal) with no width constraint. Long titles overflow the
page boundaries and get clipped.

# Root Cause

`_draw_mixed()` calls `c.drawString()` at a fixed size with no awareness of available
page width. There is no shrink-to-fit or wrapping logic.

# Fix

Add a `max_w` parameter to `_draw_mixed()`. When provided, auto-shrink the font size
(with a floor of 18pt) until the text fits within `max_w`. Apply this in all three
cover styles with appropriate available widths:

- **centered**: `page_w - 40mm` (20mm margin each side)
- **left-aligned**: `page_w - lx(25mm) - 20mm`
- **minimal**: `page_w - 50mm` (25mm margin each side)

# Test

```bash
python3 sgc-any2pdf/scripts/md2pdf.py \
  --input test-long-title.md \
  --output /tmp/test-long-title2.pdf \
  --theme warm-academic \
  --title "Design System Best Practices (Team Edition) — A Comprehensive Guide to Building Scalable UI"
```

Verify title is fully visible and does not overflow page edges.

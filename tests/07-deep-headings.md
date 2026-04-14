---
title: "Deep Headings Regression Test"
subtitle: "H4/H5/H6 must not hang the parser"
author: "any2pdf"
version: "test"
---

# Part

Body paragraph before the nested headings.

## Chapter

### Section (H3 — already supported)

Body text under H3.

#### Subsection (H4 — previously hung the parser)

Body text under H4. The parse_md loop used to never advance `i` when it saw a
deeper heading like this, because H4–H6 had no handler and the paragraph
collector broke on lines starting with `#`. The result was 100% CPU forever.

##### Deeper subsection (H5)

Body text under H5 with some `inline code` and **bold**.

###### Deepest (H6)

Body text under H6.

#### Another H4 right after a table

| Col A | Col B | Col C |
|-------|-------|-------|
| a1    | b1    | c1    |
| a2    | b2    | c2    |

Body paragraph after the table. This used to never render because the H4 above
would spin forever.

#### H4 with & ampersand and `${VAR}/path.md`

Inline code inside deep heading context should not break anything.

#!/bin/bash
# Batch test: generate PDFs for all test cases across themes
SCRIPT="$(dirname "$0")/../lov-any2pdf/scripts/md2pdf.py"
OUT="/tmp/any2pdf-tests"
rm -rf "$OUT" && mkdir -p "$OUT"

THEMES=("warm-academic" "nord-frost" "tufte")

for md in "$(dirname "$0")"/*.md; do
  name=$(basename "$md" .md)
  # Extract frontmatter fields
  title=$(sed -n 's/^title: *"\(.*\)"/\1/p' "$md")
  subtitle=$(sed -n 's/^subtitle: *"\(.*\)"/\1/p' "$md")
  author=$(sed -n 's/^author: *"\(.*\)"/\1/p' "$md")
  version=$(sed -n 's/^version: *"\(.*\)"/\1/p' "$md")

  args=()
  [ -n "$title" ] && args+=(--title "$title")
  [ -n "$subtitle" ] && args+=(--subtitle "$subtitle")
  [ -n "$author" ] && args+=(--author "$author")
  [ -n "$version" ] && args+=(--version "$version")

  for theme in "${THEMES[@]}"; do
    out="$OUT/${name}_${theme}.pdf"
    python3 "$SCRIPT" --input "$md" --output "$out" --theme "$theme" "${args[@]}" 2>&1 | tail -1
  done
done

echo ""
echo "Output: $OUT"
open "$OUT"

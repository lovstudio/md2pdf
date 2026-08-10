#!/bin/bash
# Dev mode: symlink installed skill to source repo, Ctrl+C to stop and restore

SKILL_NAME="lov-any2pdf"
SKILL_DIR="$HOME/.claude/skills/$SKILL_NAME"
SOURCE_DIR="$(cd "$(dirname "$0")/$SKILL_NAME" && pwd)"

cleanup() {
  echo ""
  rm -f "$SKILL_DIR"
  if [ -d "$SKILL_DIR.bak" ]; then
    mv "$SKILL_DIR.bak" "$SKILL_DIR"
    echo "Restored installed skill from backup."
  else
    echo "Symlink removed. Run 'npx skills' to reinstall."
  fi
  echo "Dev mode OFF."
  exit 0
}
trap cleanup INT TERM

if [ -d "$SKILL_DIR" ] && [ ! -L "$SKILL_DIR" ]; then
  mv "$SKILL_DIR" "$SKILL_DIR.bak"
fi

rm -f "$SKILL_DIR"
ln -s "$SOURCE_DIR" "$SKILL_DIR"

echo "Dev mode ON → $SOURCE_DIR"
echo "Edit source freely. New CC sessions pick up changes."
echo "Ctrl+C to stop."
echo ""

while true; do sleep 86400; done

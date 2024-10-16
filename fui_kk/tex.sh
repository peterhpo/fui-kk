#!/usr/bin/env bash

# Check if correct number of arguments is provided
if [ $# -ne 1 ]; then
  echo "Usage: $0 <directory_name>"
  exit 1
fi

# Check if pandoc is available
if ! command -v pandoc &> /dev/null; then
  echo "Error: pandoc is not installed."
  exit 1
fi

BASE_DIR="./data/$1"
RESOURCE_DIR="$BASE_DIR/resources"
echo "$BASE_DIR/resources"

# Create necessary directories
mkdir -p "$BASE_DIR/outputs/tex" \
         "$BASE_DIR/inputs/md" \
         "$BASE_DIR/outputs/report" \
         "$BASE_DIR/inputs/tex"

# Copy resource directory if it doesn't exist
if [ ! -d "$RESOURCE_DIR" ]; then
  cp -r ./resources "$RESOURCE_DIR"
fi

# Copy specific files
echo "$RESOURCE_DIR/fui/fui-kompendium-burgund.pdf"
cp "$RESOURCE_DIR/fui/fui-kompendium-burgund.pdf" "$BASE_DIR/outputs/report/ifi-kompendium-forside-bm.pdf"
cp "$RESOURCE_DIR/ifikompendium/ifikompendium.tex" "$BASE_DIR/outputs/report"
cp "$RESOURCE_DIR/ifikompendium/ifikompendiumforside.sty" "$BASE_DIR/outputs/report"

# Copy header and tail templates if they don't exist
if [ ! -f "$BASE_DIR/inputs/tex/header.tex" ]; then
  cp ./templates/header.tex "$BASE_DIR/inputs/tex/header.tex"
fi

if [ ! -f "$BASE_DIR/inputs/tex/tail.tex" ]; then
  cp ./templates/tail.tex "$BASE_DIR/inputs/tex/tail.tex"
fi

# Change to markdown directory and convert files
cd "$BASE_DIR/inputs/md" || exit 1
find . -iname "*.md" -type f -exec sh -c 'pandoc "{}" -o "../../outputs/tex/${0%.md}.tex"' {} \;

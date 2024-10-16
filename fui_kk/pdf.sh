#!/usr/bin/env bash

function triplelatex {
    local input_file="$1"
    local filename=$(basename "$input_file")
    local filename="${filename%.*}"

    mkdir -p "./.latex"

    # Move _minted directory if it exists
    if [ -d "./.latex/_minted-$filename" ]; then
       mv "./.latex/_minted-$filename" ./
    fi

    # Run pdflatex
    pdflatex -shell-escape -output-directory "./.latex" "${input_file/.pdf/.tex}"

    # Move generated PDFs to current working directory
    mv ./.latex/*.pdf ./

    # Restore _minted directory if it was moved
    if [ -d "_minted-$filename" ]; then
        mv "_minted-$filename" ./.latex
    fi
}

# Ensure correct number of arguments
if [ $# -ne 1 ]; then
  echo "Usage: $0 <identifier>"
  exit 1
fi

# Create and navigate to the report directory
TARGET_DIR="./data/$1/outputs/report"
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR" || { echo "Failed to change directory to $TARGET_DIR"; exit 1; }

# Run the triplelatex function
triplelatex "fui-kk_report_$1.tex"

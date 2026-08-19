#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../supplement"
pdflatex -interaction=nonstopmode supplement.tex > /dev/null 2>&1
bibtex supplement > /dev/null 2>&1
for i in 1 2 3; do pdflatex -interaction=nonstopmode supplement.tex > /dev/null 2>&1; done
echo "--- errors ---"; grep -c '^!' supplement.log || true
echo "--- undefined ---"; grep -cE 'undefined (references|citations)' supplement.log || true
echo "--- pages ---"; pdfinfo supplement.pdf 2>/dev/null | grep '^Pages'

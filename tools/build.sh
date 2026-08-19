#!/usr/bin/env bash
# Build main.pdf (5 pdflatex + bibtex) from paper/is2/paper.
# Usage: build.sh [--quick]   (--quick = 2 passes, no bibtex; for intermediate checks)
set -uo pipefail
cd "$(dirname "$0")/../paper"
if [ "${1:-}" = "--quick" ]; then
  pdflatex -interaction=nonstopmode -halt-on-error main.tex > /dev/null 2>&1
  pdflatex -interaction=nonstopmode -halt-on-error main.tex > /dev/null 2>&1
else
  pdflatex -interaction=nonstopmode -halt-on-error main.tex > /dev/null 2>&1
  bibtex main > /dev/null 2>&1
  for i in 1 2 3 4; do
    pdflatex -interaction=nonstopmode -halt-on-error main.tex > /dev/null 2>&1
  done
fi
rc=$?
echo "--- errors ---"; grep -c '^!' main.log || true
echo "--- undefined refs/cites ---"; grep -cE 'undefined (references|citations)' main.log || true
echo "--- pages ---"; pdfinfo main.pdf 2>/dev/null | grep '^Pages'

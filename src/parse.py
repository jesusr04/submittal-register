"""Stage 1 — Parse: spec PDF -> plain text, structure preserved.

The only job here is to turn one PDF into clean text with page breaks marked, so
the next stage can split it into CSI sections. Eyeball the output before trusting
anything downstream (`python -m src.parse data/spec.pdf`): garbage text here
means a garbage register.

Real spec books print a running header/footer on every page (project name,
section number + title, "Page X of Y"). Left in, those repeated lines fragment a
multi-page section — section-splitting matches the per-page header number on each
page and keeps only the longest single page. So we strip the repeating page
furniture here, before the text ever reaches `sections.py`.
"""
import re
from collections import Counter

import fitz  # pymupdf

# A visible marker so section-splitting can tell where a printed page ended.
# Plain text, unlikely to collide with spec content.
PAGE_BREAK = "\n\f\n"

# Running headers/footers live at the top/bottom of a page, never mid-flow, so we
# only ever consider the first/last few non-blank lines of each page as candidates.
_EDGE_TOP = 6
_EDGE_BOTTOM = 4
_DIGITS = re.compile(r"\d+")
# A bare CSI number line ("05 32 23 STEEL ROOF DECKING") — the variable line of the
# running header. Note: a real section header reads "SECTION 05 31 23", so the
# leading-anchor here deliberately does NOT allow a "SECTION " prefix.
_CSI_HEADER = re.compile(r"^\s*\d{2} \d{2} \d{2}(?:\.\d{2})?\b")


def load_text(path: str) -> str:
    """Concatenate every page's text (minus running headers/footers), page-broken."""
    doc = fitz.open(path)
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return PAGE_BREAK.join(_strip_running_headers(pages))


def _edge_indices(lines: list[str]) -> list[int]:
    """Indices of the first _EDGE_TOP and last _EDGE_BOTTOM non-blank lines."""
    nonblank = [i for i, ln in enumerate(lines) if ln.strip()]
    return sorted(set(nonblank[:_EDGE_TOP] + nonblank[-_EDGE_BOTTOM:]))


def _norm(line: str) -> str:
    """Collapse digit runs so 'Page 1 of 5' and 'Page 2 of 5' compare equal."""
    return _DIGITS.sub("#", line.strip())


def _strip_running_headers(pages: list[str]) -> list[str]:
    """Drop the header/footer lines that repeat across most pages.

    Two passes: (1) any edge line whose digit-normalized form recurs on at least
    half the pages is page furniture; (2) within the top edge, a bare CSI-number
    header line is furniture too if it sits between such lines (its number varies
    per section, so it never trips the frequency test on its own).
    """
    if not pages:
        return pages

    page_lines = [p.split("\n") for p in pages]

    counts: Counter[str] = Counter()
    for lines in page_lines:
        for norm in {_norm(lines[i]) for i in _edge_indices(lines) if lines[i].strip()}:
            counts[norm] += 1
    threshold = max(5, len(pages) // 2)
    boiler = {norm for norm, c in counts.items() if c >= threshold}

    cleaned: list[str] = []
    for lines in page_lines:
        edge = _edge_indices(lines)
        edge_pos = {idx: p for p, idx in enumerate(edge)}
        drop = {i for i in edge if _norm(lines[i]) in boiler}
        for i in edge:
            if i in drop or not _CSI_HEADER.match(lines[i]):
                continue
            p = edge_pos[i]
            neighbors = {edge[p - 1] if p > 0 else None, edge[p + 1] if p + 1 < len(edge) else None}
            if neighbors & drop:
                drop.add(i)
        cleaned.append("\n".join(ln for j, ln in enumerate(lines) if j not in drop))
    return cleaned


if __name__ == "__main__":
    import sys

    text = load_text(sys.argv[1])
    print(f"Extracted {len(text):,} characters.")
    print("---- first 1500 chars ----")
    print(text[:1500])

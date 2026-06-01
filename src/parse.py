"""Stage 1 — Parse: spec PDF -> plain text, structure preserved.

The only job here is to turn one PDF into clean text with page breaks marked, so
the next stage can split it into CSI sections. Eyeball the output before trusting
anything downstream (`python -m src.parse data/spec.pdf`): garbage text here
means a garbage register.
"""
import fitz  # pymupdf

# A visible marker so section-splitting can tell where a printed page ended.
# Plain text, unlikely to collide with spec content.
PAGE_BREAK = "\n\f\n"


def load_text(path: str) -> str:
    """Concatenate every page's text, separated by a page-break marker."""
    doc = fitz.open(path)
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return PAGE_BREAK.join(pages)


if __name__ == "__main__":
    import sys

    text = load_text(sys.argv[1])
    print(f"Extracted {len(text):,} characters.")
    print("---- first 1500 chars ----")
    print(text[:1500])

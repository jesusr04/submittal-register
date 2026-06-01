"""Stage 2 — Identify sections: split the book by CSI MasterFormat numbering.

CSI MasterFormat numbers every spec section as `XX XX XX` (e.g. `03 30 00 —
Cast-in-Place Concrete`). We split the whole-book text on those headers so each
downstream LLM call sees ONE section, not the entire book — that's the main
cost lever in this pipeline.

Two real-world wrinkles handled here:
  1. The same number appears in the Table of Contents AND as the real section.
     We keep, per number, the occurrence with the most body text (the real one).
  2. We only feed the extractor PART 1 — GENERAL (where Submittals at 1.5 and
     Delivery/Storage at 1.6 live), not Parts 2/3, which cuts tokens further.
"""
import re
from dataclasses import dataclass

# A CSI number: two-digit division, then two more two-digit pairs. The lookahead
# keeps us from matching longer digit runs (phone numbers, dimensions).
_NUMBER = r"\d{2}\s\d{2}\s\d{2}(?:\.\d{2})?"
_HEADER_RE = re.compile(rf"(?m)^[ \t]*(?:SECTION\s+)?({_NUMBER})\b[ \t]*[-–—]?[ \t]*(.*)$")


@dataclass
class Section:
    number: str  # normalized "03 30 00"
    title: str  # "Cast-in-Place Concrete"
    text: str  # full body of this section

    @property
    def label(self) -> str:
        """The 'Spec Section' cell, e.g. '03 30 00 — Cast-in-Place Concrete'."""
        return f"{self.number} — {self.title}" if self.title else self.number


def split_sections(text: str) -> list[Section]:
    """Return one Section per CSI number, de-duplicated against the TOC."""
    matches = list(_HEADER_RE.finditer(text))
    found: list[Section] = []
    for i, m in enumerate(matches):
        number = re.sub(r"\s+", " ", m.group(1)).strip()
        title = m.group(2).strip(" .-–—\t")
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        # A title sometimes sits on the next line rather than after the number.
        if not title:
            first_line = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
            if first_line and not _HEADER_RE.match(first_line):
                title = first_line
        found.append(Section(number=number, title=title, text=body))

    # De-dupe: keep the fullest occurrence of each number (real section > TOC line).
    best: dict[str, Section] = {}
    for sec in found:
        if sec.number not in best or len(sec.text) > len(best[sec.number].text):
            best[sec.number] = sec
    # Preserve first-seen order of the kept sections.
    order = list(dict.fromkeys(s.number for s in found))
    return [best[n] for n in order]


def part1(section_text: str) -> str:
    """Just PART 1 — GENERAL, where Submittals (1.5) and Storage (1.6) live.

    Falls back to the whole section if the PART markers aren't found (some specs
    use 'PART 1 GENERAL', 'PART 1 - GENERAL', etc.).
    """
    start = re.search(r"(?im)^\s*PART\s+1\b", section_text)
    if not start:
        return section_text
    end = re.search(r"(?im)^\s*PART\s+2\b", section_text[start.end():])
    if end:
        return section_text[start.start(): start.end() + end.start()]
    return section_text[start.start():]


if __name__ == "__main__":
    import sys

    from src.parse import load_text

    secs = split_sections(load_text(sys.argv[1]))
    print(f"Found {len(secs)} sections:")
    for s in secs:
        print(f"  {s.label}  ({len(s.text):,} chars)")

"""Wire the six stages into one callable, with a content-keyed cache.

    parse -> split sections -> extract items -> classify -> priority -> Excel

LLM calls cost money, so the per-section extract+classify results are cached to
.cache/, keyed by a fingerprint of (PDF bytes + both model names + the lead-time
table). Change the PDF, swap a model, or edit lead_times.py and the cache
rebuilds itself — no stale registers, no need to remember to clear anything.
"""
import hashlib
import json
import os

from config import CACHE_DIR, CLASSIFY_MODEL, EXTRACT_MODEL
from src import lead_times
from src.classify import classify_items
from src.excel import Row, write_register
from src.extract import extract_items
from src.lead_times import cell_text
from src.parse import load_text
from src.priority import priority_flag
from src.sections import Section, part1, split_sections


def _fingerprint(pdf_path: str) -> str:
    """Stable id for 'this PDF + these models + this lead-time table'."""
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        h.update(f.read())
    table = json.dumps(lead_times.LEAD_TIME_TABLE, sort_keys=True)
    h.update(f"{EXTRACT_MODEL}:{CLASSIFY_MODEL}:{table}".encode())
    return h.hexdigest()


def _rows_from_section(sec: Section) -> list[Row]:
    """The two LLM calls for one section, turned into register rows."""
    items = extract_items(sec.label, part1(sec.text))
    if not items:
        return []
    categories = classify_items([it.item for it in items])
    rows = []
    for it, category in zip(items, categories):
        rows.append(
            Row(
                spec_section=sec.label,
                item=it.item,
                submittal_required=it.submittal_required,
                lead_time_category=cell_text(category),
                priority=priority_flag(category, it.storage_sensitive),
            )
        )
    return rows


def build_register(
    pdf_path: str,
    out_path: str,
    *,
    max_sections: int | None = None,
    use_cache: bool = True,
    on_section=None,
) -> list[Row]:
    """Run the full pipeline and write the .xlsx. Returns the rows written.

    `max_sections` caps how many sections are processed — use it for a cheap
    smoke test before paying to run the whole book. `on_section(i, total, sec)`
    is an optional progress callback.
    """
    sections = split_sections(load_text(pdf_path))
    if max_sections is not None:
        sections = sections[:max_sections]

    cache_path = os.path.join(CACHE_DIR, f"{_fingerprint(pdf_path)}.json")
    cached: dict[str, list[dict]] = {}
    # Cache only covers full runs — a capped run shouldn't poison the full cache.
    if use_cache and max_sections is None and os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cached = json.load(f)

    all_rows: list[Row] = []
    fresh: dict[str, list[dict]] = {}
    for i, sec in enumerate(sections, start=1):
        if on_section:
            on_section(i, len(sections), sec)
        if sec.number in cached:
            rows = [Row(**d) for d in cached[sec.number]]
        else:
            rows = _rows_from_section(sec)
        fresh[sec.number] = [r.__dict__ for r in rows]
        all_rows.extend(rows)

    if use_cache and max_sections is None:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(fresh, f, indent=2)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    write_register(all_rows, out_path)
    return all_rows

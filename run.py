"""CLI — turn a spec PDF into a submittal register.

    python run.py data/spec.pdf                    # full book -> output/<name>.xlsx
    python run.py data/spec.pdf -o register.xlsx   # choose the output path
    python run.py data/spec.pdf --max-sections 3   # cheap smoke test (3 sections)
    python run.py data/spec.pdf --list-sections    # parse only, NO API calls

`--list-sections` is the free first step: confirm the PDF split into sensible CSI
sections before you spend a cent on extraction.
"""
import argparse
import os
import sys


def main() -> int:
    p = argparse.ArgumentParser(description="Generate a submittal register from a spec PDF.")
    p.add_argument("pdf", help="Path to the construction spec PDF.")
    p.add_argument("-o", "--output", help="Output .xlsx path (default: output/<pdf name>.xlsx).")
    p.add_argument("--max-sections", type=int, help="Process only the first N sections (cost control).")
    p.add_argument("--list-sections", action="store_true", help="Print detected sections and exit (no API calls).")
    p.add_argument("--no-cache", action="store_true", help="Ignore and overwrite the .cache for this PDF.")
    args = p.parse_args()

    if not os.path.exists(args.pdf):
        print(f"File not found: {args.pdf}", file=sys.stderr)
        return 1

    # Import after arg parsing so --help and --list-sections don't require a key.
    from src.parse import load_text
    from src.sections import split_sections

    if args.list_sections:
        sections = split_sections(load_text(args.pdf))
        print(f"Detected {len(sections)} CSI sections:\n")
        for s in sections:
            print(f"  {s.label}  ({len(s.text):,} chars)")
        return 0

    out = args.output or os.path.join("output", os.path.splitext(os.path.basename(args.pdf))[0] + ".xlsx")

    from src.pipeline import build_register

    def progress(i: int, total: int, sec) -> None:
        print(f"  [{i}/{total}] {sec.label}", flush=True)

    print(f"Building register from {args.pdf} ...")
    rows = build_register(
        args.pdf,
        out,
        max_sections=args.max_sections,
        use_cache=not args.no_cache,
        on_section=progress,
    )
    urgent = sum(1 for r in rows if r.priority == "Urgent")
    print(f"\nDone. {len(rows)} submittal items ({urgent} Urgent) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

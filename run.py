"""CLI — turn a spec PDF into a submittal register.

    python run.py data/spec.pdf                    # full book -> output/<name>.xlsx
    python run.py data/spec.pdf -o register.xlsx   # choose the output path
    python run.py data/spec.pdf --max-sections 3   # cheap smoke test (3 sections)
    python run.py data/spec.pdf --only 03 30 00    # just one section / division (cheap test)
    python run.py data/spec.pdf --list-sections    # parse only, NO API calls

`--list-sections` is the free first step: confirm the PDF split into sensible CSI
sections before you spend a cent on extraction. `--only` targets a specific CSI
number (or a division prefix like `03`) so you can test real extraction cheaply.
"""
import argparse
import os
import sys


def main() -> int:
    # CSI section labels use an em-dash; force UTF-8 so a Windows console (default
    # code page) prints it cleanly instead of mojibake.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    p = argparse.ArgumentParser(description="Generate a submittal register from a spec PDF.")
    p.add_argument("pdf", help="Path to the construction spec PDF.")
    p.add_argument("-o", "--output", help="Output .xlsx path (default: output/<pdf name>.xlsx).")
    p.add_argument("--max-sections", type=int, help="Process only the first N sections (cost control).")
    p.add_argument(
        "--only",
        nargs="+",
        metavar="CSI",
        help='Run only the section(s) matching this CSI number or division prefix '
        '(e.g. --only 03 30 00, or --only 03 for all of Division 03). Cost control for testing.',
    )
    p.add_argument("--list-sections", action="store_true", help="Print detected sections and exit (no API calls).")
    p.add_argument("--no-cache", action="store_true", help="Ignore and overwrite the .cache for this PDF.")
    args = p.parse_args()

    if not os.path.exists(args.pdf):
        print(f"File not found: {args.pdf}", file=sys.stderr)
        return 1

    # Import after arg parsing so --help and --list-sections don't require a key.
    from src.parse import load_text
    from src.sections import is_spec_section, split_sections

    if args.list_sections:
        detected = split_sections(load_text(args.pdf))
        sections = [s for s in detected if is_spec_section(s)]
        skipped = len(detected) - len(sections)
        print(
            f"Detected {len(sections)} CSI sections "
            f"({skipped} skipped — no body, or a non-MasterFormat division):\n"
        )
        for s in sections:
            print(f"  {s.label}  ({len(s.text):,} chars)")
        return 0

    out = args.output or os.path.join("output", os.path.splitext(os.path.basename(args.pdf))[0] + ".xlsx")

    from src.pipeline import build_register

    def progress(i: int, total: int, sec) -> None:
        print(f"  [{i}/{total}] {sec.label}", flush=True)

    # Join tokens and drop spaces so '--only 03 30 00', '--only "03 30 00"', and
    # '--only 033000' all mean the same thing; a short prefix like '03' selects a division.
    only = "".join(args.only).replace(" ", "") if args.only else None

    print(f"Building register from {args.pdf} ...")
    rows = build_register(
        args.pdf,
        out,
        max_sections=args.max_sections,
        only=only,
        use_cache=not args.no_cache,
        on_section=progress,
    )
    urgent = sum(1 for r in rows if r.priority == "Urgent")
    print(f"\nDone. {len(rows)} submittal items ({urgent} Urgent) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

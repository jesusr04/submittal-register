# Submittal Register Generator

Turn a construction **spec book PDF** into a **submittal register** (`.xlsx`) —
every product that requires a submittal, with a lead-time category and an
Urgent/Standard priority flag — in minutes instead of the 1–3 days a project
engineer normally spends building it by hand at the start of every job.

> **Why this exists.** The submittal register is a deliverable every PM already
> knows and every PE dreads. The competing process is a person reading the spec
> cover to cover. A working draft that gets you 80% of the way there, that you
> then verify, answers "would anyone use this?" instantly — because they already
> use the manual version.

---

## What it does

Input: **one** construction spec PDF.
Output: an `.xlsx` with five columns —

| Column | Where it comes from |
|---|---|
| **Spec Section** | CSI MasterFormat number + title (e.g. `03 30 00 — Cast-in-Place Concrete`) |
| **Item** | The product/material requiring a submittal |
| **Submittal Required** | What's due — product data, shop drawings, samples, certs… (from the Submittals article, ~1.5) |
| **Lead Time Category** | `Stock` / `Short (4-8 wk)` / `Medium (10-16 wk)` / `Long (20-30 wk)` / `Extra-Long (30+ wk)`, or `Plan` for prep/plan-based submittals (a curing method, a weather plan) |
| **Priority Flag** | Driven by lead time: `Stock`→`Low`, `Plan`/`Short`→`Medium`, `Medium`→`High`, `Long`/`Extra-Long`→`Urgent` |

Urgent and High rows are tinted so the schedule risks jump out.

## How it works

Six stages, one section at a time:

```
1. parse      PDF  -> text                      (PyMuPDF)
2. sections   text -> CSI sections (XX XX XX)    (regex split + TOC de-dup)
3. extract    PART 1 -> submittal items (JSON)   (Claude, strong model)
4. classify   item  -> material category         (Claude, cheap model)
              category -> lead-time bucket        (your lookup table)
5. priority   lead-time bucket -> Low/Medium/High/Urgent (rule)
6. excel      rows  -> .xlsx                      (openpyxl)
```

**Cost is designed in, not bolted on:**
- The book is split into sections first, so the LLM never sees the whole thing at once.
- Extraction (the hard read) and classification (pick-from-a-list) run on **different
  models** — `EXTRACT_MODEL` (Sonnet) and `CLASSIFY_MODEL` (Haiku).
- Lead-time numbers live in [`src/lead_times.py`](src/lead_times.py), not in the
  prompt — the model only ever picks a category; **you** own the weeks.
- Results are cached per PDF in `.cache/`, keyed by PDF bytes + models + the
  lookup table, so re-runs and tweaks don't re-pay for unchanged sections.

## Quickstart

```bash
python -m venv .venv && .venv\Scripts\activate    # Windows (PowerShell)
pip install -r requirements.txt
copy .env.example .env                             # then paste your ANTHROPIC_API_KEY

# 1) Free sanity check — does the PDF split into sensible CSI sections? (no API calls)
python run.py data/spec.pdf --list-sections

# 2) Cheap smoke test — first 3 sections only
python run.py data/spec.pdf --max-sections 3

# 3) Full run
python run.py data/spec.pdf -o output/register.xlsx
```

Run the offline tests (no key needed) — they cover section splitting, the
lead-time table, the priority rule, and the Excel writer:

```bash
python -m pytest          # or: python -m unittest discover -s tests
```

## v1 scope (deliberately narrow)

**In:** one real spec book, CLI + Excel out, the five columns above, hand-verifiable
to ~80% by someone who's built these registers.

**Out (on purpose):** multiple spec formats at once, a web UI, schedule /
critical-path integration, live manufacturer lead-time feeds, a standalone storage
column (it lives inside the priority rule), and closeout artifacts
(warranties, mockups, O&M).

## Roadmap

- **v2** — explicit Storage Constraint column from Part 1.6
- **v3** — schedule integration: order window vs install date, urgency against the real schedule
- **v4** — live lead-time data: manufacturer feeds + your firm's own project history
- **v5** — full submittal tracking: status, ball-in-court, closeout register

## A note on accuracy

This produces a **first draft a PE verifies**, not a system of record. It reads
only what the spec says and is told never to invent items. You're the validator —
the win is turning a 1–3 day cold start into a 30-minute review.

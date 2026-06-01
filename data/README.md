# data/

Drop the spec PDF you want to process here, e.g. `data/spec.pdf`, then run:

```bash
python run.py data/spec.pdf --list-sections   # free: confirm the split looks right
python run.py data/spec.pdf                    # full run -> output/spec.xlsx
```

PDFs in this folder are **gitignored** (`data/*.pdf`) — client spec books and any
generated `.xlsx` never get committed. Keep the real PKA spec local.

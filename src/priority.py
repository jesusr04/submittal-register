"""Stage 5 — Assign priority: the one derived column.

Priority is a pure function of the lead-time category, so identical inputs always
produce the same flag (a demo must reproduce). The longer the procurement lead
time, the higher the schedule risk if you don't order early — so Long/Extra-Long
items are Urgent. Prep/plan-based submittals carry no procurement lead time but
still gate work, so they sit at Medium.

The week numbers behind each bucket live in `lead_times.py`; this file owns only
the bucket -> level mapping. Edit it if your firm weighs the levels differently.
"""
from src.lead_times import PLAN_LABEL

# Lead-time bucket label (or the 'Plan' pseudo-bucket) -> priority level.
_PRIORITY_BY_BUCKET = {
    "Stock": "Low",
    PLAN_LABEL: "Medium",
    "Short": "Medium",
    "Medium": "High",
    "Long": "Urgent",
    "Extra-Long": "Urgent",
}

PRIORITY_LEVELS = ("Low", "Medium", "High", "Urgent")


def priority_flag(bucket: str) -> str:
    """Map a lead-time bucket label (or 'Plan') to a priority level.

    Unknown buckets fall back to High so they surface for human review.
    """
    return _PRIORITY_BY_BUCKET.get(bucket, "High")

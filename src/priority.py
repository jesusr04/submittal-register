"""Stage 5 — Assign priority: the one derived column.

Rule from the build spec: an item is URGENT if it is long-lead OR storage-
sensitive; otherwise STANDARD. 'Long-lead' means it lands in the Long or
Extra-Long bucket — those are the items that, if you don't order them in the
first weeks of a project, will sit on your critical path. Storage-sensitive items
are urgent for a different reason: even if the lead time is short, you must plan
where they go the moment they arrive.
"""
from src.lead_times import bucket_for

# The buckets that count as "long lead" for the Urgent rule. Edit if your firm
# treats Medium as urgent too.
LONG_LEAD_BUCKETS = {"Long", "Extra-Long"}


def priority_flag(category: str, storage_sensitive: bool) -> str:
    """'Urgent' or 'Standard' for one item."""
    bucket = bucket_for(category)[0]
    if bucket in LONG_LEAD_BUCKETS or storage_sensitive:
        return "Urgent"
    return "Standard"

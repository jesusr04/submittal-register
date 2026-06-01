"""Central config — models, paths, and the two cost-control knobs.

The pipeline runs Claude twice per spec section: once to EXTRACT submittal items
(needs a capable model) and once to CLASSIFY each item into a lead-time bucket
(a constrained pick-from-a-list task that a cheap model does well). Splitting the
work across two models — and processing one section at a time — is the whole
cost story: you never send the entire spec book in a single giant call.
"""
import os

from dotenv import load_dotenv

load_dotenv()

# Extraction reads messy spec prose and pulls structured items — use the stronger
# model. Classification only maps a known item to one of a fixed list of material
# categories, so Haiku is plenty and ~10x cheaper.
EXTRACT_MODEL = os.getenv("EXTRACT_MODEL", "claude-sonnet-4-6")
CLASSIFY_MODEL = os.getenv("CLASSIFY_MODEL", "claude-haiku-4-5-20251001")

CACHE_DIR = ".cache"

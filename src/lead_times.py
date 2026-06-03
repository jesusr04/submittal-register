"""The lead-time lookup table — your field knowledge, in code.

Stage 4 has the LLM map each item to ONE material `category` key below; this
table maps that category to a bucket and a week range. Keeping the numbers here
(not in the prompt) means YOU are the dictator of truth: refine these from your
own project history and the model's judgment never overrides them.

Buckets follow the build spec:
    Stock | Short (4-8 wk) | Medium (10-16 wk) | Long (20-30 wk) | Extra-Long (30+ wk)

These are conservative starting numbers. Edit freely as you validate.
"""

# category key -> (bucket label, low_weeks, high_weeks)
LEAD_TIME_TABLE: dict[str, tuple[str, int, int]] = {
    # --- Stock: commodity, on the shelf or a short truck ride away ---
    "concrete_rebar_aggregate": ("Stock", 0, 2),
    "rough_carpentry_lumber": ("Stock", 0, 2),
    "fasteners_accessories": ("Stock", 0, 2),
    "curing_compound": ("Stock", 0, 2),
    "insulation": ("Stock", 1, 3),
    # Electrical commodity — stocked at any supply house. (PE: tune these.)
    "electrical_devices": ("Stock", 1, 3),  # receptacles, switches, plates, fuses
    "conduit_raceway_boxes": ("Stock", 1, 3),  # conduit, raceway, boxes, supports, grounding, ID
    # HVAC commodity — accessories carried/quick. (PE: tune these.)
    "hvac_accessories": ("Stock", 1, 3),  # access doors, vibration isolators, hangers, grilles/diffusers/registers
    # --- Short (4-8 wk) ---
    "gypsum_drywall": ("Short", 4, 8),
    "paint_coatings": ("Short", 4, 8),
    "doors_frames_hardware": ("Short", 6, 8),
    "plumbing_fixtures": ("Short", 4, 8),
    "basic_lighting": ("Short", 6, 8),
    "wire_cable": ("Short", 4, 8),  # building wire / branch-circuit conductors
    "electrical_controls_metering": ("Short", 6, 10),  # lighting controls, contactors, sensors, meters, SPDs
    "hvac_ductwork": ("Short", 4, 8),  # ducts, dampers, louvers, flues, duct lining, sealant, insulation
    "hvac_piping": ("Short", 4, 8),  # HVAC/refrigerant piping, fittings, valves
    # --- Medium (10-16 wk) ---
    "structural_steel": ("Medium", 10, 16),
    "metal_deck_joists": ("Medium", 10, 14),
    "roofing_membrane": ("Medium", 10, 16),
    "millwork_casework": ("Medium", 12, 16),
    "fire_sprinkler": ("Medium", 10, 14),
    "enclosed_switches_breakers": ("Medium", 10, 16),  # enclosed breakers/switches, motor controllers
    "hvac_terminal_units": ("Medium", 12, 18),  # fans, fan coil units, unit heaters, pumps (smaller/quicker gear)
    # --- Long (20-30 wk) ---
    "panelboards": ("Long", 20, 28),
    "storefront_glazing": ("Long", 20, 28),
    "curtain_wall": ("Long", 24, 30),
    "elevators_escalators": ("Long", 22, 30),
    "hvac_packaged_equipment": ("Long", 20, 30),  # packaged DX/RTU/AHU, heat pumps, condensing units, ERVs
    "overhead_coiling_doors": ("Long", 20, 26),
    # --- Extra-Long (30+ wk): the schedule killers ---
    "electrical_switchgear": ("Extra-Long", 30, 52),
    "generators": ("Extra-Long", 30, 50),
    "chillers_cooling_towers": ("Extra-Long", 30, 45),
    "transformers": ("Extra-Long", 40, 60),
    "custom_long_lead_equipment": ("Extra-Long", 30, 52),
    # --- Fallback: when the model can't confidently place an item ---
    "unknown": ("Medium", 10, 16),  # conservative — surfaces for human review
}

# The valid choices the classifier is allowed to return.
CATEGORIES = list(LEAD_TIME_TABLE.keys())

# Prep/plan-based submittals (a curing method, a hot/cold-weather plan) carry no
# procurement lead time, so they bypass the table above and show as "Plan" in the
# Lead Time Category column. The extractor flags these; see priority.py for level.
PLAN_LABEL = "Plan"


def bucket_for(category: str) -> tuple[str, int, int]:
    """(label, low_wk, high_wk) for a category; falls back to 'unknown'."""
    return LEAD_TIME_TABLE.get(category, LEAD_TIME_TABLE["unknown"])


def cell_text(category: str) -> str:
    """The 'Lead Time Category' cell, e.g. 'Long (20-30 wk)' or 'Stock'."""
    label, low, high = bucket_for(category)
    if label == "Stock":
        return "Stock"
    return f"{label} ({low}-{high} wk)"

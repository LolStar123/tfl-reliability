"""
TfL Fare Data 2025/2026 — London Commute Cost Optimizer
========================================================

All fares effective from 1 March 2026 (frozen caps/travelcards from March 2025).
Bus/tram fares frozen until 5 July 2026. Caps frozen until March 2027.

Sources:
  - https://content.tfl.gov.uk/adult-fares.pdf
  - https://www.london.gov.uk/md3464-march-2026-transport-london-fare-changes
  - https://tfl.gov.uk/fares/find-fares/caps-and-travelcard-prices
  - https://oysterfares.com/information-pages/daily-caps-and-travelcards-2025/
  - https://tfl.gov.uk/fares/free-and-discounted-travel/national-railcard-discount
  - https://content.tfl.gov.uk/railcard-fares.pdf
"""

# =============================================================================
# 1. PEAK / OFF-PEAK DEFINITIONS
# =============================================================================

PEAK_HOURS = {
    "morning": {"start": "06:30", "end": "09:30"},
    "evening": {"start": "16:00", "end": "19:00"},
    "days": "Monday-Friday (excluding public holidays)",
    "notes": [
        "Peak fares based on touch-in time, not boarding time.",
        "Journeys FROM outside Zone 1 INTO Zone 1 during evening peak (16:00-19:00) are charged at off-peak rate.",
        "Weekends and public holidays are always off-peak.",
        "Night Tube services are always off-peak.",
    ],
}

# =============================================================================
# 2. BUS & TRAM FARES (flat fare, no zones)
# =============================================================================

BUS_TRAM = {
    "single_fare": 1.75,
    "daily_cap": 5.25,       # equals 3x single fares
    "weekly_cap": 24.70,     # Mon-Sun
    "one_day_pass": 6.00,    # paper ticket
    "hopper_fare": {
        "cost": 0.00,        # free transfer
        "window_minutes": 60,
        "max_transfers": None,  # unlimited within the hour
        "rules": [
            "Pay £1.75 for first bus/tram, then unlimited free transfers within 1 hour.",
            "Must touch in on every boarding (even free ones).",
            "Only applies to bus-to-bus or bus-to-tram or tram-to-bus transfers.",
            "Does NOT apply to Tube/DLR/Overground/Elizabeth line.",
            "The 1-hour window starts from first touch-in.",
        ],
    },
    "notes": [
        "Bus/tram fares frozen until 5 July 2026.",
        "No railcard discount on bus/tram single fares.",
        "Bus daily cap is separate from Tube/rail daily cap.",
        "If you mix bus + Tube in one day, you pay towards the Tube/rail daily cap (which is higher).",
    ],
}

# =============================================================================
# 3. TUBE / DLR / OVERGROUND / ELIZABETH LINE — SINGLE FARES (PAYG)
# =============================================================================

# Adult pay-as-you-go single fares (Oyster or contactless)
# Format: {zone_range: {"peak": price, "off_peak": price}}

SINGLE_FARES_INCLUDING_ZONE_1 = {
    "1":   {"peak": 3.10, "off_peak": 3.00},
    "1-2": {"peak": 3.60, "off_peak": 3.10},
    "1-3": {"peak": 3.90, "off_peak": 3.30},
    "1-4": {"peak": 4.80, "off_peak": 3.60},
    "1-5": {"peak": 5.30, "off_peak": 3.80},
    "1-6": {"peak": 5.90, "off_peak": 4.00},
}

SINGLE_FARES_EXCLUDING_ZONE_1 = {
    "2":   {"peak": 2.30, "off_peak": 2.20},
    "2-3": {"peak": 2.50, "off_peak": 2.30},
    "2-4": {"peak": 3.20, "off_peak": 2.40},
    "2-5": {"peak": 3.40, "off_peak": 2.50},
    "2-6": {"peak": 3.80, "off_peak": 2.60},
    "3":   {"peak": 2.30, "off_peak": 2.20},
    "3-4": {"peak": 2.50, "off_peak": 2.30},
    "3-5": {"peak": 3.20, "off_peak": 2.40},
    "3-6": {"peak": 3.40, "off_peak": 2.50},
    "4":   {"peak": 2.10, "off_peak": 2.20},
    "4-5": {"peak": 2.30, "off_peak": 2.30},
    "4-6": {"peak": 3.20, "off_peak": 2.40},
    "5":   {"peak": 2.30, "off_peak": 2.20},
    "5-6": {"peak": 2.50, "off_peak": 2.30},
    "6":   {"peak": 2.30, "off_peak": 2.20},
}

CASH_SINGLE_FARE = 7.00  # Any zone, avoid this at all costs

# =============================================================================
# 4. DAILY CAPS (PAYG — Oyster & Contactless)
# =============================================================================

# Daily caps are the same for peak (anytime) and off-peak for zones 1-6.
# They diverge only for zones 1-7 and beyond.
# Cap period: 04:30 to 04:29 next day.

DAILY_CAPS_INCLUDING_ZONE_1 = {
    "1":   {"anytime": 8.90, "off_peak": 8.90},
    "1-2": {"anytime": 8.90, "off_peak": 8.90},
    "1-3": {"anytime": 10.50, "off_peak": 10.50},
    "1-4": {"anytime": 12.80, "off_peak": 12.80},
    "1-5": {"anytime": 15.30, "off_peak": 15.30},
    "1-6": {"anytime": 16.30, "off_peak": 16.30},
    "1-7": {"anytime": 17.80, "off_peak": 16.30},
    "1-8": {"anytime": 21.00, "off_peak": 16.30},
    "1-9": {"anytime": 23.30, "off_peak": 16.30},
}

# Excluding zone 1 — daily caps are lower
# Note: These are derived from the weekly travelcard / 7 equivalence.
# The daily cap equals the 7-day travelcard price / 5 (rounded).
DAILY_CAPS_EXCLUDING_ZONE_1 = {
    "2":   {"anytime": 8.90, "off_peak": 8.90},   # same as zone 1-2
    "2-3": {"anytime": 8.90, "off_peak": 8.90},
    "2-4": {"anytime": 10.50, "off_peak": 10.50},
    "2-5": {"anytime": 12.80, "off_peak": 12.80},
    "2-6": {"anytime": 15.30, "off_peak": 15.30},
}

# =============================================================================
# 5. WEEKLY CAPS (PAYG — Monday 04:30 to Monday 04:29)
# =============================================================================

# Weekly caps equal the 7-day Travelcard price for that zone combination.
# Only available on contactless (NOT Oyster — Oyster has no rail weekly cap).

WEEKLY_CAPS_INCLUDING_ZONE_1 = {
    "1":   44.70,
    "1-2": 44.70,
    "1-3": 52.50,
    "1-4": 64.20,
    "1-5": 76.40,
    "1-6": 81.60,
    "1-7": 88.90,
    "1-8": 104.90,
    "1-9": 116.40,
}

WEEKLY_CAPS_EXCLUDING_ZONE_1 = {
    "2":   33.50,
    "2-3": 37.10,
    "2-4": 44.50,
    "2-5": 55.90,
    # 2-6 not listed officially; would be capped at zone 1-6 cap
}

# Bus-only weekly cap
BUS_WEEKLY_CAP = 24.70

# =============================================================================
# 6. TRAVELCARD SEASON TICKETS
# =============================================================================

TRAVELCARDS = {
    # Including Zone 1
    "1":   {"weekly": 44.70, "monthly": 171.70, "annual": 1788.00},
    "1-2": {"weekly": 44.70, "monthly": 171.70, "annual": 1788.00},
    "1-3": {"weekly": 52.50, "monthly": 201.60, "annual": 2100.00},
    "1-4": {"weekly": 64.20, "monthly": 246.60, "annual": 2568.00},
    "1-5": {"weekly": 76.40, "monthly": 293.40, "annual": 3056.00},
    "1-6": {"weekly": 81.60, "monthly": 313.40, "annual": 3264.00},
    "1-7": {"weekly": 88.90, "monthly": 341.40, "annual": 3556.00},
    "1-8": {"weekly": 104.90, "monthly": 402.90, "annual": 4196.00},
    "1-9": {"weekly": 116.40, "monthly": 447.00, "annual": 4656.00},
    # Excluding Zone 1
    "2":   {"weekly": 33.50, "monthly": 128.70, "annual": 1340.00},
    "2-3": {"weekly": 37.10, "monthly": 142.50, "annual": 1484.00},
    "2-4": {"weekly": 44.50, "monthly": 170.90, "annual": 1780.00},
    "2-5": {"weekly": 55.90, "monthly": 214.70, "annual": 2236.00},
}

TRAVELCARD_NOTES = [
    "Annual travelcard = ~10.5 months' price (saves ~1.5 months vs monthly).",
    "Monthly = weekly price × 4.348 (standard calendar conversion).",
    "Zone 1 and zone 1-2 travelcards are the same price.",
    "Travelcards are frozen until March 2027.",
    "Travelcard covers Tube, DLR, Overground, Elizabeth line, and most National Rail in zones.",
    "Travelcard holders also get free bus/tram travel within their zones.",
]

# Day Travelcards (paper tickets, rarely best value)
DAY_TRAVELCARDS = {
    "anytime_1-4": 16.60,
    "anytime_1-6": 23.60,
    "anytime_1-9": 29.80,
    "off_peak_1-6": 16.60,
}

# =============================================================================
# 7. RAILCARD DISCOUNTS
# =============================================================================

RAILCARDS = {
    "16-25": {
        "name": "16-25 Railcard",
        "annual_cost": 35.00,
        "three_year_cost": 80.00,
        "discount": "1/3 off",
        "applies_to": "off-peak PAYG fares and off-peak daily caps only",
        "oyster_only": True,  # must be linked to Oyster, NOT contactless
    },
    "26-30": {
        "name": "26-30 Railcard",
        "annual_cost": 35.00,
        "three_year_cost": None,  # 1-year only
        "discount": "1/3 off",
        "applies_to": "off-peak PAYG fares and off-peak daily caps only",
        "oyster_only": True,
    },
    "senior": {
        "name": "Senior Railcard",
        "annual_cost": 35.00,
        "three_year_cost": 80.00,
        "discount": "1/3 off",
        "applies_to": "off-peak PAYG fares and off-peak daily caps only",
        "oyster_only": True,
    },
    "hm_forces": {
        "name": "HM Forces Railcard",
        "annual_cost": 35.00,
        "three_year_cost": None,
        "discount": "1/3 off",
        "applies_to": "off-peak PAYG fares and off-peak daily caps only",
        "oyster_only": True,
    },
    "veterans": {
        "name": "Veterans Railcard",
        "annual_cost": 35.00,
        "three_year_cost": 80.00,
        "discount": "1/3 off",
        "applies_to": "off-peak PAYG fares and off-peak daily caps only",
        "oyster_only": True,
    },
    "disabled": {
        "name": "Disabled Persons Railcard",
        "annual_cost": 35.00,
        "three_year_cost": None,
        "discount": "1/3 off",
        "applies_to": "ALL fares (peak AND off-peak) — unique among railcards",
        "oyster_only": True,
        "companion_discount": True,  # companion also gets 1/3 off
    },
    "two_together": {
        "name": "Two Together Railcard",
        "annual_cost": 35.00,
        "three_year_cost": None,
        "discount": "1/3 off",
        "applies_to": "off-peak National Rail fares only",
        "oyster_only": False,  # cannot be linked to Oyster
        "tfl_integration": "Can only buy discounted Off-Peak Day Travelcards at station",
        "notes": "Both named passengers must travel together. No Oyster/contactless integration.",
    },
    "network": {
        "name": "Network Railcard",
        "annual_cost": 35.00,
        "three_year_cost": None,
        "discount": "1/3 off",
        "applies_to": "off-peak National Rail fares in Network Railcard area",
        "oyster_only": False,
        "tfl_integration": "Can only buy discounted Off-Peak Day Travelcards at station",
    },
    "family_friends": {
        "name": "Family & Friends Railcard",
        "annual_cost": 35.00,
        "three_year_cost": 80.00,
        "discount": "1/3 off adults, 60% off children",
        "applies_to": "off-peak National Rail fares",
        "oyster_only": False,
        "tfl_integration": "Can only buy discounted Off-Peak Day Travelcards at station",
    },
}

RAILCARD_RULES = [
    "Railcard discount on TfL only works via Oyster — NOT contactless (as of April 2026).",
    "TfL is exploring linking railcards to contactless in future but no date confirmed.",
    "Must carry physical railcard when travelling.",
    "Discount applies to Tube, DLR, Overground, Elizabeth line, and National Rail PAYG.",
    "No discount on bus/tram single fares.",
    "Off-peak = all day weekends/holidays, plus weekday off-peak windows.",
    "Evening peak (16:00-19:00) INTO Zone 1 is charged off-peak = railcard discount applies.",
    "Railcard discounts apply to off-peak daily cap, reducing it by ~1/3.",
    "Oyster does NOT have weekly rail capping (only contactless does).",
    "So railcard holders on Oyster get discounted daily caps but no weekly cap benefit.",
]

# Railcard-discounted off-peak daily caps (1/3 off the standard off-peak cap)
RAILCARD_DAILY_CAPS_OFF_PEAK = {
    "1":   5.90,
    "1-2": 5.90,
    "1-3": 6.95,
    "1-4": 8.50,
    "1-5": 10.15,
    "1-6": 10.85,
    "1-7": 10.85,
    "1-8": 10.85,
    "1-9": 10.85,
}

# Railcard-discounted single fares (1/3 off off-peak fare, rounded to nearest 10p)
# These are computed: round(off_peak * 2/3, 1)
RAILCARD_SINGLE_FARES_OFF_PEAK = {
    "1":   2.00,
    "1-2": 2.05,
    "1-3": 2.20,
    "1-4": 2.40,
    "1-5": 2.55,
    "1-6": 2.65,
}

# =============================================================================
# 8. CAPPING RULES
# =============================================================================

CAPPING_RULES = {
    "daily_cap": {
        "period": "04:30 to 04:29 next day",
        "applies_to": ["contactless", "oyster"],
        "how_it_works": [
            "You pay single fare for each journey.",
            "Once total fares hit the daily cap, remaining journeys that day are free.",
            "Cap is based on highest zone touched during the day.",
            "If you travel zones 1-3 in morning and zones 1-6 in evening, you pay the 1-6 cap.",
            "Bus/tram has its own separate daily cap (£5.25).",
            "If you use bus AND rail, only the rail cap applies (bus spending counts toward it).",
        ],
    },
    "weekly_cap": {
        "period": "Monday 04:30 to Monday 04:29",
        "applies_to": ["contactless"],  # NOT Oyster
        "how_it_works": [
            "Only works with contactless payment (same card/device all week).",
            "Oyster does NOT have weekly rail capping.",
            "Weekly cap = 7-day Travelcard price for that zone combination.",
            "Cap is based on highest zone reached during the week.",
            "Bus-only weekly cap is £24.70.",
            "Must use same contactless card/device for all journeys in the week.",
        ],
    },
    "oyster_vs_contactless": {
        "same_single_fares": True,
        "same_daily_caps": True,
        "same_weekly_caps": False,  # Oyster has NO rail weekly cap
        "key_difference": "Contactless has weekly capping; Oyster does not (for rail).",
        "oyster_advantage": "Can link railcard for 1/3 off off-peak fares.",
        "contactless_advantage": "Weekly capping (Mon-Sun) automatically applied.",
        "recommendation": [
            "If you have a railcard and travel off-peak: Oyster is better.",
            "If you travel 5+ days/week at peak: Contactless is better (weekly cap).",
            "If you travel occasionally: Either is fine, same daily caps.",
        ],
    },
}

# =============================================================================
# 9. INCOMPLETE JOURNEY CHARGES
# =============================================================================

INCOMPLETE_JOURNEY = {
    "maximum_fare_zones_1_9": 9.40,
    "maximum_fare_beyond_zone_9": 26.00,  # includes Heathrow Express
    "national_rail_maximum": 29.00,
    "rules": [
        "If you fail to touch in OR touch out, you are charged the maximum fare.",
        "If journey time exceeds maximum allowed, you are charged TWO maximum fares.",
        "Neither incomplete journey charge counts toward your daily cap.",
        "You can claim refunds online (up to 8 weeks back for contactless, 8 weeks for Oyster).",
        "Contactless journey history viewable for 12 months.",
        "Auto-refunds may apply if the network caused the issue (e.g., severe delays).",
    ],
    "maximum_journey_times": {
        "zone_1_only": 78,        # minutes
        "zones_1_2": 90,
        "zones_1_3": 105,
        "zones_1_4": 120,
        "zones_1_5": 130,
        "zones_1_6": 140,
        "note": "Approximate. Exceeding these triggers double maximum fare.",
    },
}

# =============================================================================
# 10. BOUNDARY / SPECIAL RULES
# =============================================================================

ZONE_BOUNDARY_RULES = {
    "boundary_stations": [
        "Some stations sit on zone boundaries (e.g., zone 2/3).",
        "You are charged for the cheaper zone combination.",
        "Example: If you are in zone 1 and travel to a zone 2/3 boundary station, you pay zone 1-2.",
    ],
    "avoiding_zone_1": [
        "If your route CAN avoid Zone 1, you can get a cheaper fare.",
        "You MUST touch a pink card reader at the interchange station to prove you avoided Zone 1.",
        "If you don't touch the pink reader, the system assumes you went through Zone 1.",
        "Pink readers are at stations like Canada Water, Whitechapel, Highbury & Islington, etc.",
    ],
    "heathrow_zone_6": [
        "Heathrow is in Zone 6.",
        "Peak fare is ALWAYS charged for journeys to/from Heathrow (even off-peak hours).",
        "Heathrow Express is NOT covered by Oyster/contactless PAYG.",
    ],
}

# =============================================================================
# 11. OYSTER CARD DETAILS
# =============================================================================

OYSTER_CARD = {
    "deposit": 10.00,  # non-refundable as of 2026
    "max_balance": 90.00,
    "minimum_fare_deduction": True,
    "auto_top_up_available": True,
    "notes": [
        "£10 Oyster card fee is non-refundable (changed in 2025).",
        "Max balance is £90.",
        "Can set up auto top-up (minimum £20) when balance drops below threshold.",
        "Under 11s travel free on all TfL services.",
        "11-15 Zip Oyster photocard: free bus/tram, half-price rail.",
    ],
}

# =============================================================================
# 12. HELPER FUNCTIONS FOR COST CALCULATION
# =============================================================================

def daily_cost(zone_range, num_peak_journeys=0, num_off_peak_journeys=0,
               num_bus_journeys=0, has_railcard=False, railcard_type=None):
    """Calculate daily travel cost for a given zone and journey pattern."""
    # Bus cost
    bus_total = min(num_bus_journeys * BUS_TRAM["single_fare"], BUS_TRAM["daily_cap"])

    # Rail cost
    rail_total = 0.0
    fares = SINGLE_FARES_INCLUDING_ZONE_1.get(zone_range, {})
    if not fares:
        fares = SINGLE_FARES_EXCLUDING_ZONE_1.get(zone_range, {})
    if not fares:
        raise ValueError(f"Unknown zone range: {zone_range}")

    for _ in range(num_peak_journeys):
        rail_total += fares["peak"]
    for _ in range(num_off_peak_journeys):
        if has_railcard and railcard_type != "disabled":
            # 1/3 off off-peak
            rail_total += round(fares["off_peak"] * 2 / 3, 2)
        elif has_railcard and railcard_type == "disabled":
            rail_total += round(fares["off_peak"] * 2 / 3, 2)
        else:
            rail_total += fares["off_peak"]

    # Apply daily cap
    caps = DAILY_CAPS_INCLUDING_ZONE_1.get(zone_range, {})
    if not caps:
        caps = DAILY_CAPS_EXCLUDING_ZONE_1.get(zone_range, {})

    if has_railcard and num_peak_journeys == 0:
        # All off-peak day — use railcard cap
        rc_cap = RAILCARD_DAILY_CAPS_OFF_PEAK.get(zone_range)
        if rc_cap:
            rail_total = min(rail_total, rc_cap)
    elif caps:
        if num_peak_journeys > 0:
            rail_total = min(rail_total, caps["anytime"])
        else:
            rail_total = min(rail_total, caps["off_peak"])

    # If mix of bus and rail, total counts toward the rail cap
    total = rail_total + bus_total
    if num_bus_journeys > 0 and (num_peak_journeys > 0 or num_off_peak_journeys > 0):
        # Bus spending counts toward rail daily cap
        if caps:
            cap = caps["anytime"] if num_peak_journeys > 0 else caps["off_peak"]
            total = min(total, cap)

    return round(total, 2)


def weekly_cost(zone_range, days_travelling=5, peak_journeys_per_day=2,
                off_peak_journeys_per_day=0, bus_journeys_per_day=0,
                has_railcard=False, railcard_type=None, payment="contactless"):
    """Calculate weekly travel cost and compare options."""
    # Calculate PAYG cost
    payg_daily = []
    for _ in range(days_travelling):
        cost = daily_cost(zone_range, peak_journeys_per_day,
                         off_peak_journeys_per_day, bus_journeys_per_day,
                         has_railcard, railcard_type)
        payg_daily.append(cost)
    payg_total = sum(payg_daily)

    # Apply weekly cap (contactless only)
    weekly_cap = None
    if payment == "contactless":
        weekly_cap = WEEKLY_CAPS_INCLUDING_ZONE_1.get(zone_range)
        if not weekly_cap:
            weekly_cap = WEEKLY_CAPS_EXCLUDING_ZONE_1.get(zone_range)
        if weekly_cap:
            payg_total = min(payg_total, weekly_cap)

    # Compare with travelcard
    tc = TRAVELCARDS.get(zone_range, {})
    weekly_tc = tc.get("weekly")
    monthly_tc = tc.get("monthly")
    annual_tc = tc.get("annual")

    # Per-week cost of monthly/annual
    monthly_per_week = round(monthly_tc / 4.348, 2) if monthly_tc else None
    annual_per_week = round(annual_tc / 52, 2) if annual_tc else None

    return {
        "payg_weekly": round(payg_total, 2),
        "weekly_cap_applied": weekly_cap is not None and payg_total == weekly_cap,
        "weekly_travelcard": weekly_tc,
        "monthly_travelcard_per_week": monthly_per_week,
        "annual_travelcard_per_week": annual_per_week,
        "cheapest": min(
            filter(None, [payg_total, weekly_tc, monthly_per_week, annual_per_week])
        ),
        "recommendation": _recommend(payg_total, weekly_tc, monthly_per_week,
                                      annual_per_week),
    }


def annual_cost_comparison(zone_range, days_per_week=5, weeks_per_year=48,
                           peak_journeys_per_day=2, off_peak_journeys_per_day=0,
                           bus_journeys_per_day=0, has_railcard=False,
                           railcard_type=None, payment="contactless"):
    """Compare annual cost of different payment methods."""
    # PAYG annual estimate
    wk = weekly_cost(zone_range, days_per_week, peak_journeys_per_day,
                     off_peak_journeys_per_day, bus_journeys_per_day,
                     has_railcard, railcard_type, payment)
    payg_annual = round(wk["payg_weekly"] * weeks_per_year, 2)

    tc = TRAVELCARDS.get(zone_range, {})
    annual_tc = tc.get("annual")
    monthly_tc = tc.get("monthly")
    monthly_annual = round(monthly_tc * 12, 2) if monthly_tc else None

    # Railcard cost
    rc_cost = 0.0
    if has_railcard and railcard_type:
        rc = RAILCARDS.get(railcard_type, {})
        rc_cost = rc.get("annual_cost", 0.0)

    results = {
        "payg_annual": payg_annual + rc_cost,
        "annual_travelcard": annual_tc,
        "monthly_x12": monthly_annual,
        "railcard_cost_included": rc_cost,
    }
    # Only compare actual total-cost options (exclude railcard_cost_included which is a sub-component)
    costs = {k: v for k, v in results.items()
             if v is not None and isinstance(v, (int, float)) and k != "railcard_cost_included"}
    results["cheapest_option"] = min(costs, key=costs.get)
    results["cheapest_cost"] = costs[results["cheapest_option"]]
    results["annual_savings_vs_worst"] = round(max(costs.values()) - min(costs.values()), 2)

    return results


def _recommend(payg, weekly_tc, monthly_pw, annual_pw):
    """Generate a recommendation string."""
    options = {}
    if payg is not None:
        options["PAYG (capped)"] = payg
    if weekly_tc is not None:
        options["Weekly Travelcard"] = weekly_tc
    if monthly_pw is not None:
        options["Monthly Travelcard (per week)"] = monthly_pw
    if annual_pw is not None:
        options["Annual Travelcard (per week)"] = annual_pw

    if not options:
        return "No data available for this zone combination."

    best = min(options, key=options.get)
    return f"Best value: {best} at £{options[best]:.2f}/week"


# =============================================================================
# 13. QUICK REFERENCE — PRINT ALL DATA
# =============================================================================

def print_fare_summary():
    """Print a human-readable summary of all fares."""
    print("=" * 70)
    print("TfL FARE DATA 2025/2026 — LONDON COMMUTE COST OPTIMIZER")
    print("=" * 70)

    print("\n--- BUS & TRAM ---")
    print(f"  Single fare:  £{BUS_TRAM['single_fare']:.2f}")
    print(f"  Daily cap:    £{BUS_TRAM['daily_cap']:.2f}")
    print(f"  Weekly cap:   £{BUS_TRAM['weekly_cap']:.2f}")
    print(f"  Hopper:       Unlimited free transfers within {BUS_TRAM['hopper_fare']['window_minutes']} mins")

    print("\n--- TUBE/DLR/OVERGROUND SINGLE FARES (inc. Zone 1) ---")
    print(f"  {'Zones':<8} {'Peak':>8} {'Off-Peak':>10}")
    for z, f in SINGLE_FARES_INCLUDING_ZONE_1.items():
        print(f"  {z:<8} £{f['peak']:>6.2f}  £{f['off_peak']:>7.2f}")

    print("\n--- TUBE/DLR/OVERGROUND SINGLE FARES (exc. Zone 1) ---")
    print(f"  {'Zones':<8} {'Peak':>8} {'Off-Peak':>10}")
    for z, f in SINGLE_FARES_EXCLUDING_ZONE_1.items():
        print(f"  {z:<8} £{f['peak']:>6.2f}  £{f['off_peak']:>7.2f}")

    print("\n--- DAILY CAPS (inc. Zone 1) ---")
    print(f"  {'Zones':<8} {'Anytime':>10} {'Off-Peak':>10}")
    for z, c in DAILY_CAPS_INCLUDING_ZONE_1.items():
        print(f"  {z:<8} £{c['anytime']:>8.2f}  £{c['off_peak']:>7.2f}")

    print("\n--- WEEKLY CAPS (contactless only, inc. Zone 1) ---")
    for z, c in WEEKLY_CAPS_INCLUDING_ZONE_1.items():
        print(f"  {z:<8} £{c:>8.2f}")

    print("\n--- TRAVELCARD SEASON TICKETS ---")
    print(f"  {'Zones':<8} {'Weekly':>10} {'Monthly':>10} {'Annual':>10}")
    for z, t in TRAVELCARDS.items():
        print(f"  {z:<8} £{t['weekly']:>8.2f}  £{t['monthly']:>8.2f}  £{t['annual']:>8.2f}")

    print("\n--- RAILCARD DISCOUNTED OFF-PEAK DAILY CAPS ---")
    for z, c in RAILCARD_DAILY_CAPS_OFF_PEAK.items():
        print(f"  {z:<8} £{c:>8.2f}")

    print("\n--- RAILCARD PRICES ---")
    for key, rc in RAILCARDS.items():
        cost = f"£{rc['annual_cost']:.0f}/yr"
        if rc.get("three_year_cost"):
            cost += f" or £{rc['three_year_cost']:.0f}/3yr"
        print(f"  {rc['name']:<30} {cost}")

    print("\n--- INCOMPLETE JOURNEY CHARGES ---")
    print(f"  Zones 1-9:     £{INCOMPLETE_JOURNEY['maximum_fare_zones_1_9']:.2f}")
    print(f"  Beyond Zone 9: £{INCOMPLETE_JOURNEY['maximum_fare_beyond_zone_9']:.2f}")
    print(f"  National Rail:  up to £{INCOMPLETE_JOURNEY['national_rail_maximum']:.2f}")

    print("\n--- PEAK HOURS ---")
    print(f"  Morning: {PEAK_HOURS['morning']['start']} - {PEAK_HOURS['morning']['end']}")
    print(f"  Evening: {PEAK_HOURS['evening']['start']} - {PEAK_HOURS['evening']['end']}")
    print(f"  Days:    {PEAK_HOURS['days']}")


if __name__ == "__main__":
    print_fare_summary()

    print("\n" + "=" * 70)
    print("EXAMPLE: Zones 1-2 commuter, 5 days/week, 2 peak journeys/day")
    print("=" * 70)
    result = weekly_cost("1-2", days_travelling=5, peak_journeys_per_day=2)
    for k, v in result.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 70)
    print("EXAMPLE: Annual comparison, Zones 1-3, with 26-30 railcard")
    print("=" * 70)
    result = annual_cost_comparison("1-3", days_per_week=5, weeks_per_year=48,
                                    peak_journeys_per_day=0,
                                    off_peak_journeys_per_day=2,
                                    has_railcard=True, railcard_type="26-30",
                                    payment="contactless")
    for k, v in result.items():
        print(f"  {k}: {v}")

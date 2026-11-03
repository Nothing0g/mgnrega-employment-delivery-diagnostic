"""Canonical, aggregate-only input schema for district-year MIS extracts."""

from __future__ import annotations

IDENTIFIER_COLUMNS = ["fy", "state", "district"]
REQUIRED_METRIC_COLUMNS = [
    "households_demanded",
    "households_provided",
    "persondays_generated",
]
OPTIONAL_METRIC_COLUMNS = [
    "households_100_days",
    "women_persondays",
    "sc_persondays",
    "st_persondays",
    "expenditure_rs",
]
ALL_METRIC_COLUMNS = REQUIRED_METRIC_COLUMNS + OPTIONAL_METRIC_COLUMNS
KEY_COLUMNS = IDENTIFIER_COLUMNS

CANONICAL_COLUMNS = IDENTIFIER_COLUMNS + ALL_METRIC_COLUMNS

# The successor Act came into force on 1 July 2026; 2026-27 is not a clean
# MGNREGA-only financial year and must be flagged in analysis.
TRANSITION_FY_TOKENS = ("2026-27", "2026-2027")

METRIC_DEFINITIONS = {
    "households_demanded": "Households recorded as demanding work in the selected financial year and geography.",
    "households_provided": "Households recorded as having received employment in the selected financial year and geography.",
    "persondays_generated": "Person-days recorded by the source. Preserve the source's exact label and coverage; some official summaries use 'person-days of Central Liability'.",
    "households_100_days": "Households recorded as completing 100 days in the financial year. This is not a direct measure of unmet demand.",
    "women_persondays": "Person-days attributed to women, if provided by the source.",
    "sc_persondays": "Person-days attributed to Scheduled Castes, if provided by the source.",
    "st_persondays": "Person-days attributed to Scheduled Tribes, if provided by the source.",
    "expenditure_rs": "Expenditure in Indian rupees. Include only after documenting the source's expenditure components and period.",
}

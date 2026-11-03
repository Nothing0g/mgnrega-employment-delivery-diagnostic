"""Derived service-delivery indicators and descriptive peer-relative priority screen."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()

    def ratio(numerator: str, denominator: str) -> pd.Series:
        denom = pd.to_numeric(data[denominator], errors="coerce")
        num = pd.to_numeric(data[numerator], errors="coerce")
        return (num / denom.where(denom > 0)) * 100

    data["demand_fulfilment_pct"] = ratio("households_provided", "households_demanded")
    data["unmet_demand_households_proxy"] = data["households_demanded"] - data["households_provided"]
    data["avg_persondays_per_employed_household"] = (
        data["persondays_generated"] / data["households_provided"].where(data["households_provided"] > 0)
    )
    data["households_100_days_share_pct"] = ratio("households_100_days", "households_provided")
    data["women_persondays_share_pct"] = ratio("women_persondays", "persondays_generated")
    data["sc_persondays_share_pct"] = ratio("sc_persondays", "persondays_generated")
    data["st_persondays_share_pct"] = ratio("st_persondays", "persondays_generated")
    data["expenditure_per_personday_rs"] = (
        data["expenditure_rs"] / data["persondays_generated"].where(data["persondays_generated"] > 0)
    )
    return data


def prioritization_screen(frame: pd.DataFrame) -> pd.DataFrame:
    """Rank relatively weak delivery on observed output proxies; this is not an audit score.

    The score is calculated within the supplied peer group. It equally weights
    lower demand-fulfilment share and fewer person-days per employed household.
    Women/SC/ST shares are displayed separately rather than folded into the score,
    because an eligible-population denominator is not available here.
    """
    data = add_metrics(frame)
    result = data.copy()
    indicators = ["demand_fulfilment_pct", "avg_persondays_per_employed_household"]
    scores: list[pd.Series] = []
    for metric in indicators:
        valid = result[metric].dropna()
        if valid.nunique() >= 2:
            percentile = result[metric].rank(method="average", pct=True)
            scores.append((1 - percentile) * 100)
    if scores:
        result["priority_score_relative"] = pd.concat(scores, axis=1).mean(axis=1, skipna=True)
        result["priority_rank_relative"] = result["priority_score_relative"].rank(method="min", ascending=False).astype("Int64")
    else:
        result["priority_score_relative"] = np.nan
        result["priority_rank_relative"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    return result.sort_values("priority_score_relative", ascending=False, na_position="last")


def aggregate_rates(frame: pd.DataFrame) -> dict[str, float | None]:
    """Return denominator-weighted rates; never average district percentages."""
    def weighted(numerator: str, denominator: str) -> float | None:
        if numerator not in frame or denominator not in frame:
            return None
        num = pd.to_numeric(frame[numerator], errors="coerce").sum(min_count=1)
        den = pd.to_numeric(frame[denominator], errors="coerce").sum(min_count=1)
        if pd.isna(num) or pd.isna(den) or den <= 0:
            return None
        return float(num / den * 100)

    return {
        "demand_fulfilment_pct": weighted("households_provided", "households_demanded"),
        "women_persondays_share_pct": weighted("women_persondays", "persondays_generated"),
        "sc_persondays_share_pct": weighted("sc_persondays", "persondays_generated"),
        "st_persondays_share_pct": weighted("st_persondays", "persondays_generated"),
        "households_100_days_share_pct": weighted("households_100_days", "households_provided"),
    }

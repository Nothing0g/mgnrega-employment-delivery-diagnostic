from pathlib import Path
import sqlite3

import pandas as pd

from mgnrega_diag.ingest import validate_panel
from mgnrega_diag.metrics import add_metrics, aggregate_rates, prioritization_screen
from mgnrega_diag.storage import write_sqlite

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_district_panel_test_only.csv"


def load_fixture():
    return pd.read_csv(FIXTURE)


def test_synthetic_fixture_is_explicitly_not_government_data():
    data = load_fixture()
    assert set(data["state"]) == {"TEST-STATE"}
    assert data["district"].str.startswith("Test District").all()


def test_validation_passes_and_optional_fields_are_available():
    result = validate_panel(load_fixture())
    assert result.valid
    assert not result.errors
    assert result.data["households_demanded"].sum() > 0


def test_derived_metrics_use_explicit_numerators_and_denominators():
    row = add_metrics(load_fixture()).iloc[0]
    assert row["demand_fulfilment_pct"] == 80.0
    assert row["avg_persondays_per_employed_household"] == 30.0
    assert row["households_100_days_share_pct"] == 15.0
    assert row["women_persondays_share_pct"] == 60.0
    assert row["sc_persondays_share_pct"] == 20.0
    assert row["st_persondays_share_pct"] == 10.0
    assert row["expenditure_per_personday_rs"] == 400.0


def test_aggregate_rates_are_weighted_not_unweighted_district_means():
    data = load_fixture().query("fy == '2024-25'")
    rates = aggregate_rates(data)
    assert rates["demand_fulfilment_pct"] == (800 + 540) / (1000 + 900) * 100


def test_duplicate_geographic_year_keys_are_errors():
    data = load_fixture()
    duplicate = pd.concat([data, data.iloc[[0]]], ignore_index=True)
    result = validate_panel(duplicate)
    assert not result.valid
    assert any("Duplicate" in error for error in result.errors)


def test_negative_counts_are_errors():
    data = load_fixture()
    data.loc[0, "persondays_generated"] = -1
    result = validate_panel(data)
    assert not result.valid
    assert any("negative" in error.lower() for error in result.errors)


def test_optional_metrics_missing_are_warned_not_fabricated():
    data = load_fixture().drop(columns=["women_persondays", "sc_persondays", "st_persondays", "expenditure_rs"])
    result = validate_panel(data)
    assert result.valid
    assert all(pd.isna(result.data[field]).all() for field in ["women_persondays", "sc_persondays", "st_persondays", "expenditure_rs"])
    assert any("not present" in warning for warning in result.warnings)


def test_missing_required_numeric_values_are_warned_not_imputed():
    data = load_fixture()
    data.loc[0, "households_demanded"] = pd.NA
    result = validate_panel(data)
    assert result.valid
    assert any("households_demanded" in warning and "missing" in warning for warning in result.warnings)
    assert pd.isna(result.data.loc[0, "households_demanded"])


def test_normalized_source_header_non_numeric_values_are_rejected():
    data = load_fixture().rename(columns={"households_provided": "Households Provided"})
    data["Households Provided"] = data["Households Provided"].astype("object")
    data.loc[0, "Households Provided"] = "not-a-count"
    result = validate_panel(data)
    assert not result.valid
    assert any("non-numeric" in error for error in result.errors)


def test_transition_year_is_flagged():
    data = load_fixture().iloc[[0]].copy()
    data["fy"] = "2026-27"
    result = validate_panel(data)
    assert result.valid
    assert any("transition" in warning for warning in result.warnings)


def test_priority_screen_is_relative_and_not_an_absolute_compliance_score():
    result = prioritization_screen(load_fixture().query("fy == '2024-25'")).reset_index(drop=True)
    assert "priority_score_relative" in result
    assert result["priority_score_relative"].between(0, 100).all()
    assert result.iloc[0]["district"] == "Test District B"


def test_sqlite_database_stores_cleaned_panel_and_metadata(tmp_path):
    result = validate_panel(load_fixture())
    enriched = add_metrics(result.data)
    database = tmp_path / "test.sqlite"
    write_sqlite(enriched, database, {"synthetic": True, "records": len(enriched)})
    with sqlite3.connect(database) as connection:
        count = connection.execute("SELECT COUNT(*) FROM district_panel").fetchone()[0]
        metadata = connection.execute("SELECT metadata_json FROM ingest_metadata").fetchone()[0]
    assert count == len(enriched)
    assert '"synthetic": true' in metadata

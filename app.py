from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mgnrega_diag.ingest import read_source, validate_panel  # noqa: E402
from mgnrega_diag.metrics import add_metrics, aggregate_rates, prioritization_screen  # noqa: E402

st.set_page_config(
    page_title="MGNREGA Employment Delivery & Inclusion Diagnostic",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.7rem; padding-bottom: 2rem; max-width: 1500px;}
      .hero {padding: 1.2rem 1.45rem; border-radius: 14px; background: linear-gradient(120deg,#123c3a,#1a6654); color: white; margin-bottom: 1rem;}
      .hero h1 {font-size: 2rem; margin: 0 0 .35rem 0; color: white;}
      .hero p {margin: 0; color: #e3f3ec;}
      .note {padding:.8rem 1rem; background:#f1f5f4; border-left:4px solid #548c7b; border-radius:6px;}
      div[data-testid="stMetric"] {background:#f8faf9; border:1px solid #e5ece9; padding:12px 14px; border-radius:12px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>MGNREGA Employment Delivery & Inclusion Diagnostic</h1>'
    '<p>District-year monitoring of employment demand, delivery depth, participation and spending — with explicit data-quality guardrails.</p></div>',
    unsafe_allow_html=True,
)

st.sidebar.title("Data and filters")
st.sidebar.caption("The project does not download or transmit source records.")
demo_mode = st.sidebar.checkbox("Load synthetic software-test fixture", value=False)
uploaded = st.sidebar.file_uploader("Upload a vetted aggregate CSV or Excel file", type=["csv", "xlsx", "xls"])

source_label = ""
is_synthetic = False
raw: pd.DataFrame | None = None
if demo_mode:
    fixture = ROOT / "tests" / "fixtures" / "synthetic_district_panel_test_only.csv"
    raw = read_source(fixture)
    source_label = "TEST FIXTURE ONLY — fabricated software-test records"
    is_synthetic = True
elif uploaded is not None:
    try:
        raw = read_source(io.BytesIO(uploaded.getvalue()), uploaded.name)
        source_label = f"User-supplied file: {uploaded.name} (source not independently authenticated)"
    except Exception as exc:
        st.error(f"Could not read uploaded file: {exc}")
elif (ROOT / "data" / "processed" / "district_panel.csv").exists():
    processed_file = ROOT / "data" / "processed" / "district_panel.csv"
    raw = read_source(processed_file)
    metadata_file = ROOT / "data" / "processed" / "ingest_metadata.json"
    metadata = json.loads(metadata_file.read_text(encoding="utf-8")) if metadata_file.exists() else {}
    is_synthetic = bool(metadata.get("synthetic", False))
    source_label = (
        "SYNTHETIC TEST OUTPUT — fabricated records"
        if is_synthetic
        else "Local processed file (verify source metadata before interpretation)"
    )

if raw is None:
    st.warning(
        "No verified district extract is bundled. The official portal’s download format and district export were not verified during this build; the data.gov.in resource checked returned ‘Record not found’. Upload a vetted aggregate export after mapping it to the canonical schema, or enable the clearly labeled software-test fixture."
    )
    st.markdown("### What this dashboard will calculate when data is supplied")
    st.markdown(
        "Demand-fulfilment proxy, person-days per employed household, the share of working households completing 100 days, women/SC/ST person-day shares, expenditure per person-day where available, district comparisons and validation flags."
    )
    st.markdown("### Interpretation boundary")
    st.markdown(
        "These are administrative outputs. They do not establish income, poverty, asset quality or empowerment outcomes. A financial-year demand ratio is not a request-date-based statutory compliance measure."
    )
    st.caption("See docs/DIAGNOSTIC_REPORT.md for verified national/state findings and limitations.")
    st.stop()

result = validate_panel(raw)
if is_synthetic:
    st.error("SYNTHETIC TEST DATA — fabricated rows used only to demonstrate software. These are not government statistics and must not be used for policy, reporting or inference.")
else:
    st.info("User-supplied data: this app validates structure and arithmetic, not the authenticity, provenance or official status of the uploaded file.")

st.caption(f"Source status: {source_label} · Rows loaded: {len(raw):,}")
for message in result.warnings:
    st.warning(message)
if result.errors:
    for message in result.errors:
        st.error(message)
    st.stop()

panel = add_metrics(result.data)

fy_values = sorted(panel["fy"].dropna().astype(str).unique().tolist(), reverse=True)
state_values = sorted(panel["state"].dropna().astype(str).unique().tolist())
fy_choice = st.sidebar.selectbox("Financial year", ["All available years"] + fy_values)
state_choice = st.sidebar.selectbox("State / UT", ["All states"] + state_values)
base = panel.copy()
if fy_choice != "All available years":
    base = base[base["fy"].astype(str) == fy_choice]
if state_choice != "All states":
    base = base[base["state"].astype(str) == state_choice]
district_values = sorted(base["district"].dropna().astype(str).unique().tolist())
district_choice = st.sidebar.selectbox("District", ["All districts"] + district_values)
view = base if district_choice == "All districts" else base[base["district"].astype(str) == district_choice]

if view.empty:
    st.info("No records match the selected filters.")
    st.stop()

if fy_choice != "All available years" and any(token in fy_choice for token in ("2026-27", "2026-2027")):
    st.warning("FY 2026–27 straddles the 1 July 2026 change from MGNREGA to the VB-G RAM G Act. Do not compare it as a clean MGNREGA year unless the input records identify the legal regime.")

st.subheader("Selected-scope delivery snapshot")
all_rates = aggregate_rates(view)

def fmt_pct(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f}%"

def fmt_count(value: object) -> str:
    number = pd.to_numeric(value, errors="coerce")
    return "—" if pd.isna(number) else f"{number:,.0f}"

households_demanded = pd.to_numeric(view["households_demanded"], errors="coerce").sum(min_count=1)
households_provided = pd.to_numeric(view["households_provided"], errors="coerce").sum(min_count=1)
persondays = pd.to_numeric(view["persondays_generated"], errors="coerce").sum(min_count=1)
full_days = pd.to_numeric(view["households_100_days"], errors="coerce").sum(min_count=1)
expenditure = pd.to_numeric(view["expenditure_rs"], errors="coerce").sum(min_count=1)

cols = st.columns(3)
cols[0].metric("Households demanded", fmt_count(households_demanded))
cols[1].metric("Households provided", fmt_count(households_provided))
cols[2].metric("Demand fulfilment proxy", fmt_pct(all_rates["demand_fulfilment_pct"]))
cols = st.columns(2)
cols[0].metric("Person-days", fmt_count(persondays))
cols[1].metric("Households completing 100 days", fmt_count(full_days))

if pd.isna(expenditure):
    st.caption("Expenditure is unavailable in the selected input, so cost indicators are not shown.")
else:
    cost = expenditure / persondays if pd.notna(persondays) and persondays > 0 else None
    st.metric("Reported expenditure (all components as supplied)", f"₹{expenditure / 10_000_000:,.2f} cr" if pd.notna(expenditure) else "—")
    st.caption(f"Expenditure per person-day: ₹{cost:,.2f} only if input expenditure and person-days have matching scope and period." if cost is not None else "Expenditure per person-day unavailable.")

inclusion = st.columns(3)
inclusion[0].metric("Women person-day share", fmt_pct(all_rates["women_persondays_share_pct"]))
inclusion[1].metric("SC person-day share", fmt_pct(all_rates["sc_persondays_share_pct"]))
inclusion[2].metric("ST person-day share", fmt_pct(all_rates["st_persondays_share_pct"]))
st.caption("Subgroup percentages use total person-days as denominator. They are participation shares, not population-adjusted equity measures.")

st.markdown('<div class="note"><b>Output, not outcome:</b> days, households reached, participation and expenditure are administrative outputs. They do not establish income change, asset quality, resilience or empowerment. Correlation is not causation.</div>', unsafe_allow_html=True)

left, right = st.columns([1.1, 1])
with left:
    st.subheader("Employment delivery over time")
    trend_data = panel.copy()
    if state_choice != "All states":
        trend_data = trend_data[trend_data["state"].astype(str) == state_choice]
    if district_choice != "All districts":
        trend_data = trend_data[trend_data["district"].astype(str) == district_choice]
    trend = trend_data.groupby("fy", as_index=False)[["persondays_generated", "households_demanded", "households_provided"]].sum(min_count=1)
    if len(trend) > 1:
        long = trend.melt(id_vars="fy", value_vars=["persondays_generated"], var_name="metric", value_name="value")
        chart = px.line(long.sort_values("fy"), x="fy", y="value", markers=True, title="Person-days by FY", labels={"fy": "Financial year", "value": "Person-days", "metric": "Indicator"})
        chart.update_layout(height=340, showlegend=False, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(chart, width="stretch")
    else:
        st.info("Select a state/district with multiple years to view a time trend.")

with right:
    st.subheader("District delivery variation")
    if fy_choice == "All available years":
        st.info("Select one financial year to compare districts without pooling unlike periods.")
    else:
        comparison = add_metrics(base)
        if district_choice != "All districts":
            comparison = add_metrics(panel[(panel["fy"].astype(str) == fy_choice) & (panel["state"].astype(str) == state_choice)]) if state_choice != "All states" else add_metrics(panel[panel["fy"].astype(str) == fy_choice])
        else:
            comparison = comparison[comparison["district"].notna()]
        comparison["district_label"] = comparison["district"].astype(str) + " · " + comparison["state"].astype(str)
        if comparison["demand_fulfilment_pct"].notna().any():
            chart = px.bar(comparison.sort_values("demand_fulfilment_pct", ascending=True), x="demand_fulfilment_pct", y="district_label", orientation="h", title="Households provided ÷ households demanded", labels={"demand_fulfilment_pct": "Percent (proxy)", "district_label": "District · State"}, hover_data=["households_demanded", "households_provided"])
            chart.update_layout(height=max(340, min(620, 24 * len(comparison))), margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(chart, width="stretch")
        else:
            st.info("Demand fields are missing or have zero denominators; district fulfilment comparison is unavailable.")

st.subheader("Priority screen")
if fy_choice == "All available years":
    st.info("Choose a single FY to build a peer-relative screen. The score is not a compliance judgement.")
else:
    priority_input = panel[panel["fy"].astype(str) == fy_choice].copy()
    if state_choice != "All states":
        priority_input = priority_input[priority_input["state"].astype(str) == state_choice]
    priorities = prioritization_screen(priority_input)
    if priorities["priority_score_relative"].notna().any():
        show_cols = ["state", "district", "demand_fulfilment_pct", "avg_persondays_per_employed_household", "priority_score_relative", "priority_rank_relative"]
        show_cols = [column for column in show_cols if column in priorities.columns]
        display = priorities[show_cols].round(2).rename(columns={
            "state": "State", "district": "District", "demand_fulfilment_pct": "Fulfilled (%)",
            "avg_persondays_per_employed_household": "Days / HH", "priority_score_relative": "Priority (0–100)",
            "priority_rank_relative": "Rank",
        })
        st.dataframe(display, width="stretch", hide_index=True)
        st.caption("Higher score = relatively weaker observed fulfilment and/or fewer days per working household within this selected peer set. Inclusion shares are not included in the score because population denominators are not available.")
    else:
        st.info("At least two comparable observations are needed to calculate a relative score.")

with st.expander("Data quality and source definitions"):
    st.write("Required source grain: one state × district × FY row. Duplicate keys stop the pipeline. Missing optional fields remain missing; no imputation is performed.")
    st.write("The demand-fulfilment ratio is a period aggregate proxy. It does not identify a household’s request date or work-offer date. A legal response-time assessment requires dated records and the rule in force for that observation.")
    st.write("See `docs/DATA_DICTIONARY.md`, `docs/METHODOLOGY.md` and `docs/SOURCE_REGISTER.md` for definitions and acquisition limitations.")
    st.dataframe(result.data, width="stretch", hide_index=True)

st.caption("MGNREGA Employment Delivery & Inclusion Diagnostic · local-first analytics · raw inputs are not uploaded by this app")

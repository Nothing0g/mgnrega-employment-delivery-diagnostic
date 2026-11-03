# Data dictionary

The application accepts **aggregated** district–financial-year records only. It does not accept worker-level or job-card-level data. The government portal’s downloadable file headers and export format could not be verified during this build, so the import expects the canonical column names below after an explicit, documented mapping. Header casing and punctuation are normalized; the program does not guess field meaning.

| Canonical field | Required? | Unit | Definition and caveat |
|---|---:|---|---|
| `fy` | Yes | Financial year string, e.g. `2024-25` | Preserve the source financial-year label. |
| `state` | Yes | Text | State/UT as published by source. |
| `district` | Yes | Text | District as published by source. District boundaries/names may change over time; no crosswalk is bundled. |
| `households_demanded` | Yes | Households | Households recorded as demanding work in the period. Confirm source definition and period. |
| `households_provided` | Yes | Households | Households recorded as receiving employment. This is not the same as persons or workdays. |
| `persondays_generated` | Yes | Person-days | Preserve source label and coverage. An official annual summary may label this “person-days of Central Liability”; do not silently equate differing source definitions. |
| `households_100_days` | No | Households | Households recorded as completing 100 days in the FY. Low completion alone does not prove unmet demand. |
| `women_persondays` | No | Person-days | Person-days attributed to women. Share denominator is total person-days in the same row. This is not a measure of women’s population-adjusted access. |
| `sc_persondays` | No | Person-days | Person-days attributed to Scheduled Castes. Share denominator is total person-days in the same row. |
| `st_persondays` | No | Person-days | Person-days attributed to Scheduled Tribes. Share denominator is total person-days in the same row. |
| `expenditure_rs` | No | Indian rupees | Expenditure amount. Document source components, liabilities, timing and nominal-price basis before comparing. |

## Derived fields

`demand_fulfilment_pct` = households provided ÷ households demanded × 100, aggregated across districts as sum(provided) ÷ sum(demanded), not as an unweighted average of district percentages. It is a FY-level administrative proxy, not a test of whether each request received work within the statutory time limit. Values above 100% are retained and flagged.

`unmet_demand_households_proxy` = households demanded − households provided. This can be negative when source timing or definitions do not align; inspect warnings rather than clipping it.

`avg_persondays_per_employed_household` = person-days generated ÷ households provided. Confirm compatible coverage before comparing.

`households_100_days_share_pct` = households completing 100 days ÷ households provided × 100. It is a depth-of-employment output indicator, not an outcome or a failure rate.

`women_persondays_share_pct`, `sc_persondays_share_pct` and `st_persondays_share_pct` divide the respective subgroup person-days by total person-days. These are participation shares, not parity/equity rates without the relevant eligible population, labour force, demand, or household denominators.

`expenditure_per_personday_rs` = reported expenditure rupees ÷ person-days. Use only when both measures refer to matching scope and period; do not call it a wage rate.

`priority_score_relative` is a peer-relative screening score that gives equal weight to lower demand fulfilment and lower average person-days per employed household within the currently supplied comparison set. It is not an audit finding, causal estimate, or entitlement-compliance determination. Subgroup shares are shown separately and are excluded from the score because population denominators are not available.

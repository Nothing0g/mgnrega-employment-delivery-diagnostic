# Methodology

## Scope and data acquisition

The intended observation is one district × financial-year record, with fields for households demanding and provided employment, person-days, households completing 100 days, subgroup person-days and expenditure. The current official portal advertises district filtering and a download action, but a district file was not successfully retrieved during this build. The OGD record inspected returned “Record not found.” Accordingly, the repository contains **no observed district data** and makes no district-level performance claims.

A user-supplied official export should be stored locally in `data/raw/` (ignored by Git). First run `python scripts/inspect_source.py <file>`; record the source URL, access date, source title, reporting date, FY coverage, exact header labels, units, aggregation and any source footnotes. Explicitly map those fields to `docs/DATA_DICTIONARY.md`. The importer supports local CSV and Excel but does not claim the government portal exports either format. No raw or worker-level records should be committed.

## Validation

The pipeline normalizes header typography only, then requires `fy`, `state`, `district`, `households_demanded`, `households_provided` and `persondays_generated`. It rejects missing keys, nonnumeric nonblank values, negative numeric observations and duplicate state–district–FY keys. Missing optional demographic, full-days or expenditure fields remain missing and are reported; they are never imputed.

Potentially material anomalies are warnings, not silent corrections: households provided exceeding demand, 100-day households exceeding households provided, subgroup person-days above total person-days, and a period spanning the July 2026 legal change. District boundaries, missingness and source revisions require analyst review. The pipeline hashes the source file and saves aggregate outputs plus a local SQLite table; raw data, outputs, database files and environment secrets are git-ignored.

## Derived measures

The demand-fulfilment proxy is households provided ÷ households demanded, and its aggregate is a denominator-weighted ratio (sum provided ÷ sum demanded). It is not a timing-based legal compliance measure. An exact statutory assessment needs request dates, work-offer dates and the governing rules. Average days is person-days ÷ households provided. The 100-day completion share is 100-day households ÷ households provided. Women, SC and ST person-day shares use total person-days as denominator. Expenditure per person-day is reported only when expenditure components and period match. See `DATA_DICTIONARY.md` for detailed formulas and caveats.

## Prioritization

The screening score ranks districts **within the selected peer set** using the average of percentile-based risk on (a) lower demand-fulfilment proxy and (b) fewer person-days per employed household. Both inputs are equal-weighted. It is a descriptive queue for investigation, not a pass/fail threshold or causal index. Women's and SC/ST participation are displayed as separate flags because person-day shares without eligible-population or demand denominators cannot support an equity ranking. A final field intervention should check source completeness, demand registration, local context, payment and worksite records, and worker feedback.

## Interpretation

Person-days, households reached, full-100-day households, participation and spending are **administrative outputs**. They do not establish income gains, asset quality, resilience, poverty reduction or women’s empowerment. Observed district correlations are not causal. Expenditure per person-day may be confounded by wage rates, geography, work mix, material/labour composition and accounting timing. This repository makes no causal estimates.

## Legal comparability

Official PIB guidance states MGNREGA was repealed on 1 July 2026, when the VB-G RAM G Act commenced with a 125-day guarantee. FY 2026–27 crosses that date. It is flagged in the dashboard and should not be treated as a single-regime MGNREGA trend. Earlier MGNREGA FYs also require consistent source definitions and district-boundary treatment before trend comparisons.

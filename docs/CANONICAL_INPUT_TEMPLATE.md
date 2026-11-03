# Canonical input template

Create a local aggregate CSV with exactly these headers after inspecting and explicitly mapping an official source file. This template intentionally contains **no data rows** and must not be used to imply that government statistics were obtained.

```csv
fy,state,district,households_demanded,households_provided,persondays_generated,households_100_days,women_persondays,sc_persondays,st_persondays,expenditure_rs
```

Optional numeric values may be blank when the verified source does not provide them. Record the source field label, definition, unit, coverage and any footnotes separately. Refer to [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md).

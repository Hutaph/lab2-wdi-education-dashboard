# lab2-wdi-education-dashboard

## Preprocessing

Run preprocessing:

```bash
python scripts/preprocess_wdi_education.py
```

Output:

- `data/processed/wdi_education_preprocessed.csv`: long-format enriched dataset for the dashboard.

The processed dataset keeps one row per country, indicator, and year, with added features for filtering, KPI cards, trend charts, ranking, and missing-value handling.

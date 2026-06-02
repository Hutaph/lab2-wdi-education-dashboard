import numpy as np
import pandas as pd

from .config import (
    SMOOTH_CONTEXT_CODES,
    EDUCATION_RATE_CODES,
    FINANCE_CODES,
    OUT_OF_SCHOOL_CODES,
    LITERACY_CODES,
)
from .utils import classify_indicator

def get_imputation_rule(series_code: str) -> dict:
    if series_code in SMOOTH_CONTEXT_CODES:
        return {
            "max_internal_gap": None,
            "max_edge_gap": 2,
            "transform": None,
            "clip_lower": 0,
            "clip_upper": 100 if series_code == "SP.URB.TOTL.IN.ZS" else None,
            "internal_method": "linear_smooth_interpolation",
        }

    if series_code in EDUCATION_RATE_CODES:
        return {
            "max_internal_gap": 3,
            "max_edge_gap": 1,
            "transform": None,
            "clip_lower": 0,
            "clip_upper": None,
            "internal_method": "linear_short_gap_interpolation",
        }

    if series_code in FINANCE_CODES:
        return {
            "max_internal_gap": 2,
            "max_edge_gap": 1,
            "transform": None,
            "clip_lower": 0,
            "clip_upper": 100,
            "internal_method": "linear_short_gap_interpolation",
        }

    if series_code in OUT_OF_SCHOOL_CODES:
        return {
            "max_internal_gap": 2,
            "max_edge_gap": 1,
            "transform": "log1p",
            "clip_lower": 0,
            "clip_upper": None,
            "internal_method": "log_linear_short_gap_interpolation",
        }

    if series_code in LITERACY_CODES:
        return {
            "max_internal_gap": None,
            "max_edge_gap": 0,
            "transform": None,
            "clip_lower": 0,
            "clip_upper": 100,
            "internal_method": "linear_sparse_census_interpolation",
        }

    return {
        "max_internal_gap": 2,
        "max_edge_gap": 1,
        "transform": None,
        "clip_lower": None,
        "clip_upper": None,
        "internal_method": "linear_short_gap_interpolation",
    }


def iter_missing_runs(mask: np.ndarray):
    start = None
    for idx, is_missing in enumerate(mask):
        if is_missing and start is None:
            start = idx
        elif not is_missing and start is not None:
            yield start, idx - 1
            start = None

    if start is not None:
        yield start, len(mask) - 1


def apply_transform(series: pd.Series, transform_type: str) -> pd.Series:
    if transform_type == "log1p":
        return pd.Series(np.log1p(series.clip(lower=0).to_numpy()), index=series.index)
    return series.copy()


def reverse_transform(series: pd.Series, transform_type: str) -> pd.Series:
    if transform_type == "log1p":
        return pd.Series(np.expm1(series.to_numpy()), index=series.index)
    return series.copy()


def impute_time_series(values: pd.Series, year_lookup: dict, rule: dict) -> tuple[pd.Series, pd.Series]:
    result = values.astype("float64").copy()
    methods = pd.Series(pd.NA, index=values.index, dtype="object")

    if result.notna().sum() < 2:
        return result, methods

    years = pd.Index([year_lookup[col] for col in values.index])
    
    working_values = apply_transform(result, rule.get("transform"))
    working_series = pd.Series(working_values.to_numpy(), index=years, dtype="float64")
    interpolated = working_series.interpolate(method="index", limit_area="inside")
    interpolated_values = reverse_transform(interpolated, rule.get("transform"))

    candidates = pd.Series(interpolated_values.to_numpy(), index=values.index, dtype="float64")
    missing_mask = result.isna().to_numpy()

    for start, end in iter_missing_runs(missing_mask):
        run_length = end - start + 1
        is_internal_gap = start > 0 and end < len(result) - 1

        if is_internal_gap:
            max_internal_gap = rule["max_internal_gap"]
            if max_internal_gap is None or run_length <= max_internal_gap:
                fill_columns = values.index[start : end + 1]
                result.loc[fill_columns] = candidates.loc[fill_columns]
                methods.loc[fill_columns] = rule["internal_method"]
            continue

        max_edge_gap = rule["max_edge_gap"]
        if max_edge_gap is None or run_length > max_edge_gap or max_edge_gap == 0:
            continue

        fill_columns = values.index[start : end + 1]
        if start == 0 and end < len(result) - 1:
            edge_value = result.iloc[end + 1]
        elif end == len(result) - 1 and start > 0:
            edge_value = result.iloc[start - 1]
        else:
            continue

        if pd.notna(edge_value):
            result.loc[fill_columns] = edge_value
            methods.loc[fill_columns] = "edge_nearest_short_gap"

    if rule["clip_lower"] is not None or rule["clip_upper"] is not None:
        result = result.clip(lower=rule["clip_lower"], upper=rule["clip_upper"])

    return result, methods


def fill_full_country_indicator_series(values: pd.Series, year_lookup: dict, rule: dict) -> pd.Series:
    result = values.astype("float64").copy()

    if result.notna().sum() == 0:
        return result

    years = pd.Index([year_lookup[col] for col in values.index])
    
    working_values = apply_transform(result, rule.get("transform"))
    working_series = pd.Series(working_values.to_numpy(), index=years, dtype="float64")
    filled = working_series.interpolate(method="index", limit_direction="both")
    result_values = reverse_transform(filled, rule.get("transform"))
    
    result = pd.Series(result_values.to_numpy(), index=values.index, dtype="float64")

    if rule["clip_lower"] is not None or rule["clip_upper"] is not None:
        result = result.clip(lower=rule["clip_lower"], upper=rule["clip_upper"])

    return result


def fill_remaining_missing_values(
    df: pd.DataFrame,
    values: pd.DataFrame,
    methods: pd.DataFrame,
    year_columns: list[str],
    year_lookup: dict,
) -> None:
    for idx, row in df.iterrows():
        missing_mask = values.loc[idx, year_columns].isna()
        if not missing_mask.any():
            continue

        rule = get_imputation_rule(row["Series Code"])
        filled_values = fill_full_country_indicator_series(values.loc[idx, year_columns], year_lookup, rule)
        fill_mask = missing_mask & filled_values.notna()
        values.loc[idx, fill_mask] = filled_values.loc[fill_mask]
        methods.loc[idx, fill_mask] = "country_indicator_full_series_fill"

    for col in year_columns:
        for series_code, group in df.groupby("Series Code"):
            row_index = group.index
            missing_mask = values.loc[row_index, col].isna()
            if not missing_mask.any():
                continue

            same_year_median = values.loc[row_index, col].median(skipna=True)
            if pd.notna(same_year_median):
                target_index = missing_mask[missing_mask].index
                values.loc[target_index, col] = same_year_median
                methods.loc[target_index, col] = "fallback_same_indicator_year_median"

    for series_code, group in df.groupby("Series Code"):
        row_index = group.index
        series_median = values.loc[row_index, year_columns].stack().median(skipna=True)
        if pd.isna(series_median):
            unit = classify_indicator(group["Series Name"].iloc[0])["metric_unit"]
            series_median = {
                "index": 1,
                "percent": 0,
                "current_usd": 0,
                "years": 0,
                "people": 0,
            }.get(unit, 0)

        missing_mask = values.loc[row_index, year_columns].isna()
        if missing_mask.any().any():
            values.loc[row_index, year_columns] = values.loc[row_index, year_columns].mask(
                missing_mask,
                series_median,
            )
            methods.loc[row_index, year_columns] = methods.loc[row_index, year_columns].mask(
                missing_mask,
                "fallback_same_indicator_median",
            )

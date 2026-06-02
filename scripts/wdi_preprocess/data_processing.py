import re
import numpy as np
import pandas as pd

from .config import (
    RAW_DATA_PATH,
    MISSING_VALUES,
    MAX_ANALYSIS_YEAR,
    ID_COLUMNS,
    LONG_OUTPUT_COLUMNS,
    COUNTRY_YEAR_OUTPUT_COLUMNS,
    INDICATOR_COLUMN_MAP,
    RAW_INDICATOR_COLUMNS,
)
from .utils import get_year_from_column, classify_indicator, trend_direction, safe_divide
from .imputation import impute_time_series, fill_remaining_missing_values, get_imputation_rule
from .feature_engineering import derive_out_of_school_components


def impute_year_values(
    df: pd.DataFrame,
    year_columns: list[str],
    year_lookup: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    imputed_values = df[year_columns].copy()
    imputation_methods = pd.DataFrame("not_imputed", index=df.index, columns=year_columns, dtype="object")
    imputation_methods = imputation_methods.mask(imputed_values.notna(), "raw_observed")

    derive_out_of_school_components(df, imputed_values, imputation_methods, year_columns)

    for idx, row in df.iterrows():
        rule = get_imputation_rule(row["Series Code"])
        filled_values, filled_methods = impute_time_series(imputed_values.loc[idx, year_columns], year_lookup, rule)
        fill_mask = imputed_values.loc[idx, year_columns].isna() & filled_values.notna()
        imputed_values.loc[idx, fill_mask] = filled_values.loc[fill_mask]
        imputation_methods.loc[idx, fill_mask] = filled_methods.loc[fill_mask]

    derive_out_of_school_components(df, imputed_values, imputation_methods, year_columns)
    fill_remaining_missing_values(df, imputed_values, imputation_methods, year_columns, year_lookup)
    return imputed_values, imputation_methods


def build_dataset() -> pd.DataFrame:
    df = pd.read_csv(RAW_DATA_PATH, na_values=MISSING_VALUES)
    df = df.dropna(how="all")

    valid_country_code = df["Country Code"].astype("string").str.fullmatch(r"[A-Z]{3}", na=False)
    df = df[valid_country_code & df["Series Code"].notna()].copy()

    year_columns = [
        col
        for col in df.columns
        if re.fullmatch(r"\d{4} \[YR\d{4}\]", col)
        and get_year_from_column(col) <= MAX_ANALYSIS_YEAR
    ]
    year_lookup = {col: get_year_from_column(col) for col in year_columns}

    for col in ID_COLUMNS:
        df[col] = df[col].astype("string").str.strip()

    for col in year_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    feature_df = df["Series Name"].apply(classify_indicator)
    raw_year_values = df[year_columns].copy()
    imputed_year_values, _ = impute_year_values(df, year_columns, year_lookup)
    df[year_columns] = imputed_year_values
    year_stats = raw_year_values

    available_year_count = year_stats.notna().sum(axis=1)
    missing_year_count = year_stats.isna().sum(axis=1)

    first_year = []
    latest_year = []
    first_value = []
    latest_value = []

    for _, row in imputed_year_values.iterrows():
        valid_values = row.dropna()
        if valid_values.empty:
            first_year.append(pd.NA)
            latest_year.append(pd.NA)
            first_value.append(pd.NA)
            latest_value.append(pd.NA)
            continue

        first_col = valid_values.index[0]
        latest_col = valid_values.index[-1]
        first_year.append(year_lookup[first_col])
        latest_year.append(year_lookup[latest_col])
        first_value.append(valid_values.iloc[0])
        latest_value.append(valid_values.iloc[-1])

    indicator_features = pd.concat([df[ID_COLUMNS].reset_index(drop=True), feature_df.reset_index(drop=True)], axis=1)
    indicator_features["available_year_count"] = available_year_count.to_numpy()
    indicator_features["missing_year_count"] = missing_year_count.to_numpy()
    indicator_features["first_year_with_value"] = first_year
    indicator_features["latest_year_with_value"] = latest_year
    indicator_features["first_value"] = first_value
    indicator_features["latest_value"] = latest_value
    indicator_features["change_since_first"] = indicator_features["latest_value"] - indicator_features["first_value"]
    first_values = pd.to_numeric(indicator_features["first_value"], errors="coerce")
    change_values = pd.to_numeric(indicator_features["change_since_first"], errors="coerce")
    indicator_features["pct_change_since_first"] = np.divide(
        change_values,
        first_values,
        out=np.zeros_like(change_values, dtype="float64"),
        where=first_values.ne(0) & first_values.notna(),
    ) * 100
    indicator_features["trend_direction"] = indicator_features["change_since_first"].apply(trend_direction)

    long_df = df.melt(
        id_vars=ID_COLUMNS,
        value_vars=year_columns,
        var_name="year_column",
        value_name="value",
    )
    long_df["year"] = long_df["year_column"].str.extract(r"(\d{4})").astype(int)

    long_df = long_df.rename(
        columns={
            "Country Name": "country_name",
            "Country Code": "country_code",
            "Series Name": "series_name",
            "Series Code": "series_code",
        }
    )

    long_df = long_df.merge(
        indicator_features[
            [
                "Country Code",
                "Series Code",
                "indicator_category",
                "education_level",
                "gender",
                "metric_unit",
                "available_year_count",
                "missing_year_count",
                "first_year_with_value",
                "latest_year_with_value",
                "first_value",
                "latest_value",
                "change_since_first",
                "pct_change_since_first",
                "trend_direction",
            ]
        ].rename(columns={"Country Code": "country_code", "Series Code": "series_code"}),
        on=["country_code", "series_code"],
        how="left",
    )

    long_df = long_df.sort_values(["country_code", "series_code", "year"]).reset_index(drop=True)
    group_cols = ["country_code", "series_code"]
    long_df["previous_value"] = long_df.groupby(group_cols)["value"].shift(1)
    long_df["yoy_change"] = long_df["value"] - long_df["previous_value"]
    long_df["previous_value"] = long_df["previous_value"].fillna(long_df["value"])
    long_df["yoy_change"] = long_df["yoy_change"].fillna(0)
    previous_values = pd.to_numeric(long_df["previous_value"], errors="coerce")
    yoy_changes = pd.to_numeric(long_df["yoy_change"], errors="coerce")
    long_df["yoy_change_pct"] = np.divide(
        yoy_changes,
        previous_values,
        out=np.zeros_like(yoy_changes, dtype="float64"),
        where=previous_values.ne(0) & previous_values.notna(),
    ) * 100
    long_df["is_value_available"] = long_df["value"].notna()
    long_df["is_latest_year_with_value"] = (
        long_df["latest_year_with_value"].notna()
        & long_df["year"].eq(long_df["latest_year_with_value"].astype("Int64"))
    )
    long_df["decade"] = (long_df["year"] // 10 * 10).astype(str) + "s"
    long_df["period_5y"] = ((long_df["year"] - 2001) // 5 * 5 + 2001).astype(str) + "-" + (
        (long_df["year"] - 2001) // 5 * 5 + 2005
    ).astype(str)

    long_df = long_df[LONG_OUTPUT_COLUMNS]
    return long_df


def build_country_year_dataset(long_df: pd.DataFrame) -> pd.DataFrame:
    country_year_df = (
        long_df[long_df["series_code"].isin(INDICATOR_COLUMN_MAP)]
        .pivot(
            index=["country_name", "country_code", "year"],
            columns="series_code",
            values="value",
        )
        .rename(columns=INDICATOR_COLUMN_MAP)
        .reset_index()
    )

    for col in RAW_INDICATOR_COLUMNS:
        if col not in country_year_df:
            country_year_df[col] = pd.NA

    country_year_df = country_year_df[["country_name", "country_code", "year", *RAW_INDICATOR_COLUMNS]]
    indicators = country_year_df[RAW_INDICATOR_COLUMNS]

    country_year_df["available_indicator_count"] = indicators.notna().sum(axis=1)
    country_year_df["missing_indicator_count"] = indicators.isna().sum(axis=1)
    country_year_df["data_completeness_pct"] = (
        country_year_df["available_indicator_count"] / len(RAW_INDICATOR_COLUMNS) * 100
    )

    country_year_df["primary_secondary_enrollment_gap"] = (
        country_year_df["school_enrollment_primary"] - country_year_df["school_enrollment_secondary"]
    )
    country_year_df["secondary_tertiary_enrollment_gap"] = (
        country_year_df["school_enrollment_secondary"] - country_year_df["school_enrollment_tertiary"]
    )
    country_year_df["completion_gap_primary_lower_secondary"] = (
        country_year_df["primary_completion_rate"] - country_year_df["lower_secondary_completion_rate"]
    )
    country_year_df["out_of_school_gender_gap"] = (
        country_year_df["children_out_of_school_female"] - country_year_df["children_out_of_school_male"]
    )
    country_year_df["out_of_school_female_share"] = safe_divide(
        country_year_df["children_out_of_school_female"],
        country_year_df["children_out_of_school_total"],
    ) * 100
    country_year_df["out_of_school_male_share"] = safe_divide(
        country_year_df["children_out_of_school_male"],
        country_year_df["children_out_of_school_total"],
    ) * 100
    country_year_df["out_of_school_per_100k_population"] = safe_divide(
        country_year_df["children_out_of_school_total"],
        country_year_df["population"],
    ) * 100000
    country_year_df["gdp_per_capita_log"] = np.log1p(country_year_df["gdp_per_capita"])
    country_year_df["population_log"] = np.log1p(country_year_df["population"])
    country_year_df["gender_parity_score"] = (
        100 - (country_year_df["gender_parity_index"] - 1).abs() * 100
    ).clip(lower=0, upper=100)

    education_score_components = pd.DataFrame(
        {
            "primary": country_year_df["school_enrollment_primary"].clip(0, 100),
            "secondary": country_year_df["school_enrollment_secondary"].clip(0, 100),
            "tertiary": country_year_df["school_enrollment_tertiary"].clip(0, 100),
            "primary_completion": country_year_df["primary_completion_rate"].clip(0, 100),
            "lower_secondary_completion": country_year_df["lower_secondary_completion_rate"].clip(0, 100),
            "literacy": country_year_df["literacy_rate"].clip(0, 100),
            "gender_parity": country_year_df["gender_parity_score"],
        }
    )
    country_year_df["education_access_score"] = education_score_components.mean(axis=1, skipna=True)

    development_components = country_year_df.groupby("year")[
        ["gdp_per_capita", "life_expectancy", "urban_population"]
    ].rank(pct=True)
    country_year_df["development_context_score"] = development_components.mean(axis=1, skipna=True) * 100

    country_year_df = country_year_df.sort_values(["country_code", "year"]).reset_index(drop=True)
    country_year_df = country_year_df[COUNTRY_YEAR_OUTPUT_COLUMNS]
    return country_year_df

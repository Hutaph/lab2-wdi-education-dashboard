import re
import numpy as np
import pandas as pd

from .config import (
    RAW_DATA_FILE,
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


def load_and_clean_data() -> pd.DataFrame:
    if not RAW_DATA_FILE.exists():
        raise FileNotFoundError(f"Raw WDI education data file not found: {RAW_DATA_FILE}")

    df = pd.read_csv(RAW_DATA_FILE, na_values=MISSING_VALUES)
    df = df.dropna(how="all")

    valid_country_code = df["Country Code"].astype("string").str.fullmatch(r"[A-Z]{3}", na=False)
    df = df[valid_country_code & df["Series Code"].notna()].copy()

    for col in ID_COLUMNS:
        df[col] = df[col].astype("string").str.strip()

    return df


def get_year_columns_and_lookup(df: pd.DataFrame) -> tuple[list[str], dict]:
    year_columns = [
        col for col in df.columns
        if re.fullmatch(r"\d{4} \[YR\d{4}\]", col)
        and get_year_from_column(col) <= MAX_ANALYSIS_YEAR
    ]
    year_lookup = {col: get_year_from_column(col) for col in year_columns}
    return year_columns, year_lookup


def compute_time_series_features(
    df: pd.DataFrame, 
    imputed_year_values: pd.DataFrame, 
    raw_year_values: pd.DataFrame, 
    year_lookup: dict
) -> pd.DataFrame:
    available_year_count = raw_year_values.notna().sum(axis=1)
    missing_year_count = raw_year_values.isna().sum(axis=1)

    first_col = imputed_year_values.apply(pd.Series.first_valid_index, axis=1)
    latest_col = imputed_year_values.apply(pd.Series.last_valid_index, axis=1)

    first_year = first_col.map(year_lookup).astype("Int64")
    latest_year = latest_col.map(year_lookup).astype("Int64")

    first_value = imputed_year_values.bfill(axis=1).iloc[:, 0]
    latest_value = imputed_year_values.ffill(axis=1).iloc[:, -1]

    first_value = first_value.where(first_col.notna(), pd.NA)
    latest_value = latest_value.where(latest_col.notna(), pd.NA)

    feature_df = df["Series Name"].apply(classify_indicator)
    indicator_features = pd.concat([df[ID_COLUMNS].reset_index(drop=True), feature_df.reset_index(drop=True)], axis=1)

    indicator_features["available_year_count"] = available_year_count.to_numpy()
    indicator_features["missing_year_count"] = missing_year_count.to_numpy()
    indicator_features["first_year_with_value"] = first_year.to_numpy()
    indicator_features["latest_year_with_value"] = latest_year.to_numpy()
    indicator_features["first_value"] = first_value.to_numpy()
    indicator_features["latest_value"] = latest_value.to_numpy()

    indicator_features["change_since_first"] = indicator_features["latest_value"] - indicator_features["first_value"]
    
    first_values_num = pd.to_numeric(indicator_features["first_value"], errors="coerce")
    change_values_num = pd.to_numeric(indicator_features["change_since_first"], errors="coerce")
    
    indicator_features["pct_change_since_first"] = np.divide(
        change_values_num,
        first_values_num,
        out=np.zeros_like(change_values_num, dtype="float64"),
        where=first_values_num.ne(0) & first_values_num.notna(),
    ) * 100
    
    indicator_features["trend_direction"] = indicator_features["change_since_first"].apply(trend_direction)
    return indicator_features


def reshape_to_long_format(df: pd.DataFrame, year_columns: list[str], indicator_features: pd.DataFrame) -> pd.DataFrame:
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

    merge_cols = [
        "country_code", "series_code", "indicator_category", "education_level",
        "gender", "metric_unit", "available_year_count", "missing_year_count",
        "first_year_with_value", "latest_year_with_value", "first_value",
        "latest_value", "change_since_first", "pct_change_since_first", "trend_direction"
    ]

    long_df = long_df.merge(
        indicator_features.rename(columns={"Country Code": "country_code", "Series Code": "series_code"})[merge_cols],
        on=["country_code", "series_code"],
        how="left",
    )

    long_df = long_df.sort_values(["country_code", "series_code", "year"]).reset_index(drop=True)
    return long_df


def calculate_yoy_metrics(long_df: pd.DataFrame) -> pd.DataFrame:
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

    return long_df[LONG_OUTPUT_COLUMNS]


def build_dataset() -> pd.DataFrame:
    df = load_and_clean_data()
    year_columns, year_lookup = get_year_columns_and_lookup(df)

    for col in year_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    raw_year_values = df[year_columns].copy()
    imputed_year_values, _ = impute_year_values(df, year_columns, year_lookup)
    df[year_columns] = imputed_year_values

    indicator_features = compute_time_series_features(df, imputed_year_values, raw_year_values, year_lookup)
    long_df = reshape_to_long_format(df, year_columns, indicator_features)
    final_long_df = calculate_yoy_metrics(long_df)
    
    return final_long_df


def extract_indicator_matrix(long_df: pd.DataFrame) -> pd.DataFrame:
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

    return country_year_df[["country_name", "country_code", "year", *RAW_INDICATOR_COLUMNS]]


def calculate_derived_gap_and_share_metrics(country_year_df: pd.DataFrame) -> pd.DataFrame:
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
    
    return country_year_df


def calculate_composite_scores(country_year_df: pd.DataFrame) -> pd.DataFrame:
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

    return country_year_df


def build_country_year_dataset(long_df: pd.DataFrame) -> pd.DataFrame:
    country_year_df = extract_indicator_matrix(long_df)
    country_year_df = calculate_derived_gap_and_share_metrics(country_year_df)
    country_year_df = calculate_composite_scores(country_year_df)
    
    country_year_df = country_year_df.sort_values(["country_code", "year"]).reset_index(drop=True)
    return country_year_df[COUNTRY_YEAR_OUTPUT_COLUMNS]

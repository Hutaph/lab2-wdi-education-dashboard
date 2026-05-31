from pathlib import Path
import re

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = ROOT_DIR / "data" / "Data.csv"
OUTPUT_DIR = ROOT_DIR / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "wdi_education_preprocessed.csv"
COUNTRY_YEAR_OUTPUT_PATH = OUTPUT_DIR / "wdi_education_country_year.csv"

MISSING_VALUES = ["..", "", " "]
ID_COLUMNS = ["Country Name", "Country Code", "Series Name", "Series Code"]
MAX_ANALYSIS_YEAR = 2024
INDICATOR_COLUMN_MAP = {
    "SE.PRM.ENRR": "school_enrollment_primary",
    "SE.SEC.ENRR": "school_enrollment_secondary",
    "SE.TER.ENRR": "school_enrollment_tertiary",
    "SE.PRM.CMPT.ZS": "primary_completion_rate",
    "SE.SEC.CMPT.LO.ZS": "lower_secondary_completion_rate",
    "SE.ADT.LITR.ZS": "literacy_rate",
    "SE.XPD.TOTL.GD.ZS": "government_expenditure_education_gdp",
    "SE.XPD.TOTL.GB.ZS": "government_expenditure_education_gov",
    "SE.XPD.SECO.PC.ZS": "government_expenditure_per_student_secondary",
    "SE.PRM.UNER": "children_out_of_school_total",
    "SE.PRM.UNER.FE": "children_out_of_school_female",
    "SE.PRM.UNER.MA": "children_out_of_school_male",
    "SE.ENR.PRSC.FM.ZS": "gender_parity_index",
    "NY.GDP.PCAP.CD": "gdp_per_capita",
    "SP.DYN.LE00.IN": "life_expectancy",
    "SP.URB.TOTL.IN.ZS": "urban_population",
    "SP.POP.TOTL": "population",
}

RAW_INDICATOR_COLUMNS = list(INDICATOR_COLUMN_MAP.values())

LONG_OUTPUT_COLUMNS = [
    "country_name",
    "country_code",
    "series_name",
    "series_code",
    "year_column",
    "value",
    "year",
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
    "previous_value",
    "yoy_change",
    "yoy_change_pct",
    "is_value_available",
    "is_latest_year_with_value",
    "decade",
    "period_5y",
]

COUNTRY_YEAR_OUTPUT_COLUMNS = [
    "country_name",
    "country_code",
    "year",
    "school_enrollment_primary",
    "school_enrollment_secondary",
    "school_enrollment_tertiary",
    "primary_completion_rate",
    "lower_secondary_completion_rate",
    "literacy_rate",
    "government_expenditure_education_gdp",
    "government_expenditure_education_gov",
    "government_expenditure_per_student_secondary",
    "children_out_of_school_total",
    "children_out_of_school_female",
    "children_out_of_school_male",
    "gender_parity_index",
    "gdp_per_capita",
    "life_expectancy",
    "urban_population",
    "population",
    "available_indicator_count",
    "missing_indicator_count",
    "data_completeness_pct",
    "primary_secondary_enrollment_gap",
    "secondary_tertiary_enrollment_gap",
    "completion_gap_primary_lower_secondary",
    "out_of_school_gender_gap",
    "out_of_school_female_share",
    "out_of_school_male_share",
    "out_of_school_per_100k_population",
    "gdp_per_capita_log",
    "population_log",
    "gender_parity_score",
    "education_access_score",
    "development_context_score",
]

SMOOTH_CONTEXT_CODES = {
    "SP.POP.TOTL",
    "SP.DYN.LE00.IN",
    "SP.URB.TOTL.IN.ZS",
}

EDUCATION_RATE_CODES = {
    "SE.PRM.ENRR",
    "SE.SEC.ENRR",
    "SE.TER.ENRR",
    "SE.PRM.CMPT.ZS",
    "SE.SEC.CMPT.LO.ZS",
    "SE.ENR.PRSC.FM.ZS",
}

FINANCE_CODES = {
    "SE.XPD.TOTL.GD.ZS",
    "SE.XPD.TOTL.GB.ZS",
    "SE.XPD.SECO.PC.ZS",
}

OUT_OF_SCHOOL_CODES = {
    "SE.PRM.UNER",
    "SE.PRM.UNER.FE",
    "SE.PRM.UNER.MA",
}

LITERACY_CODES = {"SE.ADT.LITR.ZS"}


def classify_indicator(series_name: str) -> pd.Series:
    name = str(series_name).lower()

    if "expenditure" in name:
        category = "education_finance"
    elif "gdp" in name:
        category = "economy"
    elif "life expectancy" in name:
        category = "health"
    elif "population" in name and "urban" not in name:
        category = "demography"
    elif "urban population" in name:
        category = "urbanization"
    elif "literacy" in name:
        category = "literacy"
    elif "completion" in name:
        category = "completion"
    elif "out of school" in name:
        category = "out_of_school"
    elif "enrollment" in name:
        category = "enrollment"
    else:
        category = "other"

    if "primary and secondary" in name:
        level = "primary_secondary"
    elif "lower secondary" in name:
        level = "lower_secondary"
    elif "secondary" in name:
        level = "secondary"
    elif "primary" in name:
        level = "primary"
    elif "tertiary" in name:
        level = "tertiary"
    elif "adult" in name:
        level = "adult"
    else:
        level = "not_applicable"

    if "female" in name:
        gender = "female"
    elif "male" in name:
        gender = "male"
    else:
        gender = "total"

    if "gender parity index" in name or "(gpi)" in name:
        unit = "index"
    elif "% of" in name or "(%" in name:
        unit = "percent"
    elif "current us$" in name:
        unit = "current_usd"
    elif "years" in name:
        unit = "years"
    elif "population" in name or "children out of school" in name:
        unit = "people"
    else:
        unit = "value"

    return pd.Series(
        {
            "indicator_category": category,
            "education_level": level,
            "gender": gender,
            "metric_unit": unit,
        }
    )


def trend_direction(change):
    if pd.isna(change):
        return "unknown"
    if change > 0:
        return "up"
    if change < 0:
        return "down"
    return "flat"


def get_year_from_column(column_name: str) -> int:
    return int(re.search(r"\d{4}", column_name).group())


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


def impute_time_series(values: pd.Series, year_lookup: dict, rule: dict) -> tuple[pd.Series, pd.Series]:
    result = values.astype("float64").copy()
    methods = pd.Series(pd.NA, index=values.index, dtype="object")

    if result.notna().sum() < 2:
        return result, methods

    years = pd.Index([year_lookup[col] for col in values.index])
    if rule["transform"] == "log1p":
        working_values = np.log1p(result.clip(lower=0))
    else:
        working_values = result.copy()

    working_series = pd.Series(working_values.to_numpy(), index=years, dtype="float64")
    interpolated = working_series.interpolate(method="index", limit_area="inside")

    if rule["transform"] == "log1p":
        interpolated_values = np.expm1(interpolated)
    else:
        interpolated_values = interpolated

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
    if rule["transform"] == "log1p":
        working_values = np.log1p(result.clip(lower=0))
    else:
        working_values = result.copy()

    working_series = pd.Series(working_values.to_numpy(), index=years, dtype="float64")
    filled = working_series.interpolate(method="index", limit_direction="both")

    if rule["transform"] == "log1p":
        result = pd.Series(np.expm1(filled).to_numpy(), index=values.index, dtype="float64")
    else:
        result = pd.Series(filled.to_numpy(), index=values.index, dtype="float64")

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


def derive_out_of_school_components(
    df: pd.DataFrame,
    values: pd.DataFrame,
    methods: pd.DataFrame,
    year_columns: list[str],
) -> None:
    code_to_method = {
        "SE.PRM.UNER": "derived_from_gender_components",
        "SE.PRM.UNER.FE": "derived_from_total_and_male",
        "SE.PRM.UNER.MA": "derived_from_total_and_female",
    }

    for _, group in df[df["Series Code"].isin(OUT_OF_SCHOOL_CODES)].groupby("Country Code"):
        index_by_code = {
            row["Series Code"]: idx
            for idx, row in group.iterrows()
        }

        if not OUT_OF_SCHOOL_CODES.issubset(index_by_code):
            continue

        total_idx = index_by_code["SE.PRM.UNER"]
        female_idx = index_by_code["SE.PRM.UNER.FE"]
        male_idx = index_by_code["SE.PRM.UNER.MA"]

        for col in year_columns:
            total = values.at[total_idx, col]
            female = values.at[female_idx, col]
            male = values.at[male_idx, col]

            if pd.isna(total) and pd.notna(female) and pd.notna(male):
                values.at[total_idx, col] = max(female + male, 0)
                methods.at[total_idx, col] = code_to_method["SE.PRM.UNER"]

            total = values.at[total_idx, col]
            female = values.at[female_idx, col]
            male = values.at[male_idx, col]

            if pd.isna(female) and pd.notna(total) and pd.notna(male):
                values.at[female_idx, col] = max(total - male, 0)
                methods.at[female_idx, col] = code_to_method["SE.PRM.UNER.FE"]

            total = values.at[total_idx, col]
            female = values.at[female_idx, col]
            male = values.at[male_idx, col]

            if pd.isna(male) and pd.notna(total) and pd.notna(female):
                values.at[male_idx, col] = max(total - female, 0)
                methods.at[male_idx, col] = code_to_method["SE.PRM.UNER.MA"]


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


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return (numerator / denominator.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(0)


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


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    long_df = build_dataset()
    country_year_df = build_country_year_dataset(long_df)

    long_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    country_year_df.to_csv(COUNTRY_YEAR_OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved long enriched dataset: {OUTPUT_PATH} {long_df.shape}")
    print(f"Saved country-year dataset: {COUNTRY_YEAR_OUTPUT_PATH} {country_year_df.shape}")


if __name__ == "__main__":
    main()

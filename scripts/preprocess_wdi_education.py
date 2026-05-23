from pathlib import Path
import re

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = ROOT_DIR / "data" / "Data.csv"
OUTPUT_DIR = ROOT_DIR / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "wdi_education_preprocessed.csv"

MISSING_VALUES = ["..", "", " "]
ID_COLUMNS = ["Country Name", "Country Code", "Series Name", "Series Code"]


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


def build_dataset() -> pd.DataFrame:
    df = pd.read_csv(RAW_DATA_PATH, na_values=MISSING_VALUES)
    df = df.dropna(how="all")

    valid_country_code = df["Country Code"].astype("string").str.fullmatch(r"[A-Z]{3}", na=False)
    df = df[valid_country_code & df["Series Code"].notna()].copy()

    year_columns = [col for col in df.columns if re.fullmatch(r"\d{4} \[YR\d{4}\]", col)]
    year_lookup = {col: int(re.search(r"\d{4}", col).group()) for col in year_columns}

    for col in ID_COLUMNS:
        df[col] = df[col].astype("string").str.strip()

    for col in year_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    feature_df = df["Series Name"].apply(classify_indicator)
    year_stats = df[year_columns]

    available_year_count = year_stats.notna().sum(axis=1)
    missing_year_count = year_stats.isna().sum(axis=1)

    first_year = []
    latest_year = []
    first_value = []
    latest_value = []

    for _, row in year_stats.iterrows():
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
    indicator_features["pct_change_since_first"] = (
        indicator_features["change_since_first"]
        / indicator_features["first_value"].replace(0, pd.NA)
        * 100
    )
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
    long_df["yoy_change_pct"] = long_df["yoy_change"] / long_df["previous_value"].replace(0, pd.NA) * 100
    long_df["is_value_available"] = long_df["value"].notna()
    long_df["is_latest_year_with_value"] = (
        long_df["latest_year_with_value"].notna()
        & long_df["year"].eq(long_df["latest_year_with_value"].astype("Int64"))
    )
    long_df["decade"] = (long_df["year"] // 10 * 10).astype(str) + "s"
    long_df["period_5y"] = ((long_df["year"] - 2001) // 5 * 5 + 2001).astype(str) + "-" + (
        (long_df["year"] - 2001) // 5 * 5 + 2005
    ).astype(str)

    return long_df


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    long_df = build_dataset()
    long_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved dashboard dataset: {OUTPUT_PATH} {long_df.shape}")


if __name__ == "__main__":
    main()

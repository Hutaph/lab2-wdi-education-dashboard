import re
import numpy as np
import pandas as pd

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


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return (numerator / denominator.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(0)

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
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

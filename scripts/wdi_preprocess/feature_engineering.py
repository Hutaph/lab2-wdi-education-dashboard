import pandas as pd
from .config import OUT_OF_SCHOOL_CODES

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

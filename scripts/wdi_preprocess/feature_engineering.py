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
        index_by_code = {row["Series Code"]: idx for idx, row in group.iterrows()}

        if not OUT_OF_SCHOOL_CODES.issubset(index_by_code):
            continue

        total_idx = index_by_code["SE.PRM.UNER"]
        female_idx = index_by_code["SE.PRM.UNER.FE"]
        male_idx = index_by_code["SE.PRM.UNER.MA"]

        totals = values.loc[total_idx, year_columns]
        females = values.loc[female_idx, year_columns]
        males = values.loc[male_idx, year_columns]

        mask_t = totals.isna() & females.notna() & males.notna()
        if mask_t.any():
            filled_t = (females[mask_t] + males[mask_t]).clip(lower=0)
            values.loc[total_idx, mask_t.index[mask_t]] = filled_t
            methods.loc[total_idx, mask_t.index[mask_t]] = code_to_method["SE.PRM.UNER"]

        totals = values.loc[total_idx, year_columns]
        
        mask_f = females.isna() & totals.notna() & males.notna()
        if mask_f.any():
            filled_f = (totals[mask_f] - males[mask_f]).clip(lower=0)
            values.loc[female_idx, mask_f.index[mask_f]] = filled_f
            methods.loc[female_idx, mask_f.index[mask_f]] = code_to_method["SE.PRM.UNER.FE"]

        females = values.loc[female_idx, year_columns]
        
        mask_m = males.isna() & totals.notna() & females.notna()
        if mask_m.any():
            filled_m = (totals[mask_m] - females[mask_m]).clip(lower=0)
            values.loc[male_idx, mask_m.index[mask_m]] = filled_m
            methods.loc[male_idx, mask_m.index[mask_m]] = code_to_method["SE.PRM.UNER.MA"]


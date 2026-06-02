import sys
from pathlib import Path

# Add the parent directory to sys.path if needed
# Actually, since wdi_preprocess is inside scripts, and we run python scripts/preprocess_wdi_education.py
# it is resolvable if we use absolute import or add scripts to path.
# Assuming running from the root of the project, 'scripts' is a folder.
# We can do:
from wdi_preprocess.config import OUTPUT_DIR, OUTPUT_PATH, COUNTRY_YEAR_OUTPUT_PATH
from wdi_preprocess.data_processing import build_dataset, build_country_year_dataset

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

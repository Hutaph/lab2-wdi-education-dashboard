from wdi_preprocess.config import (
    COUNTRY_YEAR_OUTPUT_FILE,
    LONG_OUTPUT_FILE,
    METADATA_FILE,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    RAW_DATA_FILE,
)
from wdi_preprocess.data_processing import build_dataset, build_country_year_dataset


def validate_input_files() -> None:
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Raw data directory not found: {RAW_DATA_DIR}")

    missing_files = [path for path in (RAW_DATA_FILE, METADATA_FILE) if not path.exists()]
    if missing_files:
        missing_list = "\n".join(f"- {path}" for path in missing_files)
        raise FileNotFoundError(f"Missing required raw data file(s):\n{missing_list}")


def main() -> None:
    validate_input_files()
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    long_df = build_dataset()
    country_year_df = build_country_year_dataset(long_df)

    long_df.to_csv(LONG_OUTPUT_FILE, index=False, encoding="utf-8-sig", lineterminator="\r\n")
    country_year_df.to_csv(COUNTRY_YEAR_OUTPUT_FILE, index=False, encoding="utf-8-sig", lineterminator="\r\n")

    print(f"Saved long enriched dataset: {LONG_OUTPUT_FILE} {long_df.shape}")
    print(f"Saved country-year dataset: {COUNTRY_YEAR_OUTPUT_FILE} {country_year_df.shape}")

if __name__ == "__main__":
    main()

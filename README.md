# WDI Education Dashboard

Project xử lý dữ liệu World Development Indicators (WDI) về giáo dục để phục vụ dashboard phân tích các quốc gia Đông Nam Á.

## Chạy preprocessing

Từ thư mục gốc của project, chạy:

```bash
python scripts/preprocess_wdi_education.py
```

Notebook giải thích quá trình xử lý dữ liệu:

```text
notebooks/preprocessing_wdi_education.ipynb
```

## Dữ liệu đầu ra

Các file sau xử lý nằm trong thư mục `data/processed/`:

- `wdi_education_preprocessed.csv`: dữ liệu dạng long, mỗi dòng là một quốc gia, một năm và một chỉ số.
- `wdi_education_country_year.csv`: dữ liệu dạng wide, mỗi dòng là một quốc gia và một năm.

## Cách chọn file

| Nhu cầu | File nên dùng |
|---|---|
| Vẽ xu hướng theo thời gian | `wdi_education_preprocessed.csv` |
| Lọc theo quốc gia, năm hoặc chỉ số | `wdi_education_preprocessed.csv` |
| So sánh nhiều chỉ số trong cùng một năm | `wdi_education_country_year.csv` |
| Vẽ scatter plot hoặc bubble chart | `wdi_education_country_year.csv` |
| Tạo country profile hoặc dashboard tổng hợp | `wdi_education_country_year.csv` |

## Lưu ý

- Gross enrollment có thể lớn hơn 100 vì bao gồm cả người học không thuộc đúng độ tuổi chính thức.
- Các chỉ số `children_out_of_school_*` là số lượng tuyệt đối, nên cần xem cùng bối cảnh dân số.
- Biểu đồ so sánh chi tiêu và kết quả giáo dục chỉ thể hiện mối liên hệ quan sát được, không chứng minh quan hệ nhân quả.
- Các cột `education_access_score`, `development_context_score` và `gender_parity_score` là feature do project tạo thêm, không phải chỉ số chính thức của WDI.

# Lab 02: Khai thác và trực quan hóa dữ liệu bằng Tableau
**Môn học:** Trực Quan Hóa Dữ Liệu CQ2023/24 - VNU-HCMUS

## 1. Giới thiệu đồ án
World Development Indicators (WDI) là một nguồn dữ liệu do Ngân hàng Thế giới (World Bank) cung cấp, tập trung vào các chỉ số phát triển toàn cầu. Dữ liệu bao gồm thông tin từ hơn 200 quốc gia trên toàn cầu, trải dài qua nhiều năm với đa dạng các khía cạnh.

Thông qua việc khai thác và phân tích dữ liệu này, đồ án hướng đến mục tiêu trình bày các xu hướng phát triển, khám phá mối quan hệ giữa các chỉ số, và làm rõ các vấn đề nổi bật về giáo dục, kinh tế, và các khía cạnh phát triển xã hội khác ở các quốc gia.

## 2. Cấu trúc thư mục
```text
lab2-wdi-education-dashboard
 ┣ data
 ┃ ┣ processed/      # Dữ liệu đầu ra sau khi chạy script (CSV)
 ┃ ┣ Data.csv        # Dữ liệu thô (Raw data) tải từ World Bank
 ┃ ┗ Data_Metadata.csv
 ┣ notebooks/        # Jupyter Notebooks khám phá dữ liệu & giải thích quy trình
 ┣ scripts/          # Mã nguồn tiền xử lý dữ liệu (đã được cấu trúc hoá theo chuẩn)
 ┃ ┣ wdi_preprocess/ # Package chứa core logic (config, imputation, features...)
 ┃ ┗ preprocess_wdi_education.py # Script chính để khởi chạy pipeline
 ┣ tableau/          # Các tệp Tableau Workbook (.twbx) đã làm
 ┣ README.md         # File README
```

## 3. Hướng dẫn chạy Tiền xử lý dữ liệu (Data Preprocessing)
Phần tiền xử lý dữ liệu sử dụng thư viện `pandas` và `numpy` trong Python để làm sạch, nội suy (impute) dữ liệu thiếu, biến đổi định dạng cấu trúc, và tính toán thêm các metrics phái sinh (Feature Engineering).

Từ thư mục gốc của project, mở Terminal/Command Prompt và chạy lệnh sau:
```bash
python scripts/preprocess_wdi_education.py
```

Các file sau xử lý sẽ tự động được lưu vào thư mục `data/processed/`:
- `wdi_education_preprocessed.csv`: dữ liệu dạng long (hẹp dọc), dùng để vẽ biểu đồ xu hướng theo thời gian, lọc theo quốc gia/năm một cách dễ dàng.
- `wdi_education_country_year.csv`: dữ liệu dạng wide (rộng ngang), mỗi dòng là một quốc gia ở một năm cụ thể kèm theo tất cả các chỉ số. Dùng tốt nhất cho biểu đồ scatter, bubble, hoặc lấy data tổng hợp cho Dashboard.

*(Tham khảo file Notebook giải thích chi tiết quá trình thăm dò và quyết định mô hình dữ liệu: `notebooks/preprocessing_wdi_education.ipynb`)*

## 4. Trực quan hóa dữ liệu (Tableau)
Toàn bộ phần trực quan hóa và xây dựng Dashboard phân tích được thực hiện duy nhất bằng công cụ **Tableau**. 
- **Dữ liệu đầu vào:** Các file kết quả CSV lấy từ thư mục `data/processed/` sau khi chạy Python.
- **Bản trình bày:** Nằm trong thư mục `tableau/` dưới định dạng `.twbx` (Tableau Packaged Workbook - đã nhúng kèm data).
- **Tính tương tác:** Dashboard được thiết kế đáp ứng các tiêu chí tương tác cơ bản qua các bộ lọc (Filter), Selector/Dropdown và Dashboard Actions (highlight, filter chéo) nhằm cung cấp cái nhìn rõ ràng và cho phép người dùng tự do khám phá dữ liệu.

## 5. Các liên kết liên quan (Links)
- **Video 1 - Giới thiệu công cụ Tableau:** [Chèn Link YouTube Unlisted]
- **Video 2 - Trình bày quá trình phân tích:** [Chèn Link YouTube Unlisted]

## 6. Các lưu ý về Dữ liệu và Bản quyền
- Các chỉ số `education_access_score`, `development_context_score` và `gender_parity_score` là các feature do nhóm tự tổng hợp tính toán thêm phục vụ mục tiêu đánh giá tổng quan, không phải chỉ số gốc của WDI.
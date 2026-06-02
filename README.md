# Lab 02: Khai thác và trực quan hóa dữ liệu bằng Tableau
**Môn học:** Trực Quan Hóa Dữ Liệu CQ2023/24 - VNU-HCMUS

## 1. Giới thiệu đồ án
World Development Indicators (WDI) là một nguồn dữ liệu do Ngân hàng Thế giới (World Bank) cung cấp, tập trung vào các chỉ số phát triển toàn cầu. Dữ liệu bao gồm thông tin từ hơn 200 quốc gia trên toàn cầu, trải dài qua nhiều năm với đa dạng các khía cạnh.

Thông qua việc khai thác và phân tích dữ liệu này, đồ án hướng đến mục tiêu trình bày các xu hướng phát triển, khám phá mối quan hệ giữa các chỉ số, và làm rõ các vấn đề nổi bật về giáo dục, kinh tế, và các khía cạnh phát triển xã hội khác ở các quốc gia.

## 2. Cấu trúc thư mục
```text
.
├── README.md
├── requirements.txt
├── data
│   ├── raw
│   │   ├── wdi_education_raw.csv
│   │   └── wdi_education_metadata.csv
│   └── processed
│       ├── wdi_education_country_year.csv
│       └── wdi_education_preprocessed.csv
├── notebooks
│   ├── data_exploration.ipynb
│   └── preprocessing_wdi_education.ipynb
├── scripts
│   ├── preprocess_wdi_education.py
│   └── wdi_preprocess
│       ├── __init__.py
│       ├── config.py
│       ├── data_processing.py
│       ├── feature_engineering.py
│       ├── imputation.py
│       └── utils.py
└── tableau
    └── dashboard_final.twbx
```

Vai trò các thư mục chính:
- `data/raw/`: dữ liệu WDI gốc và metadata, gồm `wdi_education_raw.csv` và `wdi_education_metadata.csv`.
- `data/processed/`: dữ liệu đã xử lý để dùng trong Tableau, gồm `wdi_education_preprocessed.csv` và `wdi_education_country_year.csv`.
- `notebooks/`: notebook EDA và kiểm tra quy trình preprocessing.
- `scripts/`: pipeline tiền xử lý có thể chạy lại.
- `tableau/dashboard_final.twbx`: workbook Tableau tổng hợp cuối cùng của dashboard.

## 3. Cài đặt môi trường và chạy project

Project sử dụng Python để EDA, kiểm tra dữ liệu và chạy pipeline tiền xử lý; Tableau được dùng để xây dựng dashboard.

### 3.1. Clone project
```bash
git clone https://github.com/Hutaph/lab2-wdi-education-dashboard.git
cd lab2-wdi-education-dashboard
```

### 3.2. Tạo môi trường ảo
Trên Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Trên Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3.3. Cài dependencies
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3.4. Chạy tiền xử lý dữ liệu
Phần tiền xử lý dữ liệu sử dụng `pandas` và `numpy` để làm sạch, nội suy (impute) dữ liệu thiếu, biến đổi định dạng cấu trúc, và tính toán thêm các metrics phái sinh (Feature Engineering).

Từ thư mục gốc của project, mở Terminal/Command Prompt và chạy lệnh sau:
```bash
python scripts/preprocess_wdi_education.py
```

Input chính:
- `data/raw/wdi_education_raw.csv`
- `data/raw/wdi_education_metadata.csv`

Output sau xử lý sẽ tự động được lưu vào:
- `data/processed/wdi_education_preprocessed.csv`: dữ liệu dạng long (hẹp dọc), dùng để vẽ biểu đồ xu hướng theo thời gian, lọc theo quốc gia/năm một cách dễ dàng.
- `data/processed/wdi_education_country_year.csv`: dữ liệu dạng wide (rộng ngang), mỗi dòng là một quốc gia ở một năm cụ thể kèm theo tất cả các chỉ số. Dùng tốt nhất cho biểu đồ scatter, bubble, hoặc lấy data tổng hợp cho Dashboard.

Các notebook chính:
- `notebooks/data_exploration.ipynb`: khám phá dữ liệu raw, phân tích missing values và thống kê mô tả.
- `notebooks/preprocessing_wdi_education.ipynb`: kiểm tra dữ liệu processed, schema và các ràng buộc chất lượng dữ liệu.

## 4. Trực quan hóa dữ liệu (Tableau)
Toàn bộ phần trực quan hóa và xây dựng Dashboard phân tích được thực hiện duy nhất bằng công cụ **Tableau**. 
- **Dữ liệu đầu vào:** Các file kết quả CSV lấy từ thư mục `data/processed/` sau khi chạy Python.
- **Bản trình bày:** File `tableau/dashboard_final.twbx` dưới định dạng Tableau Packaged Workbook, đã nhúng kèm data.
- **Tableau Public:** https://public.tableau.com/app/profile/phat.truong1395/viz/Q4_17796927321620/Dashboard_final?publish=yes
- **Tính tương tác:** Dashboard được thiết kế đáp ứng các tiêu chí tương tác cơ bản qua các bộ lọc (Filter), Selector/Dropdown và Dashboard Actions (highlight, filter chéo) nhằm cung cấp cái nhìn rõ ràng và cho phép người dùng tự do khám phá dữ liệu.

Để xem dashboard offline, mở `tableau/dashboard_final.twbx` bằng Tableau Desktop hoặc Tableau Public.

## 5. Demo Videos
- Video 1: https://youtu.be/wIwoXPDqe2E
- Video 2: https://youtu.be/mezGXTf7BWI

## 6. Các lưu ý về dữ liệu và bản quyền
- Các chỉ số `education_access_score`, `development_context_score` và `gender_parity_score` là các feature do nhóm tự tổng hợp tính toán thêm phục vụ mục tiêu đánh giá tổng quan, không phải chỉ số gốc của WDI.

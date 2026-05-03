# 🚀 Time-Series Query Optimization: Elasticsearch & TimescaleDB

Chào mừng đến với đồ án **Tối ưu hóa Truy vấn Dữ liệu Time-Series**. Dự án này là một bài Benchmark toàn diện so sánh tốc độ truy vấn (Latency) giữa cấu trúc lõi của **Elasticsearch (Must vs Filter Cache)** và **TimescaleDB (Hypertable)** với quy mô hàng triệu bản ghi giả lập của dữ liệu GPS phương tiện.

## 📂 Kiến Trúc Mã Nguồn (Directory Structure)

Dự án đã được module hoá bài bản để vừa có thể chạy Script ngầm, vừa trực quan hoá trên giao diện Web UI. Dưới đây là ý nghĩa của từng tệp cốt lõi:

### 1. Phân Hệ Trực Quan (Web Dashboard)
- `app.py`: Trái tim của dự án – Đây là giao diện **Streamlit Web Dashboard**. Ứng dụng này sẽ gọi trực tiếp truy vấn vào hệ CSDL của Elastic Cloud và Aiven, tính toán độ phản hồi (P95 Latency), sau đó minh hoạ rõ rệt bằng các thẻ Metric % (Delta improvement) và biểu đồ đồ họa so sánh trực tiếp.

### 2. Phân Hệ Vận Hành & Khởi Tạo (Pipeline / Script)
- `config.py`: File trung gian chịu trách nhiệm tự động nạp (load) các khoá bảo mật tài khoản CSDL từ file `.env` lên biến môi trường, bảo vệ thông tin vĩnh viễn khỏi Git.
- `scripts/generate_and_ingest_es.py`: Script sử dụng API `helpers.bulk()` đẩy mạnh **10M** bản ghi ngẫu nhiên (Mock Data) thẳng lên Cloud của Elasticearch nhằm giả lập hệ thống IoT Tracking dày đặc. Đi kèm là Giao diện Terminal theo dõi tiến trình siêu đẹp bằng thư viện `rich`.
- `scripts/generate_and_ingest_ts.py`: Tương tự như ES, nhưng dành riêng để cấu hình và đẩy **2M** bản ghi lên chuẩn **Postgres Hypertable** của TimescaleDB (Aiven Cloud).

### 3. Phân Hệ Đánh Giá (Benchmark Logging)
- `scripts/benchmark_es.py`: Tập lệnh chạy giả lập đo đạc dành riêng cho mảng Elasticsearch (So chi tiết). File này có khả năng tự xuất kết quả ra file `results/baseline_es.csv` phục vụ cho việc nhúng số liệu lên file Word/Slide báo cáo bảo vệ đồ án.

### 4. Phân Hệ Tài Liệu (Documentation)
- **Thư mục `excutive/`**: Chứa toàn bộ các kế hoạch, hướng dẫn triển khai nền tảng Cloud (`cloud_setup_guide.md`) cũng như hướng dẫn cấu trúc một bài báo cáo 10-20 trang cực kì đa dạng và chi tiết để trình bày bảo vệ trước hội đồng môn (`guide_viet_bao_cao_A4.md`).

---

## 🛠 Hướng Dẫn Chạy & Khởi Động

**Bước 1: Mở môi trường ảo (Bắt buộc)**
Khởi động không gian làm việc an toàn của Python đã được cài sẵn bộ thư viện.
```bash
source venv/bin/activate
```

**Bước 2: Mở Giao diện Web Đo đạc Hiệu Năng (Dashboard)**
```bash
streamlit run app.py
```
> Web sẽ mở cổng tại địa chỉ `http://localhost:8501`. Mở trình duyệt lên và bấm "Bắt Đầu Chạy Benchmark Tổng Hợp".

**Bước 3: (Optional) Chạy bơm thủ công thêm bản ghi**
Nếu hết dữ liệu hoặc muốn reset CSDL:
```bash
python3 scripts/generate_and_ingest_es.py
python3 scripts/generate_and_ingest_ts.py
```

---
**🏆 Tác giả:** Phạm Nhật Linh (Học phần Cơ sở Dữ liệu Nâng cao)

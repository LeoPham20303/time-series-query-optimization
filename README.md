# 🚀 Lõi Dự Án: Benchmark Tối Ưu Hoá Truy Vấn Time-Series (GPS Tracking)

Chào mừng bạn đến với Repository của Đồ án **Đánh giá và Tối ưu hoá hiệu năng thao tác dữ liệu Thời gian thực**. 
Dự án cung cấp một hệ sinh thái mã nguồn khép kín từ khâu sinh dữ liệu giả lập (Data Generator) đến Giao diện đo lường trực quan (Dashboard), nhằm chứng minh sự chênh lệch hiệu năng giữa **Elasticsearch 8.x** và **TimescaleDB (PostgreSQL)**, phân tách rạch ròi lý thuyết Query Scoring vs Bitmap Caching.

---

## 🌟 1. Thành quả đã đạt được trong hệ thống
Mã nguồn này nắm giữ 3 thành tựu lớn nhất mà tụi mình đã xây dựng:
1. **Pumping Pipeline siêu tốc:** Sử dụng Bulk API (`helpers.streaming_bulk`) và Muti-Insert (`execute_values`) đẩy hàng vạn Log một giây.
2. **Dashboard Streamlit đa năng:** Đo lường tự động (P95 Latency) hiển thị biểu đồ + Trình quản lý Data Explorer trực tiếp không qua phần mềm thứ 3.
3. **Báo cáo Khoa Học sẵn sàng:** Tệp `THESIS_REPORT_COMPLETE.md` với 7.000 chữ giải phẫu từ B-Tree của PostgreSQL đến BKD Tree của ElasticCloud.

## 📁 2. Bản đồ cấu trúc thư mục
* `app.py` 🎯: Trái tim của dự án (Giao diện Web đo lường hiệu năng).
* `config.py` & `.env`: Không gian cấu hình mốc URL Cloud ẩn giấu (Bảo mật).
* `scripts/generate_and_ingest_es.py`: Script tự động gọt phẳng Elastic cũ và bơm mới lượng lớn (Scale to 426k) logs GPS.
* `scripts/generate_and_ingest_ts.py`: Script sinh dữ liệu cho TimescaleDB Aiven.
* `THESIS_REPORT_COMPLETE.md`: Bản Draft báo cáo dài 20 trang để xài copy chắp nối vào Word thuyết trình!

---

## ⚙️ 3. Hướng dẫn Partner Cài đặt & Chạy trên máy ở nhà

> **Lưu ý Cực Kỳ Quan Trọng:** Vì tính bảo mật, tụi mình không đẩy mật khẩu Lên Github. Hãy liên hệ Leader để lấy mã trong file `.env` dán vào máy của bạn nhé!

### 🔧 Bước 3.1: Thiết lập Hệ Sinh Thái Python (Mất 1 phút)
Yêu cầu máy phải có sẵn `Python 3.9+`. Mở Terminal (MacOS/Linux) hoặc CMD (Windows) ở ngay thư mục chứa Code:
```bash
# 1. Tạo môi trường ảo ảo hóa
python3 -m venv venv

# 2. Kích hoạt môi trường (Dành cho MacOS / Linux)
source venv/bin/activate
# (Nếu xài Windows, xài lệnh này: venv\Scripts\activate)

# 3. Nạp bộ thư viện đầy đủ
pip install -r requirements.txt
```

### 🔧 Bước 3.2: Tạo File .env (Dấu diếm Key)
Tại thư mục gốc dự án, tạo file tên là `.env` và coppy bộ key tụi mình cho vào như form dưới đây:
```env
ES_URL=https://<your_host>.es.io:443
ES_USER=elastic
ES_PASSWORD=<super_secret>

PG_URI=postgres://avnadmin:<super_secret>@<your_aiven_host>/defaultdb?sslmode=require
```

---

## 🚀 4. Trải nghiệm Dự Án Mượt Mà

**A. Giao diện trực quan Website Streamlit (Quan Trọng Nhất)**
Đảm bảo bạn đã Activate `venv`, đánh lệnh này:
```bash
streamlit run app.py
```
Trình duyệt sẽ tự mở port `http://localhost:8501`. Tất cả thành quả đo đạc đều được show tại đây. Chụp ảnh màn hình này bỏ vào slide Powerpoint!

**B. Khôi phục / Tạo mới Dữ liệu (Reset Cloud)**
Trong trường hợp Giáo viên chấm thi muốn xoá toàn bộ Database và tự nhìn code chạy ra dữ liệu 400.000 dòng lại từ đầu, hãy thả 2 quả Script này:
```bash
python scripts/generate_and_ingest_es.py
```
*(Chờ chạy xong thì bật tiếp Timescale nếu cần qua file ts.py).*

Đơn giản vậy đó, chúc tụi mình qua Đồ Án Nhẹ Nhàng 10 Điểm Nhen! 🔥

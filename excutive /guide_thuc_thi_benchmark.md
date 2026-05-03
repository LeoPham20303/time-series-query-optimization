# CẨM NANG THỰC THI & ĐO ĐẠC ĐỒ ÁN (BẢN TINH GỌN MÁY CÁ NHÂN)

Tài liệu này cung cấp các bước nhỏ nhất, gọn nhẹ nhất để bạn đi đến kết quả cuối cùng mà không làm treo máy tính cá nhân.

## LỰA CHỌN NỀN TẢNG (Chọn 1 trong 2)
### Lựa chọn A: Dùng máy cá nhân (Local) - Khuyên dùng nếu máy RAM >= 16GB
Sử dụng bản 1 Node duy nhất.
- Tải [Docker Desktop](https://www.docker.com/products/docker-desktop/).
- Tạo `docker-compose.yml` cực nhẹ:
```yaml
version: '3.8'
services:
  es-node:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.2
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms2g -Xmx2g
    ports:
      - "9200:9200"
```
- Chạy: `docker-compose up -d`

### Lựa chọn B: Dùng Công cụ Online (Cloud) - Khuyên dùng nếu máy yếu
Thay vì cài trên máy, hãy sử dụng các bản Trial miễn phí (có cloud server sẵn, cấu hình mạnh):
1. **Elasticsearch:** Tạo tài khoản [Elastic Cloud](https://cloud.elastic.co/registration) (Miễn phí 14 ngày, không cần thẻ tín dụng). Copy URL và API Key để cho code python gọi vào.
2. **DynamoDB:** Dùng [AWS DynamoDB Free Tier](https://aws.amazon.com/free) (Cần tạo tài khoản AWS).
3. **TimescaleDB:** Dùng [Aiven for PostgreSQL](https://aiven.io/postgresql) (Có trial miễn phí).

---

## CÁC BƯỚC THỰC THI TỪNG PHẦN (QUY TRÌNH PIPELINE)

### Bước 1: Sinh dữ liệu mô phỏng (Mock Data Generation)
- **Hành động:** Viết script Python (hoặc Node.js) để tạo ra các dòng sự kiện mô phỏng GPS.
- **Tối ưu:** Sinh ra khoảng **2.000.000 dòng** v(viết thẳng ra file `dataset.cs` hoặc `.jsonl`). Đừng xuất 10 triệu dòng, quá nặng để upload/import.
- **Code Gợi ý:** Dùng thư viện `Faker` kết hợp vòng lặp tạo tọa độ random.

### Bước 2: Bơm dữ liệu (Ingestion)
- **Hành động:** Viết script Python đọc `dataset.csv` và dùng `elasticsearch-py` helper `bulk` để bắn dữ liệu lên ES.
- **Tối ưu:** Bơm thẳng vào 1 index duy nhất thay vì 26 index (hoặc lập Data Stream tự chia dữ liệu theo tháng). Đặt `number_of_shards=1`, `number_of_replicas=0`.

### Bước 3: Đo đạc ES chưa Tối ưu (Baseline Benchmark)
- **Hành động:** Viết script `benchmark.py`.
- **Query tồi (Cố tình làm sai):** Trong query, sử dụng block `"must"` chứa các term và range.
- **Đo đạc:**
  ```python
  import time
  start_time = time.time()
  res = es.search(index="gps-events-*", body=bad_query)
  end_time = time.time()
  
  # Ghi nhận vào file kết quả
  client_latency = (end_time - start_time) * 1000
  server_took = res['took']
  # Viết 2 con số này (cùng tên query) ra file results.csv
  ```
- Chạy vòng lặp 50 lần, lấy số trung bình (hoạt chạy percentile để lấy mức P95). Lưu ý có lệnh xóa cache ES `POST /_cache/clear` để đo trường hợp Cold Cache.

### Bước 4: Đo đạc ES ĐÃ Tối ưu (Optimized Benchmark)
- **Hành động:** Sửa lại script ở bước 3 thành truy vấn tốt.
- **Tối ưu:** Đổi block `"must"` thành block `"filter"`. Thực hiện Force Merge Index (`POST /gps-events-*/_forcemerge?max_num_segments=1`).
- Chạy lại bài test đo đạc 50 lần. Trích xuất ra `results.csv`.

### Bước 5: Chạy đối chiếu với hệ khác (DynamoDB/Timescale)
- **Hành động:** Với `dataset.csv` trên, tạo bảng ở DynamoDB/TimescaleDB. 
- Viết lại hàm truy vấn (bằng Python SDK của các DB này) và ghi lại Client Latency. (Cũng vòng lặp đo 50 lần)
- Ghi đè cột vào file `results.csv`.

### KẾT QUẢ CUỐI CÙNG TRONG TAY BẠN
Một file `results.csv` có 4 cột: `Loại Query` | `ES Baseline (ms)` | `ES Optimized (ms)` | `DynamoDB (ms)` | `TimescaleDB (ms)`
Bạn ném file này vào Excel, vẽ 2 cái biểu đồ Bar Chart. Xong phần thực hành!

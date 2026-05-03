# HƯỚNG DẪN CHI TIẾT TRIỂN KHAI ĐỒ ÁN TRÊN CLOUD

Nếu máy tính cấu hình yếu, việc đẩy CSDL lên Cloud là quyết định khôn ngoan nhất. Toàn bộ tính toán, RAM, CPU được xử lý trên máy chủ của bên thứ ba, máy tính của bạn chỉ đóng vai trò "Viết Code" và "Gửi Lệnh Đo Đạc" (gửi Request HTTP).

Dưới đây là các bước chi tiết (thực hành bằng tay) để lấy thông tin kết nối và bộ code mẫu.

## BƯỚC 1: KHỞI TẠO VÀ LẤY THÔNG TIN KẾT NỐI (CREDENTIALS)

### 1.1 Khởi tạo Elasticsearch trên Elastic Cloud
1. Truy cập [cloud.elastic.co](https://cloud.elastic.co/registration) và chọn "Start Free Trial" (đăng nhập bằng Google).
2. Click **Create deployment**. Đặt tên: `gps-events-cluster`.
3. Bạn cứ để cấu hình mặc định (Khu vực AWS/GCP gần nhất, ví dụ Singapore). Bấm **Create**.
4. **⚠️ RẤT QUAN TRỌNG:** Màn hình ngay sau đó sẽ hiện ra thông tin đăng nhập bao gồm `Username` (thường là `elastic`) và một cái `Password` ngẫu nhiên. Hãy copy và lưu mật khẩu này ra Notepad ngay lập tức (vì nó không hiện lại lần 2).
5. Sau khi Deployment chạy xong, bấm vào nút **Manage**. Hãy tìm dòng **Elasticsearch endpoint** (nó là một cái URL dài thò lò, ví dụ: `https://my-deployment.es.ap-southeast-1.aws.elastic-cloud.com`). Copy lại.

-> **Tài sản sau bước này:** Lấy được `ES_URL`, `ES_USER` và `ES_PASSWORD`.

### 1.2 Khởi tạo DynamoDB trên Amazon Web Services (AWS)
1. Đăng nhập [AWS Console](https://console.aws.amazon.com/). (Nếu chưa có tài khoản AWS Free Tier thì nên tạo, cần thẻ visa để verify nhưng không mất phí).
2. Gõ `DynamoDB` trên thanh tìm kiếm và vào đó.
3. Vì chạy qua Code Python, bạn không tạo bảng bằng tay. Cái bạn cần là Quyền truy cập.
4. Gõ `IAM` (Identity and Access Management) trên thanh tìm kiếm AWS.
5. Vào **Users** -> Chọn **Create User** -> Đặt tên: `db_assignment_user`.
6. Ở phần permissions, chọn **Attach policies directly**, tìm và tick vào mục `AmazonDynamoDBFullAccess`. Bấm Next tạo user.
7. Click vào tên user vừa tạo, qua tab **Security credentials**.
8. Kéo xuống phần **Access keys**, bấm **Create access key**. Chọn "Command Line Interface (CLI)". Create.
9. Copy lại `Access key ID` và `Secret access key`.

-> **Tài sản sau bước này:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, và mã vùng của bạn `AWS_REGION` (vd `us-east-1` hoặc `ap-southeast-1`).

### 1.3 Khởi tạo TimescaleDB trên Aiven
1. Tạo account trial trên [Aiven](https://console.aiven.io/signup).
2. Khi vào giao diện, chọn **Create Service** -> Chọn loại CSDL là **PostgreSQL**.
3. Chọn gói rẻ nhất nằm trong Free Trial. Bấm Create.
4. Chờ 1-2 phút cho Service hiển thị màu Xanh (Running). Bấm vào tab **Overview**.
5. Kéo xuống mục **Service URI**. Bấm biểu tượng Copy cái link dài ngoằng dạng `postgres://avnadmin:mat_khau@host_gi_do:port/defaultdb...`.

-> **Tài sản sau bước này:** `PG_URI`.

---

## BƯỚC 2: CẤU HÌNH MÔI TRƯỜNG Ở MÁY CỦA BẠN

Máy tính của bạn giờ chỉ là client gọi API. Hãy tạo dự án Python:

1. Mở Terminal (VSCode):
```bash
python3 -m venv venv
source venv/bin/activate  # (Mac/Linux) 
pip install elasticsearch boto3 psycopg2-binary faker python-dotenv
```

2. Tạo file `.env` chứa toàn bộ bảo mật (đừng bao giờ đẩy file này lên Github):
```env
# ELASTICSEARCH
ES_URL=https://<id>.es.ap-southeast-1.aws.elastic-cloud.com
ES_USER=elastic
ES_PASSWORD=mat_khau_elastic

# DYNAMODB
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=abcd...
AWS_REGION=ap-southeast-1

# TIMESCALEDB
PG_URI=postgres://avnadmin:xyz@pg-service.../defaultdb?sslmode=require
```

---

## BƯỚC 3: MẢNG CODE ĐỂ KẾT NỐI VÀ CHẠY ĐO ĐẠC

Khi làm đồ án, bạn sẽ dùng thư viện Python để móc nối vào những credential ở trên. Đây là sườn Code cơ bản nhất:

### 3.1 Script khởi tạo biến môi trường
Tạo file `config.py` dùng chung:
```python
import os
from dotenv import load_dotenv

load_dotenv()

# ES config
ES_URL = os.getenv("ES_URL")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")

# Dynamo Config
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

# Postgres config
PG_URI = os.getenv("PG_URI")
```

### 3.2 Code Mẫu Elasticsearch: Bơm Data & Query
**File: `es_test.py`**
```python
from elasticsearch import Elasticsearch
import config
import time

# 1. Kết nối lên Cloud
es = Elasticsearch(
    config.ES_URL,
    basic_auth=(config.ES_USER, config.ES_PASSWORD)
)

print(es.info()) # Nếu print ra chữ "You Know, for Search" là thành công!

# 2. Bơm 1 Data Mẫu
es.index(index="gps-events", body={
    "companyId": "C01",
    "assetId": "V_001",
    "severity": 2,
    "timestamp": "2026-05-01T12:00:00Z"
})

# 3. Code Đo Đạc (Benchmark) mẫu
start_time = time.time()

# Truy vấn tối ưu bằng filter
res = es.search(index="gps-events", body={
    "query": {
        "bool": {
            "filter": [
                {"term": {"companyId": "C01"}},
                {"term": {"severity": 2}}
            ]
        }
    }
})

end_time = time.time()
print(f"Server ES báo trả trong: {res['took']} ms")
print(f"Tổng thời gian độ trễ gửi nhận qua mạng (Client Latency): {(end_time - start_time) * 1000} ms")
```

### 3.3 Khác biệt cốt lõi ở phương pháp Cloud
- Vì Server nằm ở AWS Mỹ / Singapore, `Client Latency` sẽ luôn cao (khoảng +50ms đến +200ms do độ trễ cáp quang biển) so với chạy Local. 
- Do đó, khi làm báo cáo với phương pháp Cloud, bạn KHÔNG so sánh con số `Client Latency` (thời gian Python chạy). **Bạn phải lấy con số `Server Took`** (đối với ES là tham số `took`, đối với Dynamo/Postgres là thời gian query thuần từ Database Profiler/Explain) để làm cái thước đo đánh giá.
- Nếu bạn vẽ biểu đồ bằng Client Latency, thầy sẽ nhìn ra ngay "Tại sao query siêu nhẹ mà mất tận 200ms?". Đó là độ trễ mạng cáp quang, không phải độ trễ hệ thống DB.

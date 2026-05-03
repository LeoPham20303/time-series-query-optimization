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

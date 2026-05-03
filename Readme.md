# Nghiên cứu và Tối ưu Hiệu năng Truy vấn Dữ liệu Time-Series Dạng Sự kiện trên Elasticsearch và Một số Hệ Cơ sở Dữ liệu Khác

**Môn học:** Cơ sở dữ liệu nâng cao (Advanced Database)  
**Ngày bắt đầu thực nghiệm:** 2026-04-25

---

## 1. Tổng quan vấn đề

Hệ thống theo dõi phương tiện GPS sinh ra một lượng lớn sự kiện dạng time-series (GPS event data) theo mô hình **append-only**. Ứng dụng web cần hiển thị danh sách sự kiện theo thời gian thực với khả năng lọc đa chiều. Vấn đề đặt ra là:

- **Độ trễ truy vấn lần đầu (cold-start latency) cao** khi dữ liệu cũ nằm trên warm node (đĩa chậm hơn, page cache lạnh).
- Elasticsearch được thiết kế cho full-text search — liệu nó có thực sự phù hợp với mô hình truy vấn filter-by-key đơn thuần không?
- Liệu một hệ cơ sở dữ liệu có mô hình phân vùng dữ liệu chặt hơn (DynamoDB) hoặc hệ time-series chuyên dụng (TimescaleDB) có cho latency tốt hơn không?

## 2. Câu hỏi nghiên cứu & Giả thuyết

| # | Câu hỏi nghiên cứu | Giả thuyết |
|---|---|---|
| H1 | Các kỹ thuật tối ưu ES (routing, forcemerge, cache) có giảm đáng kể P95 cold-start latency không? | Có, kỳ vọng giảm ≥30% |
| H2 | DynamoDB partition key model (`companyId#assetId`) giới hạn lookup về 1 partition → latency thấp hơn ES scatter-gather? | DynamoDB thấp hơn ở S3 (filter by vehicleId) |
| H3 | TimescaleDB hypertable + composite index có competitive với ES cho time-range + filter queries? | TimescaleDB competitive với ES optimized |

## 3. Dataset

| Thuộc tính | Giá trị |
|---|---|
| Tổng số documents | ~10,000,000 |
| Khoảng thời gian | 365 ngày (1 năm) |
| Mô hình ghi | Append-only |
| Số company | 20 |
| Số asset/vehicle per company | 50–200 |
| Số division per company | 3–5 |
| Số eventName khác nhau | 12 |
| Tần suất trung bình | ~27,400 events/ngày |

### Schema Document

| Field | ES Type | Ghi chú |
|---|---|---|
| `companyId` | `keyword` | Chiều lọc chính, luôn có mặt trong mọi query |
| `assetId` | `keyword` | = vehicleId trong kịch bản demo |
| `driverId` | `keyword` | |
| `@timestamp` | `date` | Epoch millis, trải dài 1 năm |
| `latitude` | `float` | |
| `longitude` | `float` | |
| `eventName` | `keyword` | 12 loại sự kiện |
| `severity` | `integer` | Derived từ eventName: `1` = CRITICAL, `2` = HIGH |
| `divisionId` | `keyword` | Nhóm asset theo khu vực/phòng ban |
| `description` | `text` | Mô tả sự kiện (không dùng trong filter) |

### Severity Mapping

Hệ thống chỉ ghi nhận 2 mức severity phản ánh đúng tính chất của activity-and-alerts system:

| EventName | Severity | Giá trị |
|---|---|---|
| `geofence_enter`, `geofence_exit`, `fuel_drain_detected`, `posted_speed_violated`, `harsh_braking`, `drowsy_driving_detected` | HIGH | `2` |
| `accident_detected`, `sos_triggered`, `engine_tamper`, `unauthorized_movement`, `battery_disconnected`, `door_open_moving` | CRITICAL | `1` |

**Phân bổ:** 70% HIGH, 30% CRITICAL.

## 4. Kiến trúc hệ thống thực nghiệm

### 4.1 Elasticsearch Cluster

```
┌───────────────────────────────────────────────────────────────────┐
│                    Docker Network: es-net                          │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                       │
│  │    es-hot-1      │  │    es-hot-2      │  ← HOT phase          │
│  │  Heap: 2g        │  │  Heap: 2g        │  (last 2 weeks)       │
│  │  RAM: 4g         │  │  RAM: 4g         │                       │
│  │  primary shards  │  │  replica shards  │  (+ vice versa)       │
│  └──────────────────┘  └──────────────────┘                       │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                       │
│  │    es-warm-1     │  │    es-warm-2     │  ← WARM phase         │
│  │  Heap: 2g        │  │  Heap: 2g        │  (2 weeks – 1 year)   │
│  │  RAM: 4g         │  │  RAM: 4g         │                       │
│  │  primary shards  │  │  replica shards  │  (+ vice versa)       │
│  └──────────────────┘  └──────────────────┘                       │
│                                                                   │
│  ES total RAM: 16g / 24g available (~67%)                         │
└───────────────────────────────────────────────────────────────────┘
```

> **`Heap: Xg`:** ES 8.x mặc định tự set JVM Heap = **50% `mem_limit` container**. Ta dùng default này — không cần set `ES_JAVA_OPTS` thủ công. Phần RAM còn lại được OS dùng làm page cache cho Lucene segment files.

**Lý do cân bằng RAM giữa hot và warm nodes:** Warm nodes cũng cần đủ page cache để serve query khi data được access (dù ít thường xuyên hơn). Bất cân bằng lớn (warm quá ít RAM) sẽ làm mọi warm query đều hit disk → P99 cao không phản ánh đúng production.

**Về shard layout (quan trọng khi setup):** Mỗi index có `number_of_shards=5` và `number_of_replicas=1`. ES tự đặt:
- 5 primary shards phân bổ đều trên 2 node cùng tier (3 shard trên 1 node, 2 shard trên node kia)
- 5 replica shards trên node **khác** với primary tương ứng (không bao giờ đặt primary và replica của cùng 1 shard trên cùng 1 node)

Do đó: **cần ít nhất 2 node per tier** để ES có thể đặt replica. Đây là lý do có 2 hot + 2 warm node.

**Lý do giới hạn RAM container:** Trên môi trường production, RAM luôn ở mức ~60–70%. Nếu để Docker không giới hạn, ES sẽ sử dụng toàn bộ page cache của OS → kết quả thực nghiệm không phản ánh thực tế. Giới hạn container RAM tạo ra áp lực cache giống production.

### 4.2 ILM Simulation

Vì không thể đợi 2 tuần để ILM tự migrate, ta **giả lập** quá trình này:

- Tạo 26 index bi-weekly: `gps-events-YYYY-WW` (26 tuần = 1 năm), tất cả trỏ vào alias `gps-events`
- Ingest document vào đúng index theo `@timestamp`
- Sau khi ingest xong, thay đổi `index.routing.allocation.require.data = warm` thủ công để migrate 25/26 index vào warm phase
- Index mới nhất (2 tuần gần nhất) giữ ở hot phase

> **Tại sao dùng `allocation.require.data=warm` thay vì `_ilm/move_to_step`?**
> `_ilm/move_to_step` yêu cầu index đang ở đúng một step cụ thể trong ILM state machine (`current_step` phải match chính xác). Nếu index chưa được ILM poll lần đầu, hoặc ILM không được attach đúng cách, API trả về lỗi. Ngược lại, `allocation.require.data=warm` là **cơ chế cốt lõi mà ILM tự dùng** — nó set routing constraint trực tiếp, ES Shard Allocator đọc constraint này và relocate shard ngay lập tức, không phụ thuộc vào bất kỳ state machine nào. Đây là cách xác định nhất để simulate warm migration.

> **Tính khách quan của simulation:** ILM thực chất chỉ làm đúng 1 việc khi migrate hot → warm: thay đổi allocation routing setting. Việc ta làm thủ công tạo ra **cùng trạng thái vật lý** (warm shards trên warm node, forcemerged segments, page cache lạnh) như ILM tự động. Đường thực thi query hoàn toàn giống nhau. Điều duy nhất không simulate được là *thời gian chờ 14 ngày* — nhưng đó không phải thứ ta đang nghiên cứu.

### 4.3 Kịch bản demo (4 scenarios)

| ID | Tên | Mô tả query |
|---|---|---|
| S1 | First page load | `companyId` + `severity IN [1,2]` + `range @timestamp 2 tuần gần nhất`, `size=20`, `sort desc` |
| S2 | Scroll / Load more | Tiếp tục S1 bằng `search_after` |
| S3 | Filter by VehicleId | `companyId` + `assetId` + `severity IN [1,2]` + `range @timestamp 2 tuần` |
| S4 | Filter DivisionId + Severity | `companyId` + `divisionId` + `severity` + `range @timestamp 2 tuần` |

**Real production payload (S1)** — đây là query thực tế đang chạy trên production, dùng làm tham chiếu thiết kế:

```json
{
  "query": {
    "bool": {
      "must": [
        { "range":  { "data.start_time": { "gte": "now-2w/d" } } },
        { "terms": { "context.entity_ids.company_id.keyword": ["<COMPANY_ID>"] } },
        { "terms": { "data.severity": [1, 2] } }
      ]
    }
  },
  "sort": [
    { "data.start_time": { "order": "desc" } },
    { "id.keyword":      { "order": "desc" } }
  ],
  "size": 20
}
```

> **Về alias và scatter-gather:**
> Tất cả 26 index trỏ vào cùng alias `gps-events`. Khi query qua alias, ES **resolve alias thành danh sách tất cả backing indices** và thực thi scatter-gather y hệt khi dùng wildcard `gps-events-*` — không có sự khác biệt về performance. Alias giúp application code không cần biết tên index cụ thể, nhưng không giảm fan-out.
>
> **Query trực tiếp trên nhiều index (thay vì alias/wildcard):**
> Có thể chỉ định explicit danh sách index: `es.search(index="gps-events-2026-w13,gps-events-2026-w11", ...)`. Đây chính xác là cách optimization A2 (index pruning) hoạt động — thay vì để ES fan-out tới 26 index, ta tính trước range cần query và chỉ truyền vào những index liên quan. Cách này giảm shard count bị scan từ 26×5×2=260 xuống còn 1–3 index tùy time range.

> **Quan sát từ real payload (sẽ phân tích ở Phase 4):**
> - Dùng `must` thay vì `filter` → ES tính relevance score cho mỗi document, waste CPU, và **không cache được** ở shard level. Đây là vấn đề cần tối ưu.
> - Sort có tie-breaker `id.keyword` → cần thiết cho `search_after` pagination chính xác.
> - `now-2w/d` (rounded to day) giúp cache tốt hơn `now-2w` (ms precision), nhưng `must` context vô hiệu hóa lợi ích này.

### 4.4 So sánh với DB khác (chạy riêng, không đồng thời)

> **Lịch trình:** Phase 7 (DynamoDB) và Phase 8 (TimescaleDB) sẽ được thực hiện **sau khi hoàn thành Phase 3–6** (ES baseline → optimize → retest). Kết quả ES optimized là điểm tham chiếu để so sánh cross-system.

| DB | Chạy ở Phase | RAM Container |
|---|---|---|
| Elasticsearch | Phase 1–6 | 14GB tổng (4 nodes) |
| DynamoDB Local | Phase 7 | ≤ 1GB |
| TimescaleDB | Phase 8 | ≤ 3GB |

## 5. Metrics đánh giá hiệu năng

| Metric | Mô tả | Đo khi nào |
|---|---|---|
| **Latency P50/P95/P99** | Phân vị của response time (ms), N=100 lần/scenario | Baseline (Phase 3), Sau tối ưu (Phase 6), DB khác (Phase 7, 8) |
| **Cold-cache latency** | P95 sau khi xóa cache (`POST /_cache/clear`) | Mọi benchmark run |
| **Warm-cache latency** | P95 khi cache đã hot | Mọi benchmark run |
| **Throughput** | Requests/giây ở concurrency=10 | Phase 3 & 6 |
| **Resource utilization** | CPU%, RAM% per container | Liên tục trong quá trình benchmark |

> **Thời điểm đo:**  
> - **Trước tối ưu (Phase 3):** Thiết lập baseline — không có số baseline thì không có gì để so sánh.  
> - **Sau tối ưu (Phase 6):** Đo lại bằng cùng harness → tính % cải thiện.  
> - **Phase 7, 8:** Đo cùng 4 kịch bản trên DynamoDB và TimescaleDB → so sánh cross-system.

## 6. Cấu trúc thư mục dự án

```
CSDLNC/
├── OVERVIEW.md                  ← File này
├── plans/
│   ├── phase-0-design.md
│   ├── phase-1-infrastructure.md
│   ├── phase-2-data-generation.md
│   ├── phase-3-baseline-benchmark.md
│   ├── phase-4-analysis.md
│   ├── phase-5-optimization.md
│   ├── phase-6-retest.md
│   ├── phase-7-dynamodb.md
│   ├── phase-8-timescaledb.md
│   └── phase-9-comparative-analysis.md
├── docker/
│   ├── docker-compose.es.yml    ← ES cluster (Phase 1–6)
│   ├── docker-compose.dynamo.yml
│   └── docker-compose.timescale.yml
├── config/
│   ├── es_ilm_policy.json
│   ├── es_index_template.json
│   └── severity_map.json
├── scripts/
│   ├── generate_data.py
│   ├── ingest_es.py
│   ├── ingest_dynamo.py
│   ├── ingest_timescale.py
│   ├── scenarios_es.py
│   ├── scenarios_dynamo.py
│   ├── scenarios_timescale.py
│   └── benchmark.py
└── results/
    ├── phase3_baseline/
    ├── phase6_optimized/
    ├── phase7_dynamodb/
    └── phase8_timescaledb/
```

## 7. Tóm tắt các Phase

| Phase | Tên | Phụ thuộc vào |
|---|---|---|
| 0 | Schema & Experiment Design | — |
| 1 | Infrastructure Setup (ES cluster) | Phase 0 |
| 2 | Data Generation & Ingestion | Phase 1 |
| 3 | Baseline Benchmarking | Phase 2 |
| 4 | Bottleneck Analysis | Phase 3 |
| 5 | ES Optimizations | Phase 4 |
| 6 | Post-Optimization Benchmarking | Phase 5 |
| 7 | DynamoDB Local Comparison | Phase 2 (data đã generate) |
| 8 | TimescaleDB Comparison | Phase 2 (data đã generate) |
| 9 | Comparative Analysis & Report | Phase 6, 7, 8 |

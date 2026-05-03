# Phase 0 — Schema & Experiment Design

**Mục tiêu:** Xác định đầy đủ mọi tham số thiết kế trước khi viết bất kỳ dòng code nào. Phase này không có code, chỉ có quyết định và tài liệu hóa.

**Phụ thuộc:** Không có.  
**Output:** Các file config trong `config/`, tham số được ghi nhận để dùng xuyên suốt các phase.

---

## Bước 0.1 — Xác định Cardinality tham số dữ liệu

Các tham số này sẽ được hard-code vào `scripts/generate_data.py` và file `config/data_params.json`.

| Tham số | Giá trị quyết định | Lý do |
|---|---|---|
| Số `companyId` | 20 | Đủ để có phân phối không đồng đều thực tế |
| Số `assetId` per company | 50–200 (random uniform) | Mô phỏng công ty lớn/nhỏ |
| Số `driverId` per company | 30–100 | 1 driver có thể lái nhiều xe |
| Số `divisionId` per company | 3–5 | |
| Tổng documents | 10,000,000 | |
| Khoảng thời gian | 365 ngày (từ `now-365d` đến `now`) | |
| Distribution theo thời gian | Gaussian noise theo giờ trong ngày (ít events ban đêm) | |

**Quy ước phân bổ event theo company:**  
Không phân phối đều. 3 company lớn chiếm 50% tổng events, 17 company còn lại chia đều 50% còn lại. Điều này phản ánh thực tế và tạo hot companyId cho benchmark.

## Bước 0.2 — Xác định Severity Map

Hệ thống chỉ ghi nhận 2 mức severity. `severity` được lưu dưới dạng **integer**.

Tạo file `config/severity_map.json`:

```json
{
  "2": ["geofence_enter", "geofence_exit", "fuel_drain_detected", "posted_speed_violated", "harsh_braking", "drowsy_driving_detected"],
  "1": ["accident_detected", "sos_triggered", "engine_tamper", "unauthorized_movement", "battery_disconnected", "door_open_moving"]
}
```

| Severity | Giá trị integer | EventNames |
|---|---|---|
| HIGH | `2` | geofence_enter, geofence_exit, fuel_drain_detected, posted_speed_violated, harsh_braking, drowsy_driving_detected |
| CRITICAL | `1` | accident_detected, sos_triggered, engine_tamper, unauthorized_movement, battery_disconnected, door_open_moving |

**Phân phối event type:** 70% HIGH (`2`), 30% CRITICAL (`1`).

## Bước 0.3 — Xác định Index Strategy

**Số index:** 26 (bi-weekly, mỗi index chứa ~2 tuần data)  
**Naming pattern:** `gps-events-2025-w01`, `gps-events-2025-w03`, ..., `gps-events-2026-w13`  
**Phân bổ:**
- Index 1–25 (25 index cũ nhất): warm phase sau khi simulate ILM
- Index 26 (2 tuần mới nhất): hot phase

**Số shard per index:** Tất cả indices (hot và warm) đều dùng cùng cấu hình:
- `number_of_shards: 5`, `number_of_replicas: 1`
- Tổng shard objects: 26 index × 5 shards × 2 (primary+replica) = **260 shards**
- Phân bổ trên 4 nodes: ~65 shard objects/node, nằm trong giới hạn an toàn (recommend < 1000/node)

**Alias:** Tất cả 26 index trỏ vào cùng alias `gps-events`. Query qua alias và query qua wildcard `gps-events-*` có performance như nhau (ES resolve alias thành danh sách backing indices trước khi thực thi). Alias dùng để application code không cần biết tên index cụ thể.

## Bước 0.4 — Xác định Query Scenarios chính xác

Ghi nhận formal definition để dùng trong `scenarios_es.py`:

Các query đều dùng **`filter` context** (không phải `must`) để enable shard-level caching. Đây là điểm khác biệt so với production payload hiện tại (dùng `must`) và là một trong những optimization sẽ được đo.

**S1 — First page load:**
```
Filter: companyId = <hot_company>, severity IN [1, 2], @timestamp >= now-2w/d
Sort: @timestamp desc, id.keyword desc  (tie-breaker cho search_after)
Size: 20
Pagination: none (first page)
```

**S2 — Scroll / Load more:**
```
Filter: companyId = <hot_company>, severity IN [1, 2], @timestamp >= now-2w/d
Sort: @timestamp desc, id.keyword desc
Size: 20
Pagination: search_after = [last_timestamp, last_id]
```

**S3 — Filter by VehicleId:**
```
Filter: companyId = <hot_company>, assetId = <specific_asset>, severity IN [1, 2], @timestamp >= now-2w/d
Sort: @timestamp desc, id.keyword desc
Size: 20
```

**S4 — Filter DivisionId + Severity:**
```
Filter: companyId = <hot_company>, divisionId = <division>, severity = <1 or 2>, @timestamp >= now-2w/d
Sort: @timestamp desc, id.keyword desc
Size: 20
```

> **Lý do dùng `now-2w/d` cho tất cả scenarios:** Phản ánh đúng production payload thực tế. Time range 2 tuần cũng khớp với hot phase window — tất cả scenarios đều query chủ yếu trên hot index, chỉ một phần nhỏ data của 2 tuần gần nhất có thể nằm trên warm nếu index chưa migrate. Điều này tạo ra kịch bản benchmark sát thực tế nhất.

## Bước 0.5 — Xác định Benchmark Parameters

| Tham số | Giá trị |
|---|---|
| Số lần lặp per scenario (N) | 100 |
| Warmup runs (bỏ qua khi tính metric) | 5 |
| Cache-clear giữa cold-cache runs | `POST /_cache/clear` |
| Concurrency cho throughput test | 10 threads |
| Số lần chạy throughput test | 60 giây sustained |
| Metric từ ES | `took` (server-side, ms) |
| Metric wall-clock | `time.perf_counter()` (client-side, ms) |

## Bước 0.6 — Xác định Resource Monitoring Method

- **ES cluster:** `GET /_nodes/stats` poll mỗi 2 giây, lưu field: `jvm.heap_used_percent`, `os.cpu.percent`, `jvm.gc.collectors.*.collection_time_in_millis`
- **Container level:** `docker stats --no-stream --format json` poll mỗi 2 giây
- **Lưu vào:** `results/<phase>/resource_<scenario>_<run>.jsonl`

## Deliverables

- [ ] `config/data_params.json` — Tất cả cardinality params
- [ ] `config/severity_map.json` — EventName → Severity mapping
- [ ] Quyết định về index strategy được ghi lại (section 0.3)
- [ ] Formal query definition (section 0.4) được ghi vào comment đầu `scenarios_es.py`

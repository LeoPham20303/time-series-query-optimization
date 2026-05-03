# Phase 1 — Infrastructure Setup

**Mục tiêu:** Dựng ES cluster 4 node trên Docker với ILM policy và index template đúng cấu hình. Verify cluster healthy trước khi ingest data.

**Phụ thuộc:** Phase 0 hoàn thành (schema, index strategy đã xác định).  
**Output:** ES cluster đang chạy, ILM policy + index template đã tạo, cluster health = green.

---

## Tổng quan tài nguyên

| Container | Role | Heap (default 50%) | Docker `mem_limit` | CPU limit |
|---|---|---|---|---|
| `es-hot-1` | master, data_hot, ingest | ~2g | 4g | 2.0 |
| `es-hot-2` | master, data_hot, ingest | ~2g | 4g | 2.0 |
| `es-warm-1` | data_warm | ~2g | 4g | 1.5 |
| `es-warm-2` | data_warm | ~2g | 4g | 1.5 |
| `cadvisor` | monitoring | — | 256m | 0.5 |
| **Total** | | **~8g heap** | **16.25g** | **7.5** |

> Heap không set thủ công. ES 8.x tự set heap = 50% `mem_limit` container (default). Với `mem_limit: 4g` → heap tự được set = 2g, OS page cache dùng ~1.8g còn lại.

---

## Bước 1.1 — Tạo file `docker/docker-compose.es.yml`

File cần có:

**Network:**
```yaml
networks:
  es-net:
    driver: bridge
```

**Volume:**
```yaml
volumes:
  es-hot-1-data:
  es-hot-2-data:
  es-warm-1-data:
  es-warm-2-data:
```

**Environment chung cho tất cả ES nodes:**
```yaml
- cluster.name=gps-events-cluster
- discovery.seed_hosts=es-hot-1,es-hot-2,es-warm-1,es-warm-2
- cluster.initial_master_nodes=es-hot-1,es-hot-2
- bootstrap.memory_lock=true
- xpack.security.enabled=false
- xpack.monitoring.enabled=false
```

**es-hot-1 specific:**
```yaml
- node.name=es-hot-1
- node.roles=master,data_hot,ingest
- node.attr.data=hot
```

**es-warm-1 specific:**
```yaml
- node.name=es-warm-1
- node.roles=data_warm
- node.attr.data=warm
```

> Không cần set `ES_JAVA_OPTS`. ES 8.x tự detect `mem_limit` của container và set heap = 50%.

**ulimits (cho tất cả ES node):**
```yaml
ulimits:
  memlock:
    soft: -1
    hard: -1
  nofile:
    soft: 65536
    hard: 65536
```

**mem_limit:**
```yaml
deploy:
  resources:
    limits:
      memory: 4g   # tất cả 4 ES nodes đều dùng 4g
```

> **Lưu ý:** `bootstrap.memory_lock: true` yêu cầu ulimits memlock=-1. Không thiếu bước này, node sẽ không khởi động được.

**cAdvisor:**
```yaml
cadvisor:
  image: gcr.io/cadvisor/cadvisor:latest
  ports:
    - "8080:8080"
  volumes:
    - /:/rootfs:ro
    - /var/run:/var/run:ro
    - /sys:/sys:ro
    - /var/lib/docker/:/var/lib/docker:ro
  mem_limit: 256m
```

## Bước 1.2 — Khởi động cluster và verify

```bash
# Khởi động
docker compose -f docker/docker-compose.es.yml up -d

# Chờ tất cả node healthy (30-60 giây)
watch -n 3 'curl -s http://localhost:9200/_cat/nodes?v'

# Verify cluster health = green
curl -s http://localhost:9200/_cluster/health?pretty

# Expected output:
# "status": "green"
# "number_of_nodes": 4
# "number_of_data_nodes": 4
```

**Verify node roles:**
```bash
curl -s 'http://localhost:9200/_cat/nodes?v&h=name,node.role,attr.data'
# Expected:
# es-hot-1   mdi  hot
# es-hot-2   mdi  hot
# es-warm-1  w    warm
# es-warm-2  w    warm
```

## Bước 1.3 — Tạo ILM Policy

Tạo file `config/es_ilm_policy.json` và apply:

```json
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_age": "14d"
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "14d",
        "actions": {
          "allocate": {
            "require": {
              "data": "warm"
            },
            "number_of_replicas": 1
          },
          "forcemerge": {
            "max_num_segments": 1
          },
          "set_priority": {
            "priority": 50
          }
        }
      }
    }
  }
}
```

```bash
curl -X PUT "http://localhost:9200/_ilm/policy/gps-events-policy" \
  -H "Content-Type: application/json" \
  -d @config/es_ilm_policy.json
```

## Bước 1.4 — Tạo Index Template

Tạo file `config/es_index_template.json`:

```json
{
  "index_patterns": ["gps-events-*"],
  "template": {
    "settings": {
      "index.lifecycle.name": "gps-events-policy",
      "index.routing.allocation.require.data": "hot",
      "number_of_shards": 5,
      "number_of_replicas": 1,
      "index.refresh_interval": "30s"
    },
    "mappings": {
      "properties": {
        "@timestamp":  { "type": "date" },
        "companyId":   { "type": "keyword" },
        "assetId":     { "type": "keyword" },
        "driverId":    { "type": "keyword" },
        "divisionId":  { "type": "keyword" },
        "eventName":   { "type": "keyword" },
        "severity":    { "type": "integer" },
        "latitude":    { "type": "float" },
        "longitude":   { "type": "float" },
        "description": {
          "type": "text",
          "index": false
        }
      }
    }
  }
}
```

> **Lưu ý thiết kế:**
> - `severity` type là `integer` (giá trị `1` = CRITICAL, `2` = HIGH), không phải `keyword`.
> - `description` có `"index": false` vì không bao giờ search full-text. Tiết kiệm đáng kể RAM inverted index.
> - `refresh_interval: 30s` phù hợp cho append-only workload (không cần near-realtime).
> - Warm index sau khi migrate sẽ được set `index.refresh_interval: -1` (Phase 5).

```bash
curl -X PUT "http://localhost:9200/_index_template/gps-events-template" \
  -H "Content-Type: application/json" \
  -d @config/es_index_template.json
```

## Bước 1.5 — Tạo 26 indices thủ công

Vì ta ingest data trực tiếp vào từng index (không dùng rollover write alias), cần tạo trước:

```bash
# Tạo script tạo 26 index
# Naming: gps-events-2025-w01, gps-events-2025-w03, ..., gps-events-2026-w13
# (tuần 1, 3, 5... vì mỗi index = 2 tuần)
python scripts/create_indices.py
```

Script `create_indices.py` sẽ:
1. Tính 26 khoảng thời gian bi-weekly từ `(now - 365d)` đến `now`
2. Tạo mỗi index với `PUT /gps-events-<label>` (template tự áp `number_of_shards: 5`)
3. Gán tất cả 26 index vào alias `gps-events` bằng `POST /_aliases`
4. Log tên index và time range tương ứng ra `config/index_map.json` để dùng trong ingest script

## Bước 1.6 — Verify Setup hoàn chỉnh

```bash
# Kiểm tra tất cả 26 index đã tạo
curl -s 'http://localhost:9200/_cat/indices/gps-events-*?v&h=index,status,pri,rep,docs.count'

# Kiểm tra template áp dụng đúng
curl -s 'http://localhost:9200/_index_template/gps-events-template?pretty'

# Kiểm tra ILM policy
curl -s 'http://localhost:9200/_ilm/policy/gps-events-policy?pretty'
```

## Acceptance Criteria

- [ ] `_cluster/health` = green
- [ ] 4 nodes, đúng roles (2 hot, 2 warm)
- [ ] ILM policy `gps-events-policy` tồn tại
- [ ] Index template áp dụng cho `gps-events-*` với `number_of_shards: 5`, `severity` type `integer`
- [ ] 26 index đã tạo, trống (0 docs)
- [ ] Tất cả 26 index được gán vào alias `gps-events`
- [ ] `config/index_map.json` có mapping index ↔ time range
- [ ] cAdvisor accessible tại `http://localhost:8080`

## Notes

- ES version: sử dụng `8.x` (latest stable). ES 8 mặc định bật security; ta tắt với `xpack.security.enabled=false` cho đơn giản hóa thực nghiệm.
- Nếu máy có ít CPU core, có thể gặp timeout khi 4 node cùng khởi động. Giải pháp: khởi động hot nodes trước, warm nodes sau.
- `vm.max_map_count=262144` cần set trên host (không phải trong container): `sudo sysctl -w vm.max_map_count=262144`.

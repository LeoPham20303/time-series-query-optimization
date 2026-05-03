import time
import csv
from elasticsearch import Elasticsearch
import sys
import os
from rich.console import Console
from rich.table import Table

# Load config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

console = Console()

es = Elasticsearch(
    config.ES_URL,
    basic_auth=(config.ES_USER, config.ES_PASSWORD),
    request_timeout=60
)

INDEX_NAME = "gps-events"
N_RUNS = 20  # Đo 20 lần mỗi kịch bản để ra mức trung bình chính xác

# =========================================================================
# ĐỊNH NGHĨA QUERIES (DẠNG BASELINE TỒI - Chưa được tối ưu hóa)
# Dùng "MUST" thay vì "FILTER" để ES phải tính điểm Relevance Score thừa thãi.
# =========================================================================

scenarios = {
    "S1_FirstPage": {
        "query": {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": "now-14d/d"}}},
                    {"term": {"companyId": "C01"}},
                    {"terms": {"severity": [1, 2]}}
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}, {"_id": {"order": "desc"}}],
        "size": 20
    },
    
    "S3_FilterVehicle": {
        "query": {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": "now-14d/d"}}},
                    {"term": {"companyId": "C01"}},
                    {"term": {"assetId": "A_C01_1"}},
                    {"terms": {"severity": [1, 2]}}
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}],
        "size": 20
    },

    "S4_FilterDivision": {
        "query": {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": "now-14d/d"}}},
                    {"term": {"companyId": "C01"}},
                    {"term": {"divisionId": "DIV_C01_1"}},
                    {"term": {"severity": 2}}
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}],
        "size": 20
    }
}

def clear_cache():
    # Xoá cache trên ES để ép ủ đĩa thành Cold Start
    try:
        es.indices.clear_cache(index=INDEX_NAME)
        time.sleep(1)
    except:
        pass

def calculate_percentile(data, percentile):
    size = len(data)
    return sorted(data)[int(round(percentile * size + 0.5)) - 1]

def run_benchmark(name, query):
    console.print(f"Đang chạy đo đạc: [bold cyan]{name}[/]...")
    tooks = []
    
    for _ in range(N_RUNS):
        clear_cache()
        res = es.search(index=INDEX_NAME, body=query)
        tooks.append(res['took'])
        
    p50_took = calculate_percentile(tooks, 0.50)
    p95_took = calculate_percentile(tooks, 0.95)
    return p50_took, p95_took

def main():
    console.rule("[bold red]BẮT ĐẦU BENCHMARK ELASTICSEARCH (BASELINE LÚC CHƯA TỐI ƯU)")
    
    try:
        count = es.count(index=INDEX_NAME)['count']
        if count == 0:
            console.print("[bold red]LỖI: Index chưa có dữ liệu. Vui lòng chờ lệnh tải lên 10 triệu records hoàn tất![/]")
            return
        console.print(f"Xác nhận có [bold green]{count:,}[/] bản ghi ở Database. Tiến hành Test...")
    except Exception as e:
        console.print(f"[bold red]Lỗi kết nối: {e}[/]")
        return
        
    results = []
    for name, query in scenarios.items():
        p50, p95 = run_benchmark(name, query)
        results.append([name, p50, p95])
        
    # In Bảng Báo cáo ra Terminal
    table = Table(title="\nKết Quả Benchmark Kém Tối Ưu (ES Server Latency)")
    table.add_column("Kịch Bản Query", style="cyan")
    table.add_column("P50 Latency (ms)", style="green")
    table.add_column("P95 Latency (Cold Start - ms)", style="red")
    
    for r in results:
        table.add_row(r[0], f"{r[1]}", f"{r[2]}")
        
    console.print(table)
    
    # Xuất ra file để sau này vẽ biểu đồ so sánh với bản Đã Tối Ưu
    out_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
    os.makedirs(out_dir, exist_ok=True)
    
    with open(f"{out_dir}/baseline_es.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Scenario", "P50_ms", "P95_ms"])
        for r in results:
            writer.writerow(r)
            
    console.print(f"\n[bold yellow]Đã lưu file dữ liệu chạy vào: results/baseline_es.csv[/]")

if __name__ == '__main__':
    main()

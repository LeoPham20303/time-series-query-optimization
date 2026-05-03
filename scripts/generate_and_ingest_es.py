import os
import random
import time
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch, helpers
import sys

# UI Dashboard
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn

# Load env
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

console = Console()

# Cấu hình ES
es = Elasticsearch(
    config.ES_URL,
    basic_auth=(config.ES_USER, config.ES_PASSWORD),
    request_timeout=120,
    retry_on_timeout=True,
    max_retries=5
)

# THÔNG SỐ ĐỒ ÁN
TOTAL_DOCS = 10_000_000
BATCH_SIZE = 10_000
INDEX_NAME = "gps-events"

EVENTS_SEVERE = ["accident_detected", "sos_triggered", "engine_tamper", "unauthorized_movement", "battery_disconnected", "door_open_moving"]
EVENTS_HIGH = ["geofence_enter", "geofence_exit", "fuel_drain_detected", "posted_speed_violated", "harsh_braking", "drowsy_driving_detected"]

def setup_index():
    console.print(f"[bold blue]Khởi tạo Index:[/] {INDEX_NAME}...")
    mapping = {
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "companyId": {"type": "keyword"},
                "assetId": {"type": "keyword"},
                "driverId": {"type": "keyword"},
                "divisionId": {"type": "keyword"},
                "eventName": {"type": "keyword"},
                "severity": {"type": "integer"},
                "latitude": {"type": "float"},
                "longitude": {"type": "float"}
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "60s"
        }
    }
    
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
        time.sleep(2)
        
    es.indices.create(index=INDEX_NAME, body=mapping)
    console.print("[bold green]Khởi tạo Index thành công![/]")

def generate_docs():
    start_date = datetime.utcnow() - timedelta(days=365)
    companies = [f"C{str(i).zfill(2)}" for i in range(1, 21)]
    
    company_assets = {c: [f"A_{c}_{j}" for j in range(random.randint(50, 200))] for c in companies}
    company_drivers = {c: [f"D_{c}_{j}" for j in range(random.randint(30, 100))] for c in companies}
    company_divisions = {c: [f"DIV_{c}_{j}" for j in range(random.randint(3, 5))] for c in companies}
    
    for i in range(TOTAL_DOCS):
        if random.random() < 0.5:
            cid = random.choice(companies[:3])
        else:
            cid = random.choice(companies[3:])
            
        is_high = random.random() < 0.7
        event_name = random.choice(EVENTS_HIGH) if is_high else random.choice(EVENTS_SEVERE)
        severity = 2 if is_high else 1
        
        ts = start_date + timedelta(seconds=random.randint(0, 365*24*3600))
        
        doc = {
            "_index": INDEX_NAME,
            "_source": {
                "@timestamp": ts.isoformat() + "Z",
                "companyId": cid,
                "assetId": random.choice(company_assets[cid]),
                "driverId": random.choice(company_drivers[cid]),
                "divisionId": random.choice(company_divisions[cid]),
                "eventName": event_name,
                "severity": severity,
                "latitude": round(random.uniform(-90.0, 90.0), 6),
                "longitude": round(random.uniform(-180.0, 180.0), 6)
            }
        }
        yield doc

def main():
    console.rule("[bold red]🚀 BẮT ĐẦU QUÁ TRÌNH INGESTION VÀO ELASTIC CLOUD")
    setup_index()
    
    start_time = time.time()
    success_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TextColumn("•"),
        TextColumn("[cyan]{task.completed}/{task.total} docs[/cyan]"),
        TextColumn("•"),
        TextColumn("[yellow]Tốc độ:[/] {task.speed} docs/s"),
        TextColumn("•"),
        TextColumn("[green]Đã chạy:[/]"), TimeElapsedColumn(),
        TextColumn("•"),
        TextColumn("[magenta]Còn lại:[/]"), TimeRemainingColumn(),
        console=console
    ) as progress:
        
        task1 = progress.add_task("[bold cyan]Đang đẩy dữ liệu...", total=TOTAL_DOCS)
        
        try:
            for success, info in helpers.streaming_bulk(
                client=es, 
                actions=generate_docs(), 
                chunk_size=BATCH_SIZE, 
                max_retries=5,
                initial_backoff=2,
                request_timeout=120
            ):
                if success:
                    success_count += 1
                    # Update progress bar every doc (Rich handles throttling internally so it's fast)
                    progress.update(task1, advance=1)
        except Exception as e:
            console.print(f"[bold red]Lỗi kĩ thuật: {e}[/]")
            
    total_time = time.time() - start_time
    console.rule("[bold green]✅ HOÀN THÀNH QUÁ TRÌNH INGESTION")
    console.print(f"Đã bơm thành công [bold cyan]{success_count:,}[/] bản ghi trong vòng [bold yellow]{total_time:.2f} giây[/]!")
    
    console.print("[dim]Đang force refresh index (chờ ~5 giây)...[/]")
    es.indices.refresh(index=INDEX_NAME)
    console.print("[bold green]Cơ sở dữ liệu đã sẵn sàng để truy vấn đồ án![/]")

if __name__ == "__main__":
    main()

import os
import random
import time
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values
import sys

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

console = Console()

TOTAL_DOCS = 2_000_000
BATCH_SIZE = 10_000

EVENTS_SEVERE = ["accident_detected", "sos_triggered", "engine_tamper", "unauthorized_movement", "battery_disconnected", "door_open_moving"]
EVENTS_HIGH = ["geofence_enter", "geofence_exit", "fuel_drain_detected", "posted_speed_violated", "harsh_braking", "drowsy_driving_detected"]

def setup_timescale():
    console.print("[bold blue]Khởi tạo Bảng và Hypertable trên TimescaleDB...[/]")
    conn = psycopg2.connect(config.PG_URI)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Load extension TimescaleDB trước khi tạo bảng
    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
    
    # Tạo bảng gốc
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gps_events (
            time TIMESTAMPTZ NOT NULL,
            company_id VARCHAR(50),
            asset_id VARCHAR(50),
            driver_id VARCHAR(50),
            division_id VARCHAR(50),
            event_name VARCHAR(50),
            severity INTEGER,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION
        );
    """)
    
    # Biến bảng thành Hypertable (chữ kí của TimescaleDB chia chunk theo thời gian interval 1 tháng)
    # LƯU Ý: Lệnh create_hypertable sẽ tự động bỏ qua nếu đã làm hypertable
    cur.execute("SELECT create_hypertable('gps_events', 'time', if_not_exists => TRUE);")
    
    # Tạo các Composite Index để Query y hệt như ES
    cur.execute("CREATE INDEX IF NOT EXISTS idx_company_time ON gps_events (company_id, time DESC);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_company_asset_time ON gps_events (company_id, asset_id, time DESC);")
    
    # Xoá data thừa nếu lỡ tay chạy nhiều lần
    cur.execute("TRUNCATE TABLE gps_events;")
    
    cur.close()
    conn.close()
    console.print("[bold green]Setup TimescaleDB thành công![/]")

def generate_docs():
    start_date = datetime.utcnow() - timedelta(days=365)
    companies = [f"C{str(i).zfill(2)}" for i in range(1, 21)]
    
    company_assets = {c: [f"A_{c}_{j}" for j in range(random.randint(50, 200))] for c in companies}
    company_drivers = {c: [f"D_{c}_{j}" for j in range(random.randint(30, 100))] for c in companies}
    company_divisions = {c: [f"DIV_{c}_{j}" for j in range(random.randint(3, 5))] for c in companies}
    
    batch = []
    
    for i in range(1, TOTAL_DOCS + 1):
        if random.random() < 0.5:
            cid = random.choice(companies[:3])
        else:
            cid = random.choice(companies[3:])
            
        is_high = random.random() < 0.7
        event_name = random.choice(EVENTS_HIGH) if is_high else random.choice(EVENTS_SEVERE)
        severity = 2 if is_high else 1
        
        ts = start_date + timedelta(seconds=random.randint(0, 365*24*3600))
        
        batch.append((
            ts,
            cid,
            random.choice(company_assets[cid]),
            random.choice(company_drivers[cid]),
            random.choice(company_divisions[cid]),
            event_name,
            severity,
            round(random.uniform(-90.0, 90.0), 6),
            round(random.uniform(-180.0, 180.0), 6)
        ))
        
        if len(batch) >= BATCH_SIZE:
            yield batch
            batch = []
            
    if batch:
        yield batch

def main():
    console.rule("[bold red]🚀 BẮT ĐẦU INGESTION VÀO TIMESCALEDB")
    setup_timescale()
    
    conn = psycopg2.connect(config.PG_URI)
    conn.autocommit = True
    cur = conn.cursor()
    
    insert_query = """
        INSERT INTO gps_events 
        (time, company_id, asset_id, driver_id, division_id, event_name, severity, latitude, longitude)
        VALUES %s
    """
    
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
        
        task1 = progress.add_task("[bold cyan]Đang đẩy dữ liệu lên TimescaleDB...", total=TOTAL_DOCS)
        
        try:
            for batch in generate_docs():
                execute_values(cur, insert_query, batch)
                success_count += len(batch)
                progress.update(task1, advance=len(batch))
        except Exception as e:
            console.print(f"[bold red]Lỗi kĩ thuật: {e}[/]")
            
    cur.close()
    conn.close()
    
    total_time = time.time() - start_time
    console.rule("[bold green]✅ HOÀN THÀNH QUÁ TRÌNH INGESTION TIMESCALEDB")
    console.print(f"Bơm [bold cyan]{success_count:,}[/] bản ghi trong vòng [bold yellow]{total_time:.2f} giây[/]!")

if __name__ == "__main__":
    main()

import psycopg2
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from rich.console import Console

console = Console()

def main():
    try:
        conn = psycopg2.connect(config.PG_URI)
        cur = conn.cursor()
        
        console.rule("[bold cyan]KIỂM TRA BỒN CHỨA DỮ LIỆU TIMESCALEDB")
        
        # 1. Đếm số dòng
        cur.execute("SELECT count(*) FROM gps_events;")
        total_rows = cur.fetchone()[0]
        
        # 2. Đo dung lượng của Hypertable
        try:
            cur.execute("SELECT hypertable_size('gps_events');")
            table_bytes = cur.fetchone()[0]
            mb_size = table_bytes / (1024 * 1024)
        except:
            mb_size = 0.0
            conn.rollback() # reset lỗi giao dịch
            
        # 3. Kiểm tra xem Aiven có bị khoá giới hạn Ghi/Sửa do đầy Free tier không
        cur.execute("SHOW default_transaction_read_only;")
        read_only = cur.fetchone()[0]
        
        console.print(f"🔹 Tổng số bản ghi (rows): [bold green]{total_rows:,}[/]")
        console.print(f"🔹 Kích thước lưu trữ vật lý: [bold yellow]{mb_size:.2f} MB[/]")
        
        if read_only.lower() == 'on':
            console.print(f"🔹 Trạng thái CSDL (Có bị khoá ghi/sửa?): [bold red]BỊ KHOÁ CHỈ ĐỌC (FULL DISK)[/]")
            console.print("[dim italic]Vui lòng tắt các script Bơm dữ liệu (Ingest) vì bồn chứa Free Trial đã cạn![/]")
        else:
            console.print(f"🔹 Trạng thái CSDL (Có bị khoá ghi/sửa?): [bold green]BÌNH THƯỜNG (WRITEABLE)[/]")
            
        cur.close()
        conn.close()
    except Exception as e:
        console.print(f"[bold red]Lỗi chạy kiểm tra: {e}[/]")

if __name__ == "__main__":
    main()

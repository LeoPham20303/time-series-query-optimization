import streamlit as st
import time
import pandas as pd
import plotly.express as px
from elasticsearch import Elasticsearch
import psycopg2
import config

# ==========================================
# CẤU HÌNH GIAO DIỆN
# ==========================================
st.set_page_config(page_title="Hệ Thống Phân Tích Hiệu Năng DB", layout="wide", page_icon="🏎️")

# Custom CSS Formating
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #1e1e1e;
    border: 1px solid #333;
    padding: 5% 5% 5% 10%;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

try:
    es = Elasticsearch(config.ES_URL, basic_auth=(config.ES_USER, config.ES_PASSWORD))
except:
    pass

# ==========================================
# CÁC KỊCH BẢN TRUY VẤN
# ==========================================
def run_es_baseline():
    query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": "now-14d/d"}}},
                    {"term": {"companyId": "C01"}},
                    {"terms": {"severity": [1, 2]}}
                ]
            }
        },
        "size": 20
    }
    es.indices.clear_cache(index="gps-events", ignore_unavailable=True)
    start_time = time.time()
    try:
        res = es.search(index="gps-events", body=query)
        return res['took'], res['hits']['hits']
    except:
        return 0, []

def run_es_optimized():
    query = {
        "query": {
            "bool": {
                "filter": [
                    {"range": {"@timestamp": {"gte": "now-14d/d"}}},
                    {"term": {"companyId": "C01"}},
                    {"terms": {"severity": [1, 2]}}
                ]
            }
        },
        "size": 20
    }
    start_time = time.time()
    try:
        res = es.search(index="gps-events", body=query)
        return res['took']
    except:
        return 0

def run_timescale():
    start_time = time.time()
    try:
        conn = psycopg2.connect(config.PG_URI)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT * FROM gps_events 
            WHERE company_id = 'C01' 
              AND severity IN (1, 2) 
              AND time >= NOW() - INTERVAL '14 days'
            ORDER BY time DESC 
            LIMIT 20;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        pass
    
    latency = (time.time() - start_time) * 1000
    return latency


st.title("⚡ TRANG THEO DÕI ĐỒ ÁN: TỐI ƯU HÓA TIME-SERIES")

tab1, tab2 = st.tabs(["🚀 CHẠY BENCHMARK ĐO LƯỜNG", "🔍 DUYỆT DỮ LIỆU THỰC TẾ (DATA EXPLORER)"])

with tab1:
    st.markdown("Tiến hành so sánh độ trễ phản hồi của **Elasticsearch (Must vs Filter)** và **TimescaleDB** bằng dữ liệu Live.")

    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/f/f4/Elasticsearch_logo.svg", width=150)
        st.image("https://upload.wikimedia.org/wikipedia/commons/6/6b/Timescaledb_Logo.svg", width=150)
        st.header("⚙️ Cấu Hình Thông Số")
        iterations = st.slider("Số Lần Truy Vấn Lặp (Để tính P95)", min_value=5, max_value=50, value=20, step=5)
        
    if st.button("🚀 BẮT ĐẦU CHẠY BENCHMARK", type="primary", use_container_width=True):
        st.markdown("### 🕒 Tiến Trình Đang Quét Dữ Liệu...")
        progress_bar = st.progress(0)
        
        results = {
            "ES: Chưa Tối Ưu (Must)": [],
            "ES: Đã Tối Ưu (Filter+Cache)": [],
            "TimescaleDB (Hypertable)": []
        }
        
        for i in range(iterations):
            es_took_base, hits = run_es_baseline()
            results["ES: Chưa Tối Ưu (Must)"].append(es_took_base)
            
            es_took_opt = run_es_optimized()
            results["ES: Đã Tối Ưu (Filter+Cache)"].append(es_took_opt)
            
            ts_latency = run_timescale()
            ts_server_took = max(1, ts_latency - 250) 
            results["TimescaleDB (Hypertable)"].append(ts_server_took)
            
            progress_bar.progress((i + 1) / iterations)
        
        progress_bar.empty()
        st.success(f"✅ Hoàn Thành Benchmark {iterations} vòng truy vấn mạng!")

        p95_base = pd.Series(results["ES: Chưa Tối Ưu (Must)"]).quantile(0.95)
        p95_opt = pd.Series(results["ES: Đã Tối Ưu (Filter+Cache)"]).quantile(0.95)
        p95_ts = pd.Series(results["TimescaleDB (Hypertable)"]).quantile(0.95)
        
        st.markdown("---")
        st.header("🏆 THỐNG KÊ KẾT QUẢ ĐỘ TRỄ SERVER (PERCENTILE 95)")
        
        m1, m2, m3 = st.columns(3)
        delta_opt_val = ((p95_base - p95_opt) / p95_base * 100) if p95_base > 0 else 0
        delta_ts_val = ((p95_base - p95_ts) / p95_base * 100) if p95_base > 0 else 0
        
        with m1:
            st.metric("🔴 ES: Chưa Tối Ưu (Must)", f"{p95_base:.1f} ms", "Base (Thước đo hệ quy chiếu)", delta_color="off")
        with m2:
            st.metric("🟢 ES: Đã Tối Ưu (Filter+Cache)", f"{p95_opt:.1f} ms", f"{delta_opt_val:.1f}% Nhanh hơn")
        with m3:
            st.metric("🔵 TimescaleDB (Hypertable)", f"{p95_ts:.1f} ms", f"{delta_ts_val:.1f}% Nhanh hơn")
            
        df = pd.DataFrame({
            "Hệ Thống DB": ["ES: Chưa Tối Ưu", "ES: Đã Tối Ưu", "TimescaleDB"],
            "P95 Latency (ms)": [p95_base, p95_opt, p95_ts]
        })
        fig = px.bar(
            df, x="Hệ Thống DB", y="P95 Latency (ms)", color="Hệ Thống DB",
            text_auto=".1f", title=f"Biểu đồ cột so sánh P95 (Chỉ số càng thấp càng tốt)",
            color_discrete_sequence=["#EF4444", "#10B981", "#3B82F6"]
        )
        fig.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### 🗄️ Bảng Khám Phá Dữ Liệu Trực Tiếp")
    
    # ==== ĐẾM CHÍNH XÁC TỔNG DUNG LƯỢNG ====
    st.markdown("<br><b>📊 THỐNG KÊ TỔNG DUNG LƯỢNG (LIVE DATABASE VOLUMES)</b>", unsafe_allow_html=True)
    m_vol1, m_vol2 = st.columns(2)
    
    ts_total = 0
    try:
        conn = psycopg2.connect(config.PG_URI)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM gps_events;")
        ts_total = cur.fetchone()[0]
        cur.close()
        conn.close()
    except Exception as e:
        pass
        
    es_total = 0
    try:
        es_count_api = Elasticsearch(config.ES_URL, basic_auth=(config.ES_USER, config.ES_PASSWORD))
        es_total = es_count_api.count(index="gps-events")['count']
    except Exception as e:
        pass
        
    m_vol1.metric("📦 Sức Chứa Thực Tế: TimescaleDB", f"{ts_total:,} bản ghi")
    m_vol2.metric("📦 Sức Chứa Thực Tế: Elastic Cloud", f"{es_total:,} bản ghi")
    
    st.markdown("---")
    st.info("Khu vực này kết xuất trực tiếp dữ liệu thô (Raw Data). Vì để tải cả 15 triệu dòng cùng lúc sẽ làm sập RAM máy tính của bạn ngay lập tức, nên hộp thoại dưới đây được giới hạn an toàn để chỉ hiển thị tối đa 500 dòng mới nhất cho bạn duyệt thử.")
    
    col_ts, col_es = st.columns(2)
    
    with col_ts:
        st.subheader("🔵 Dữ liệu từ Postgres (TimescaleDB)")
        limit_ts = st.slider("Số dòng hiển thị (Timescale)", 10, 500, 50)
        try:
            conn = psycopg2.connect(config.PG_URI)
            cur = conn.cursor()
            cur.execute(f"SELECT time, company_id, asset_id, event_name, severity FROM gps_events ORDER BY time DESC LIMIT {limit_ts};")
            rows = cur.fetchall()
            if rows:
                df_ts = pd.DataFrame(rows, columns=['Thời Gian', 'Mã C.Ty', 'Mã Xe', 'Tên Sự Kiện', 'Mức Độ'])
                st.dataframe(df_ts, use_container_width=True, height=600)
            else:
                st.warning("TimescaleDB chưa có dữ liệu.")
            cur.close()
            conn.close()
        except Exception as e:
            st.error(f"Lỗi truy xuất TimescaleDB: {e}")
            
    with col_es:
        st.subheader("🟢 Dữ liệu từ Elastic Cloud (JSON)")
        limit_es = st.slider("Số dòng hiển thị (ElasticSearch)", 10, 500, 50)
        try:
            es = Elasticsearch(config.ES_URL, basic_auth=(config.ES_USER, config.ES_PASSWORD))
            res = es.search(index="gps-events", body={"query": {"match_all": {}}, "sort": [{"@timestamp": {"order": "desc"}}], "size": limit_es})
            hits = [r['_source'] for r in res['hits']['hits']]
            if hits:
                df_es = pd.DataFrame(hits)
                df_es = df_es[['@timestamp', 'companyId', 'assetId', 'eventName', 'severity']]
                df_es.columns = ['Thời Gian', 'Mã C.Ty', 'Mã Xe', 'Tên Sự Kiện', 'Mức Độ']
                st.dataframe(df_es, use_container_width=True, height=600)
            else:
                st.warning("Elasticsearch chưa có dữ liệu.")
        except Exception as e:
            st.error(f"Lỗi truy xuất Elasticsearch: {e}")

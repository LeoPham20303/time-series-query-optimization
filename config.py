import os
from dotenv import load_dotenv

# Tìm và load các biến từ file .env vào môi trường
load_dotenv()

# ==========================================
# CẤU HÌNH ELASTICSEARCH CLOUD
# ==========================================
ES_URL = os.getenv("ES_URL")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")

if not ES_URL or not ES_USER or not ES_PASSWORD:
    print("⚠️ CẢNH BÁO: Chưa cấu hình đủ Elasticsearch trong file .env")

# ==========================================
# CẤU HÌNH DYNAMODB (AWS)
# ==========================================
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

# ==========================================
# CẤU HÌNH TIMESCALEDB (AIVEN)
# ==========================================
PG_URI = os.getenv("PG_URI")

if not PG_URI:
    print("⚠️ CẢNH BÁO: Chưa cấu hình đủ TimescaleDB trong file .env")

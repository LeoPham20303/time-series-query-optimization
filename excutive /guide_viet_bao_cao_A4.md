# BỘ KHUNG VIẾT ĐỒ ÁN (CHUẨN 10-20 TRANG A4)

Sau khi có biểu đồ kết quả, đây là dàn ý chi tiết để ráp vào báo cáo gửi giảng viên môn Cơ sở dữ liệu nâng cao. Với cấu trúc này, đồ án của bạn sẽ mang tính hàn lâm, mạch lạc và chứng minh được quá trình nghiên cứu tự vấn.

## TRANG BÌA & MỤC LỤC
- Trường, Lớp, Môn học, Tên tác giả...
- Mục lục (Tự động sinh bằng Word).
- Phụ lục Hình/Bảng biểu.
- Liệt kê từ viết tắt (ES: Elasticsearch, TSDB: Time-Series Database, P95: Percentile 95).

## TÓM TẮT (ABSTRACT) - ~0.5 Trang
- Trình bày tóm tắt: Bài báo cáo này giải quyết vấn đề gì? Phương pháp giải quyết? Kết quả chính thu được là gì (VD: "Áp dụng cơ chế Filter cache và Force Merge giúp giảm x% độ trễ truy vấn...").

## CHƯƠNG 1: MỞ ĐẦU (1 - 2 Trang)
**1.1 Đặt vấn đề**
- Tình huống thực tế: Dữ liệu thiết bị GPS của xe buýt/xe tải in ra dữ liệu Event rất lớn (Append-only).
- Căn bệnh: Khi Data lớn dần, truy vấn để hiển thị web dashboard chạy chậm đi trông thấy do hệ thống không cache nổi.
**1.2 Mục tiêu báo cáo**
- Kiểm chứng hiệu quả của các kiến trúc Indexing (Hot-warm) và Caching rule trong Elasticsearch.
- So sánh hiệu năng của Elasticsearch với DynamoDB và TimescaleDB cho dạng query time-series theo thuộc tính (filter-by-key).
**1.3 Câu hỏi nghiên cứu & Giả thuyết (Trích xuất từ OVERVIEW.md)**
- Đưa 3 giả thuyết H1, H2, H3 vào.

## CHƯƠNG 2: CƠ SỞ LÝ THUYẾT (2 - 4 Trang)
**Lưu ý:** Không copy/paste định nghĩa suông, hãy giải thích dưới góc nhìn của đề tài. Tính điểm học thuật ở phần này.
**2.1 Kiến trúc Inverted-Index trong Elasticsearch**
- Giải thích Inverted index hoạt động thế nào. Tại sao ES sinh ra cho Full-text search nhưng lại được lạm dụng cho Time-series.
**2.2 Cơ chế Caching trong ES (Điểm ăn tiền nhất)**
- Giải thích sự khác nhau giữa `Must` query (Query Context - tính điểm Scoring nên không cache) và `Filter` query (Filter Context - tạo Bitsets cache siêu nhanh).
**2.3 Quản lý luồng bằng Hot-Warm Architecture**
- Giải thích mô hình vòng đời dữ liệu ILM.
**2.4 Tổng quan về Hash-Partitioning (DynamoDB) và Hypertable (TimescaleDB)**
- Viết rất ngắn về việc sao 2 DB này sinh ra dùng để lưu theo kiểu partition.

## CHƯƠNG 3: THIẾT KẾ THỰC NGHIỆM VÀ PHƯƠNG PHÁP (3 - 5 Trang)
**3.1 Chiến lược thu thập và tạo dữ liệu (Dataset)**
- Lập bảng mô tả Schema gồm các thuộc tính `companyId`, `assetId`, `severity`... 
- Vẽ biểu đồ Distribution (70% HIGH / 30% CRITICAL).
**3.2 Các kịch bản truy vấn (Scenarios)**
- Liệt kê 4 loại truy vấn S1, S2, S3, S4 (dựa theo OVERVIEW.md). Mô tả bằng lời thuật toán đằng sau truy vấn đó.
**3.3 Môi trường và Cách thức Benchmark**
- **Sự thành thật (Academic Integrity):** Trình bày thẳng thắn việc bạn scale down mô hình hệ thống để phù hợp đo lường tính chất vật lý của Query Engine thay vì Scale Cluster (Dùng 1 Shard, giảm volume dữ liệu, hoặc sử dụng hệ thống Cloud Trial để hạn chế sai số do máy tính cá nhân bị nóng).
- Nêu rõ dùng Python đo đạc, số vòng lặp 50 lần, lấy độ trễ P95 (Metric đánh giá).

## CHƯƠNG 4: TRIỂN KHAI VÀ ĐÁNH GIÁ (GIẢI PHẪU KẾT QUẢ) (4 - 7 Trang)
**Đây là chương quan trọng nhất, nơi bạn "dán" các biểu đồ đã đo đạc vào.**

**4.1 Đánh giá Baseline Elasticsearch so với Optimized Elasticsearch**
- Hiện bảng/biểu đồ so sánh độ trễ (latency) của Base vs Optimized.
- Bức hình "vàng": Chụp log giải thích kết quả. Phân tích tại sao nó cải thiện (Giải thích vì Filter Bitsets hoạt động, do Cache đánh trúng, do Force Merge đã gộp nhỏ ổ đĩa).
- Kết luận trực tiếp vào Câu hỏi H1. (Ví dụ: "H1 đúng. Giảm được y% độ trễ").

**4.2 So sánh đối chiếu chéo với DynamoDB và TimescaleDB (Cross-system)**
- Hiện biểu đồ kết nối của 3 cái DB.
- Phân tích: Trong các kịch bản S3, S4 (chỉ dò tìm đúng 1 xe), DynamoDB vì có Partition Key chắp nối `company#vehicle` nên tìm ra ngay lập tức với tốc độ < 10ms. TRong khi ES dù có cache vẫn phải dò (Scatter).
- Phân tích: TimescaleDB do chia B-Tree + Chunk trên Hypertable nên query mốc thời gian tốt nhất.
- Kết luận trực tiếp cho H2 và H3.

## CHƯƠNG 5: KẾT LUẬN & HƯỚNG PHÁT TRIỂN (1 - 2 Trang)
- Bài học cốt lõi: *"Không có Silver Bullet trong CSDL. ES rất tốt để search mở nhưng nếu chỉ filter exact-match trên data cực lớn thì cần DB có mô hình partition cứng ngắc, hoặc phải hiểu rất rõ ILM rules của ES"*.
- Hướng mở rộng nếu có tiền tệp: Scale Out trên Kubernetes, áp dụng Kafka để hứng dữ liệu trước khi đẩy vào ES.

## TÀI LIỆU THAM KHẢO
- Elastic Official Documentation.
- Các kho tài liệu báo cáo Whitepaper mà bạn từng đọc qua mạng.

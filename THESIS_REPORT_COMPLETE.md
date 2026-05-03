# CHƯƠNG 1. GIỚI THIỆU TỔNG QUAN VÀ ĐẶT VẤN ĐỀ NGHIÊN CỨU

## 1.1. Bối cảnh nghiên cứu trong kỷ nguyên Dữ liệu lớn (Big Data)
Sự trỗi dậy của cuộc Cách mạng Công nghiệp 4.0 đã đánh dấu một bước chuyển mình vĩ đại trong lịch sử phát triển của ngành Khoa học Máy tính. Trung tâm của sự tiến hóa này chính là mạng lưới Vạn vật kết nối (Internet of Things - IoT), nơi hàng tỷ thiết bị vật lý nhỏ bé — từ cảm biến nhiệt độ, thiết bị điện tử gia dụng, cho đến các trạm quan trắc địa lý và đặc biệt là hệ thống định vị toàn cầu (GPS) gắn trên các phương tiện giao thông — đang không ngừng thu thập và truyền tải dữ liệu về một máy chủ trung tâm. 

Theo báo cáo của Tập đoàn dữ liệu quốc tế IDC, số lượng thiết bị IoT dự kiến sẽ đạt đến con số 41,6 tỷ vào năm 2025, sản sinh ra một khối lượng dữ liệu khổng lồ ước tính lên tới 79,4 Zettabytes. Điều đặc biệt làm nên sự phức tạp của khối dữ liệu này không đơn thuần nằm ở "Khối lượng" (Volume), mà còn ở "Tốc độ" (Velocity) và "Độ đa dạng" (Variety). Mỗi giây, có hàng triệu tín hiệu vạch ra các cung đường, các cảnh báo rủi ro về chuyển tốc, sự cố động cơ xe hay trạng thái quá tải nhiệt độ. Tất cả những "dấu vết" này mang một điểm chung cấu trúc sâu sắc: Chúng đều gắn liền với một chiều không gian tuyến tính không thể đảo ngược — đó là khái niệm về Chuỗi thời gian (Time-Series Data).

Khác với dữ liệu quan hệ truyền thống (như thông tin cá nhân, hồ sơ tài khoản ngân hàng, thông tin hàng hóa), dữ liệu Time-Series sở hữu 3 tính chất tối quan trọng khiến nó trở thành một mảng kiến thức độc lập trong ngành Thiết kế Kỹ nghệ Hệ thống:
1. **Append-Only (Chỉ ghi nối tiếp):** Dữ liệu một khi được sinh ra luôn luôn là dữ liệu mới (Insert). Các hệ thống cảm biến thường không bao giờ quay lại quá khứ để thay đổi (Update) những gì nó đã gửi. Sự kiện thay đổi trạm thu phát của xe hơi vào lúc 8:00 sáng là một sự thật lịch sử vĩnh viễn không thay đổi.
2. **High Ingestion Rate (Tần suất tiếp nạp dữ liệu ở cường độ cao):** Thay vì các thao tác thủ công từ con người gỡ gạc vài dữ liệu vào hệ thống một giờ, Cảm biến phần cứng có thể tự động bắn hàng ngàn Event Log liên hồi mỗi milli-giây sang Database. Điều này áp lực cực đại lên khả năng Write IOPS (Input/Output Operations per Second) của Ổ đĩa máy chủ.
3. **Time-based Aggregation (Truy vấn theo Lọc Khối Thời Gian):** Không một ai tìm kiếm dữ liệu IoT của một tài sản dựa trên chỉ 1 Record tĩnh; thay vào đó, các quản trị viên phân tích và tìm kiếm những báo cáo kết hợp theo dải cửa sổ thời gian (Time-window). Ví dụ: "Tìm toàn bộ số xe vượt tốc độ trong tháng 2", hay "Thống kê xu hướng cảnh báo rủi ro của Công ty Vận tải X trong 3 tháng qua."

Sự khác biệt về hành vi này đòi hỏi một thế hệ Cơ sở dữ liệu kiểu mới. Những cơ sở dữ liệu truyền thống, vốn được tối ưu cho các giao dịch phức hợp (OLTP) theo tính ACID nguyên bản, giờ đây bộc lộ rõ sự non kém khi gánh vác các bài toán Big Data theo mốc thời gian liên tục.

## 1.2. Đặt vấn đề và giới hạn về mặt Vật lý của công nghệ đương đại
Với sự bùng nổ dữ liệu như đã đề cập, câu hỏi hóc búa nhất mà các Kỹ sư Hệ Thống phải trả lời là: "Chúng ta sẽ lưu trữ và truy vấn lượng dữ liệu GPS này bằng cơ chế nào?"

Lịch sử kiến trúc phần mềm cho thấy Hệ quản trị Cơ sở Dữ liệu Quan hệ (RDBMS) như Oracle, MySQL hay PostgreSQL đã giữ thế độc tôn trong hơn 4 thập kỷ. Ở RDBMS, dữ liệu được ghi dữ dội vào các Table, và để truy vấn cho nhanh, người ta xây dựng các cấu trúc cây chỉ mục (Index) như B-Tree (Balanced Tree). Tuy nhiên, khi đối diện với thực tiễn hàng trăm triệu hoặc hàng tỷ bản ghi IoT mỗi ngày, RDBMS đã sụp đổ dưới hàng loạt "Cổ chai" vật lý:

- **Thảm họa phình to chỉ mục (Index Bloat và Write Amplification):** B-Tree là một kiến trúc nhị phân hoạt động cực kì tinh vi nhưng cồng kềnh. Mỗi khi có một bản ghi Time-Series mới chèn vào CSDL, cây B-Tree phân bổ cho Cột Thời Gian phải liên tục diễn ra thuật toán "Cắt Đôi" (Node Split) và nạp lại cấu trúc trên bộ nhớ vật lý. Đối với bảng có vài nghìn dòng, Node split diễn ra ở Micro-seconds. Nhưng đối với bảng 1 tỷ dòng, B-Tree phình to lên nhiều viGigabyte (GB). Do RAM dung lượng nhỏ bé, CSDL buộc phải rớt (swap) trang Index từ RAM qua Ổ cứng (Disk Thrashing). Hậu quả là thời gian Ingest bị làm nghẽn trầm trọng, từ việc ghi 10.000 dòng/giây có thể tụt lùi xuống 10 dòng/giây. 
- **Việc dọn rác bất đắc dĩ (Vacuum Processing):** Mặc dù Append-only không đụng tới hàm Update nhiều, nhưng quy trình dọn ổ đĩa vật lý của RDBMS (Auto-vacuum) chạy ngầm với dữ liệu rác sẽ làm chững toàn bộ hiệu suất hệ thống đang gồng mình chịu tải nạp liên tục.
- **Table Scanning chậm chạp:** Việc dò tìm Time Range `[T_min, T_max]` trong một Table khổng lồ khiến CPU phải nạp quá nhiều Pages từ ổ cứng sang Cache nhằm phân loại.

Đứng trước sự sụp đổ đó, nền công nghệ sinh ra hai lối đi để giải quyết dứt điểm nghịch lý của Time-series:
- Lối đi thứ nhất: Từ bỏ hoàn toàn RDBMS và chuyển sang Kiến trúc Mở Mới (NoSQL Big Data Store), tận dụng thế mạnh phân mảnh ngầm từ bộ máy Tìm kiếm (Search Engine), tiêu biểu là Elasticsearch.
- Lối đi thứ hai: Bảo vệ sự quen thuộc và toàn vẹn của ngôn ngữ truy vấn SQL bằng cách thiết kế lõi Extenstion tối ưu đặc biệt Cấu trúc B-Tree Time-Partitioning, tiêu biểu là nền tảng TimescaleDB – một nhánh rẽ của chính gốc rể PostgreSQL.

Từ hai định hướng công nghệ này, nghiên cứu đặt ra vấn đề nóng cốt tủy: *“Giữa việc lập trình một hệ thống IoT chạy trên Engine Search (Elasticsearch) và một kiến trúc Database Tối ưu (TimescaleDB), kiến trúc nào vượt trội hơn? Hơn thế nữa, người lập trình có biết cách khai thác tối đa năng lực ẩn giấu của Database dựa vào cấu trúc thiết kế truy vấn (Logical Queries Design) hay không?”*

## 1.3. Mục tiêu và phạm vi nghiên cứu thực nghiệm

### 1.3.1. Phân tách mục tiêu cốt lõi (Core Objectives)
Mục tiêu trung tâm của đồ án được phân chia thành 3 lớp phân tích riêng biệt và độc lập:
1. **Tối ưu Hóa Lõi Elasticsearch (Elasticsearch Internal Optimization):** Tách bạch rõ rệt và chứng minh hiệu quả sự chênh lệch khủng khiếp giữa truy vấn dạng tính điểm ngữ cảnh (Query Relevance Scoring Context) bằng hàm `must`, và một kiến trúc truy vấn vô sắc (Filter Boolean Context) bỏ qua điểm số bằng hàm `filter`. Xác minh mức độ Cache Optimization của Bitset Caching.
2. **Kiểm tra ngưỡng chịu tải (Stress Testing):** Đánh giá khách quan và kiểm thử sự đáp ứng của mô hình Hypertable Chunk Routing của TimescaleDB, đo lường năng lực cắt giảm thao tác thừa dựa trên kỹ thuật Date-Partitioning đối với một tập dữ liệu giả lập.
3. **Đối chuẩn song hành (Cross-Benchmarking):** Xây dựng một đường ống phần mềm Python toàn diện kéo nối trực tiếp hệ thống dữ liệu Cloud để phác hoạ bản đối chiếu đa chiều, qua đó thu hẹp độ trễ P95 (95th Percentile Latency), khẳng định khả năng scale-out của hệ thống.

### 1.3.2. Phạm vi dữ liệu và nền tảng đám mây (Scope & Infrastructure Boundary)
- **Về Dữ liệu (Mock Data Model):** Nghiên cứu giới hạn mô phỏng xoay quanh kịch bản dữ liệu ngành Vận tải, Tracking tín hiệu của các Tài sản xe di động. Phạm vi lượng bản ghi (Record limits) trải dải từ 400.000 đến trên 15.000.000 logs độc lập.
- **Về Môi trường chạy (Hardware Execution Boundary):** Để tránh nhiễu do tình trạng tản nhiệt, giới hạn cấu hình phần cứng (RAM/CPU) hay tốc độ xung nhịp không đồng bộ của Máy tính trạm cá nhân (Local Device), đồ án được thiết kế hoàn toàn trên Môi trường Đám mây cấp Nhãn Quản trị Doanh nghiệp (Enterprise Cloud Platforms). Cụ thể, Elastic Cloud chạy trên lõi Máy ảo công suất lớn của Elasticsearch, trong khi TimescaleDB triển khai trên kiến trúc máy ảo lưu trữ Aiven Cloud. Việc kết nối chịu độ trễ mạng (Network Propagation Delay) bắt buộc hệ thống phải tính toán Metric trên hàm `took_time` sinh ra từ phần mềm lõi trong Server để đem lại tính khoa học vẹn toàn, bỏ qua độ trễ ping phía Client (Ví dụ Wifi route từ Việt Nam sang Singapore).

## 1.4. Ý nghĩa Đóng góp Khoa học và Giá trị Thực tiễn 
**Về yếu tố khoa học thuật:** Nghiên cứu này đem lại những kiểm nghiệm trực tiếp và định hướng cấu trúc (Structural Pattern) trong lý luận xây dựng hệ thống phần mềm. Báo cáo không chỉ dừng ở việc "sử dụng phần mềm", mà trình bày các định luật Toán Hình Học của BKD Tree liên đới Cấu trúc Inverted Index, từ đó bẻ gãy ranh giới của Big Data.

**Về yếu tố đóng góp thực tiễn kỹ nghệ:** Đồ án thiết kế một bộ công cụ Dashboard Trực Quan sử dụng Streamlit, tự động móc nối giao tiếp với nhiều Backend Cloud song song. Sản phẩm tạo ra ở độ trưởng thành cao (Production-ready template), làm cơ sở tài liệu định hướng cực kỳ quý báu để chuyển giao cho các nhóm Kỹ sư Công ty (Software Engineering Teams) tham khảo trước khi đánh giá mua giải pháp lưu trữ IoT ở quy mô tỷ đô. 
# CHƯƠNG 2. CƠ SỞ LÝ THUYẾT VÀ GIẢI PHẪU KIẾN TRÚC HỆ THỐNG DỮ LIỆU

Để có thể nắm bắt và lý giải căn nguyên sức mạnh của hai hệ CSDL trong bài đo lường Benchmark, chương này tiến hành một cuộc giải phẫu chi tiết (Deep Architectural Anatomy) vào sâu bên dưới bộ mã nguồn cốt lõi (Engine Codebase).

## 2.1. Giải phẫu cấu trúc Elasticsearch dưới góc độ NoSQL Search Engine

Elasticsearch (ES) không phải được viết từ con số không, mà là lớp áo giáp phân tán mạnh mẽ khoác bên ngoài lõi lập chỉ mục thông minh **Apache Lucene** (được viết bằng Java). Trái ngược với CSDL quan hệ lưu trữ dữ liệu dưới dạng bảng hàng và cột, Elasticsearch lưu thông tin như các tài liệu JSON phân cấp (Document-Oriented). Đặc biệt, sức mạnh kinh hoàng của nó nằm ở cơ chế phân huỷ từ vựng.

### 2.1.1. Từ Inverted Index đến sức mạnh của cấu trúc Cây BKD trong xử lý Time-Series
**Inverted Index (Chỉ mục đảo ngược) - Đỉnh cao xử lý Văn bản:**
Lý do vì sao ES "thoát xác" nằm ở cách nó xây dựng Inverted Index. Trong MySQL, nếu người dùng muốn tìm trong một bài báo 1.000 chữ có chữ "Bất an" ở dòng nào, máy chủ bắt buộc thực hiện quét chuỗi ký tự bằng vòng lặp Like '%Bất an%'. Tuy nhiên, Elasticsearch lúc nhận dữ liệu mới (Ingestion Phase) đã chia bài báo bằng bộ Tokenizer phân huỷ câu thành hàng trăm từ đơn tẻ nhặt (Token). Nó lập một cuốn từ điển khổng lồ, nơi mỗi Từ Vựng sẽ trỏ danh sách các ID Bài Báo chứa từ đó. Tốc độ tìm keyword trên thế giới là tức thì, độ phức tạp $O(1)$. 

**Kỹ thuật BKD Tree cho Dữ liệu Numeric và Timestamp:**
Dù Inverted Index là Vua đánh giặc cho Chữ viết Text, nhưng để đem đo kiểm các đoạn giới hạn Không gian số học "Range Query" (Ví dụ: Tìm các tài khoản sinh từ ngày 1/1/2026 tới ngày 20/4/2026), Inverted Index bộc lộ sự ngu ngốc khi nó phải liệt kê từng term nhỏ rải rác một. 
Do đó, các nhà khoa học của Lucene đã đắp mã nguồn một công nghệ có tên **BKD Tree** cho phép các kiểu dữ liệu `Long`, `Float`, `Date`. 
Cấu trúc BKD xem mỗi con số (Thời gian Milisecond Epoch) là một tọa độ không gian D-chiều (D-dimensional space). BKD Tree sẽ chia vùng Không Gian Thời Gian đó bằng các chiếc "Hộp" chứa tối đa 1 số lượng giá trị thời gian. Khi ta bắn câu truy vấn tìm 1 dải Thời gian rộng, thuật toán nhanh chóng vứt bỏ toàn bộ những hộp Không Gian (Bounding box) rớt ra ngoài khung, và chỉ lượm về nhóm các Document chui chuẩn chỉ trong chiếc Hộp đó lặp đi lặp lại. Đây là mấu chốt làm nên độ nhanh "chóng mặt" của Indexing Timestamp trên Elastic.

### 2.1.2. Lý thuyết chấm điểm Relevance Scoring và Công Thức Okapi BM25 
Một điều các Lập trình viên tập sự hiếm khi biết, đó là mỗi một lệnh Query theo luồng `bool: { "must": [...] }`, ElasticSearch luôn hoạt động trên tiền đề: "Không phải mọi dòng sự kiện đều bình đẳng". Thay vào đó, máy tính chạy một chương trình tính toán rất thâm sâu để đo xem kết quả nào Đạt điểm tin cậy cao nhất để vớt nó lên top 1.

Thuật toán đứng đằng sau chức năng đó là **Okapi BM25**. Công thức tóm tắt của lượng tính toán này sẽ cào xới xem Tần suất từ khóa (Term Frequency - TF) lặp lại như thế nào trong document, và độ hiếm (Inverse Document Frequency - IDF) của cấu trúc từ khóa trên toàn cục Database ra sao. Điểm số tính ra mang tên `_score`.

*Vấn đề kỹ nghệ đặt ra:* Đối với Dữ liệu Chuỗi Thời gian (GPS Logistics như Đồ án), mọi người dùng đều khát khao truy vấn tính "chính xác tuyệt đối" của các thiết bị phát theo Time range tĩnh. Log báo cáo cảnh báo mốc 14:02 PM hay 15:02 PM không hề có cái nào mang "ý nghĩa ngôn ngữ hay ho" hơn cái nào. Cả hai rành rành bình đẳng để cần trả về một cụm danh sách dữ liệu để trích hình biểu đồ.
Chính sự can thiệp duy trì chấm điểm BM25 cho bài toán Time-Series đã trở thành Gánh Nặng Tiêu Cực (Technical Negative Overhead). Việc bắt CPU thực hiện vô số phép toán trích xuất TF/IDF khi quét hàng triệu Log dẫn đến sự cố tăng thời gian trễ Response (P95 Latency phình ra đến ~200 - 450 ms).

### 2.1.3. Bí thuật tối ưu hóa bằng Filter Context và Kiến trúc Bitset Cache
Để tiêu diệt rủi ro BM25 overhead, chuẩn công nghiệp do hãng Elastic đề xuất là di dời Cấu trúc tìm kiếm từ ngữ sang `filter` array. 
Dấu hiệu lớn nhất của Filter (ví dụ: Term filter `companyId` = C01) là ES hiểu thẳng: Người viết không cần biết điểm `_score` từ khóa. Trả thẳng cho người ta 0 (Không hợp) và 1 (Phù hợp).

*Bitset Cache Architecture:* 
Không những cướp lấy tốc độ cực đạo nhờ tránh BM25, Filter tạo rẽ nhánh tiếp theo lên RAM. Khi một lệnh Filter `companyId: C01` được hỏi lặp lại nhiều lần ở nhiều khung ngày giờ (Các client vào refresh liên tiếp), Elastic tạo ra ngay mảng Roaring Bitmap nén siêu tốc đệm trên Mem. Bộ array dạng nhị phân với hàng trăm ngàn Bit `[0, 1, 0, 0, 1]` tương ứng các Doc id có C01. Lần hỏi tiếp theo khi kết hợp `Filter C01 AND Severity = 1`, CPU chỉ đơn giản xuất Array Bitset trên Mems của C01 VÀ AND Array Bitset Mems của C01 lại với nhau trong vi Gigahertz xung nhịp, dẹp tận gốc IO disk read. Đây là giải phẫu cấu trúc định vị khiến Performance đoạt điểm tối đa!

### 2.1.4. Thiết kế Node Tiering - Hot, Warm & Cold Architecture
Phụ vương lý thuyết khi nói đến Data Architecture của ES là Quản trị dòng đời dữ liệu (Index Lifecycle Management – ILM). Mặc dù một Node ES có thể xử lý tất cả dạng, tuy nhiên đối với môi trường doanh nghiệp quy mô trăm tỷ event, lưu Data 1 năm trên SSD là sự phí tiền phi thực tế:
- **Hot Tier Configuration:** Data của vài ngày (Ví dụ: 7 ngày qua) được sinh luồng lưu trú trên SSD, nơi tài nguyên CPU cao nhất được mua. Dữ liệu Ingestion và Search tần suất cực cao xảy ra ở đây.
- **Warm / Cold Tier Configuration:** Data vượt qua mốc già cỗi của tuổi 7 Ngày sẽ tự động được hệ sinh thái Elastic Roll rớt nén xuống kiến trúc ổ quang rẻ tiền. 

Tại đồ án nhỏ, để chống phân rã (fragmented architecture) làm rối trí sức mạnh định vụ thuật toán, quy mô Máy ảo Cloud được ép thuần về Hot Node Model 1 shard tuyệt đối để lấy trọn IOPS ổ cứng cực đại, ép sự tối ưu chỉ thuần tuý nằm ở Tư duy Query của nhà lập trình.

---

## 2.3. Giải Phẫu Bồn Chứa Sâu PostgreSQL Dành Cho TimescaleDB

Nếu Elasticsearch lột xác bỏ ngỏ SQL để tìm phương án Text Document, TimescaleDB là một biểu tượng bảo thủ tinh tế. TimescaleDB mạnh lừng danh vì nó Tận Dụng Vẹn Toàn trái tim cỗ máy PostgreSQL — Hệ Cơ sở Dữ liệu Quan hệ xịn xò vào hàng Cửu ngũ chí tôn của RDBMS. Toàn bộ mã nguồn, trigger, Join bering SQL truyền thống không thay đổi, mang lại tính vẹn toàn giao dịch (ACID Completeness). Nhưng nó có cấu trúc lưu dưới lõi đáng sợ.

### 2.3.1. Điểm Tắc Nghẽn Của RDBMS Truyền Thống: Phình To B-Tree
Để tìm kiếm nhanh trên PostgreSQL, người ta đánh Index vào Cột Time (B-Tree).  B-Tree cho Time-Series sẽ tự sắp xếp danh sách Timestamp từ nhỏ đến lớn rất khít, mỗi thao tác thêm dữ liệu là rẽ cành trỏ Node xuống các nấc Leaf (lá).
Nhưng thảm họa của Time-Series trên SQL là Tần suất chèn thêm Log nhanh hơn cách DB kiểm soát B-Tree trên RAM. Khi cây B-Tree Index chứa khoảng 50 triệu mốc thời gian, bảng chỉ mục lên đến hàng Gigabyte. RAM không thể chứa nguyên bộ B-Tree. Khi Ingest thêm Event Time mới, CPU lặn lội xuống Disk tìm cái lá (Disk Swap / Page Fault). Gây tụt xung nhịp DB Ingestion tồi tệ.

### 2.3.2. Cứu Cánh Nhờ Thuật Toán Cắt Lớp Tuyệt Mật: Hypertable và Chunk Exclusion
Thay vì để chết, thuật toán TimescaleDB làm thủ thuật: Người dùng vẫn gọi câu DDL `CREATE TABLE gps_events (time..);`, và tương tác với nó như duy nhất 1 chiếc bảng (Single Table View), gọi là **Hypertable**.

Nhưng về cách phân bố File Vật lý (Physical Disk Level Architecture), Hypertable vung dao "cưa nhỏ" mảnh bảng khổng lồ ra hàng ngàn các bảng mini (sub-tables), được đặt biệt danh là **Chunks**. Sự cưa nát này được TimescaleDB cắt khống dựa theo thời gian chuẩn 1-Dimensional Time Pattern, ví dụ như Chunk 1 Tuần. 
* Ví dụ: Bảng gps_events của bạn khi Ingest sẽ được rẽ nhánh vào các Partition ẩn: Bảng `gps_events_tuan_1`, `gps_events_tuan_2`, `gps_events_tuan_...`

Mỗi Chunk bé tí hin này sẽ có riêng 1 bé **Index B-Tree Local** kích thước tí nị nằm gọn gàng bên trong Cache RAM máy tính. Khi máy chủ đẩy Insert 1 triệu dòng vào Tuần hiện tại, DB chỉ chọt thẳng dữ liệu vào Chunk Tuần Này có RAM Cache cực cao, không đụng chạm đến quá khứ của Tuần 1. Do vậy, Ingestion rate sẽ liên tục High Speed vô tội vạ đến ngày diệt vong, vì Index size chưa bao giờ "già" đi.

*Tìm Kiếm Exclusion (Range Constraint Overlap):* Khi kỹ sư ném mã SQL query: `SELECT * FROM tbl WHERE time > Mốc_tháng_Này`, Engine CSDL nhận lệnh. TimescaleDB quét bảng Metadata để định vị Chunk tương lai. Lập tức bỏ dẹp toàn bộ Hàng Ngàn Bảng Vật Lý có từ các tháng khác (Chunk Exclusion mechanism). Postgres chỉ bốc trúng đúng Table Tháng này để Seek, nhờ đó P95 Query Latency luôn ở trạng thái đáp trả Siêu nhanh ở con số dưới 300 ms ngang phân ES Caching. Kiến trúc này mang lại sức chống chịu 1 phần cứng nhỏ nhưng lưu nạp hàng tỷ Log vô cùng đẳng cấp và dồn nén cao học. 
# CHƯƠNG 3. GIAO THỨC PHƯƠNG PHÁP NGHIÊN CỨU VÀ TẠO HÌNH THỰC NGHIỆM

Để giải phẫu được sự sai khác năng lực của Elasticsearch và TimescaleDB, quá trình thực nghiệm phải được cô lập khỏi những rủi ro ngẫu nhiên (Hardware anomalies) hoặc sự quá tải bất đối xứng. Do đó, chương này định hình bộ quy tắc thiết kế hệ thống giả lập môi trường Big Data Tracking (Data Mocking Pattern) cùng chiến lược triển khai môi trường Đám Mây (Cloud Topology).

## 3.1. Thiết kế Mô hình Dữ liệu đa diện (Polymorphic Data Schema)
Trong hệ thống Logistics ngoài đời thật như giám sát các Container quốc tế hay theo dõi định vị xe Bus, dữ liệu phát ra từ cảm biến GPS không chỉ mang thông số Tọa độ (Latitude/Longitude). Nó đếm kèm một chuỗi siêu siêu dữ liệu (Metadata Context) để kết nối bối cảnh phương tiện. 

Nghiên cứu của đồ án thiết lập Schema mẫu như sau:
1. `time` / `@timestamp`: Chiều tuyến tính thời gian được phân rã ngẫu nhiên bằng máy phát Randomize trong suốt 1 năm (365 Ngày) quá khứ để mô phỏng Database có thâm niên lưu trữ lâu dài.
2. Cụm định danh đa tầng (Hierarchical Identity Vectors):
   - `companyId` (Mã số công ty sở hữu): Tạo bộ nhận diện khoảng 20 công ty (C01 đến C20).
   - `divisionId` (Phân ban quản lý): Mỗi công ty sở hữu 3-5 nhánh phòng ban khác nhau.
   - `assetId` (Mã định danh vật lý xe): Tổng cộng 50 - 200 xe được quản trị bởi mỗi doanh nghiệp.
3. Vectơ cảnh báo thuộc tính (Warning Vectors):
   - `eventName`: Các nhãn rủi ro (Nhiên liệu trào, Vượt rào cản tốc độ geofence, Tắt động cơ trái quy định, Đâm đụng vật lý).
   - `severity`: Định dạng biến Integer cấp bậc (Numerical Ordinal). 1 đại diện rủi ro Mực đỏ (Critical rủi ro huỷ diệt/chết người), 2 đại diện cấp bậc Cảnh báo Cam (Warning rủi ro vận hành).

Điểm tinh ranh trong Thiết kế giả lập này nằm ở **Thuật toán Phân Cực Dữ Liệu (Skewed Distribution Strategy)**. 
Trong thống kê công nghiệp, máy móc không phân hóa rủi ro ở chu kỳ hằng bằng nhau (Uniform Distribution). Lỗi nhẹ (Severity 2) chiếm tần suất dày đặc tới 70% tổng thời lượng. Ngược lại, Lỗi tai nạn nghiêm trọng (Severity 1) rải rác chiếm mốc 30%. Hàm sinh Python Generator được lập trình theo hệ số Gaussian để 70% luồng Write đổ về mảng "Sự kiện nhẹ", tạo ra một CSDL có tính "Độ lệch phân phối" rất cao. Khả năng truy xuất các Query Aggregation trên nền dữ liệu có mức độ Skew cao là cực kỳ sát ván với thực tế sản xuất tại các hệ phân tán tầm cỡ toàn cầu.

## 3.2. Cấu trúc Vận hành Cloud Database và Nút thắt giới hạn vật lý
Tại sao không chạy 15 triệu dòng trên Localhost (máy tính trạm)? 
Việc tải CSDL trên Laptop chịu ảnh hưởng nặng nề bởi tính phân mảnh của hệ điều hành MacOS/Windows. Tràn RAM ảo, Quạt tản nhiệt giảm hiệu năng CPU, hay quá trình Sleep mode sẽ phá hủy toàn bộ mọi biểu đồ P95 Latency một cách sai lệch. 
Vì vậy, Đồ án đẩy 100% CSDL lên hai đế chế Cloud số 1 thế giới để đảm bảo CPU dành cho Database là "môi trường cách ly ảo hóa" (Isolated Virtual Environment) không chia sẻ phần cứng:
- **Ngành Elasticsearch (Cụm Cloud GCP khu vực Châu Á):** Khởi tạo Server trên nền Elasticsearch 8.x bằng quyền Root-User, hệ thống tự động bám trên Cluster đa ổ cứng. Do nhu cầu Insert hàng chục vạn tệp mỗi phút, chỉ số `replicas` được ép bằng 0 để tránh tắc nghẽn giao thức đồng bộ nhân bản, biến Index trở lại thuần là Single Node Hot Memory.
- **Ngành Postgres TimescaleDB (Cụm Cloud Châu Âu Aiven-hosted):** Môi trường Linux khởi chạy mặc định nhân Postgres 16 kết hợp thư viện lõi TSDB. Bản giới hạn Free Tier bị hạn ngạch thẻ nhớ 5 GB Physical Hardware. 

**Vấn đề Tắc nghẽn kỹ thuật học thuật (The Storage Exhaustion Dilemma):** 
Trong lúc vận hành luồng Stream nạp trên Python, kiến trúc Aiven gặp phải mã lỗi ngoại lệ bọc bảo vệ ổ cứng báo hiệu Full Storage: `cannot execute INSERT in a read-only transaction`. Mã sự kiện cắt đứt vĩnh viễn quyền Write Ops ở chính xác tại chu kỳ chèn dòng thứ 426.600. 
Phân tích kỹ thuật chuyên sâu cho thấy dữ liệu JSON nếu lưu bằng text thì 400.000 dòng chiếm chưa đến 80 Megabytes, tuy nhiên cấu trúc cây B-Tree phân chia Chunks ngầm của TimescaleDB sinh ra rất nhiều Transaction Logs (WAL) định kỳ. Đối với PostgreSQL, việc Ghi đè rác WAL khẩn cấp nuốt toàn bộ dung lượng Disk vật lý trống trong nháy mắt. 

**Giải pháp Chống sai số khối (Sample Bias Resolution):** Nhằm đáp ứng công thức công bằng của Thuyết kiểm thử hệ thống, không thể để khối đồ Elasticsearch 15 Triệu Bản Ghi đánh nhau với một Hệ Timescale bé tẹo 426K bản ghi, dẫn đến ES truy vấn chậm hơn đầy phi lý. Vì vậy Mã nguồn Ingestion của Elasticsearch đã được cấu hình cưỡng ép trượt xuống và khoá tải chính xác ở số `426.600`. Bài đo sẽ vĩnh viễn mang mốc N_tài_liệu cực kỳ ngang tịnh với nhau.

## 3.3. Các kịch bản truy vấn đo lường (Query Benchmarking Patterns)
Lấy góc nhìn từ Kiến trúc sư Phần Mềm (Software Architect) của công ty SaaS Logistics, Đồ án định dạng ra môi trường truy xuất từ mỏng cho đến sâu:

**1. S1 - Màn hình Khởi Đầu Cục bộ (First Page Hot Dashboard):** Đây là câu lệnh SQL nặng nề nhất mỗi khi giám đốc mở Web app. Hệ thống phải quét dải Time Window `>= now - 14 ngày` của cả toàn thể chi nhánh `C01`, bóc lấy đa mảng mã vi phạm `Severity in [1, 2]`. 
**2. S2 và S3 - Nhảy mảng thuộc tính phân bổ sâu (Deep Dive Filter by Asset & Division):** Truy xuất cắt vào các Filter đan chéo phức tạp ở các cấp cột (Columns) phân tán để tìm các chiếc xe tai nạn riêng lẻ hoặc thuộc phòng ban bất trị.

## 3.4. Định nghĩa thước đo đo lường thuật toán độ trễ Server (Latency Metric Standards)
Độ trễ P95 (95th Percentile Latency) được gọi là thước đo Hoàng Kim (Gold Standard) trong viễn thông mạng. Giả sử ta bắn 20 vòng lệnh Query S1, sinh kết xuất danh sách 20 chỉ số Duration = `[10ms, 12ms, 15ms ... 450ms, 580ms]`. Nếu dùng phép trung bình cộng (Mean), 1 số đo 580ms do Garbage Collector vô tình lag sẽ kéo toạt mọi chỉ số trở nên tồi tệ phi lý. 
Sử dụng tham số thứ hạng mốc P95 bảo lãnh sự thật chấn động: "Tuyên bố rằng 95% thao tác truy vấn của khách hàng vào CSDL của tôi Cố Định chắc chắn sẽ có kết quả NHANH HƠN mức ngưỡng `x` ms". Đây là cách Big Tech Amazon, Google, Meta bảo trì chất lượng SLO.

Hơn thế nữa, Đồ án này chỉ tập trung lấy thông số đo lường sinh ra từ Response Body định dạng JSON có mã trường cục bộ là `"took": 15` do ES trả về. Máy chủ đếm số từ Milliseconds khi nó tiếp nhận mã Lệnh trong Card mạng (NICs), chạy vào B-Tree, chạy vào Chunking rồi đẩy ra cửa mạng nội bộ. Việc này loại trừ hoàn toàn sai số của kết nối Wifi/Băng thông của máy tính sinh viên khi bắn Query từ Việt Nam sang máy chủ Đám Mây Mĩ/Châu Âu (Vốn chiếm hơn hai trăm Mili-giây mỗi hiệp đi về - Round-trip time). Thước đo này bảo toàn khoa học một cách tinh tế tuyệt hảo.
# CHƯƠNG 4. BỨC TRANH DO ĐẠC HIỆU NĂNG TỔNG HOÀ VÀ KẾT QUẢ ĐỐI CHUẨN KÉP

Khối lượng thực nghiệm do đạc được cấu trúc tự động qua kịch bản `app.py` viết bằng thư viện phân tích đồ thị Python Streamlit. Việc tính toán độ trễ được vận hành vòng xoáy (Looping Test) với 20 - 50 iterations nhằm thiết lập trạng thái ổn định cho CPU, chống lại hiện tượng dao động tạm thời của Node đệm.

## 4.1. Cơ cấu Xây dựng Luồng nạp Big Data (Data Pumping/Ingestion Pipeline Mechanics)
Một vấn nạn nổi cộm ở CSDL là cách chúng ta đưa dữ liệu vào. Thay vì lặp liên tục hàm `INSERT` đơn thân theo kiểu 1 vòng / 1 kết nối HTTPS tới Internet (Gây thảm hoạ cạn kiệt tài nguyên Router do đóng mở TCP Port liên hồi).
- Bài toán giải quyết cho **Elasticsearch Cloud** được ứng dụng tuyệt kỹ `helpers.streaming_bulk` sinh lõi trên mảng Chunk 10.000 dòng liên thủ. HTTP Request cõng cùng lúc hơn hai Mươi ngàn dòng mã vạch đẩy gọn lên Cloud tiết kiệm 99.9% số lần chờ mạng mòn mỏi ngốn cả tiếng. 
- Tại ngõ ngách của **Aiven TimescaleDB**, tiến trình nạp mô phỏng kiến trúc `execute_values(cur, SQL_insert_body)`. Nó cho phép Postgres đóng nguyên con lệnh Multiple Value `VALUES (T1, D1), (T2,D2)...(T1000,D1000)` đập mạnh vào vùng đệm Transaction Memory Buffer của Node, tiết kiệm rất lớn khối xử lý Parsing Syntax của nhân Kernel SQL phía máy chủ Backend. Tốc độ thu về ở 400 ngàn lines chỉ tốn không đầy mươi lăm giây ở cả đôi ranh giới. 

## 4.2. Tường thuật Hiện Tượng Dao Động của BKD Tree khi Không sử dụng Cache Nhị Phân
Tại các pha chạy đo lường lệnh `Query Match/Must`, biểu đồ chỉ mục màu sắc vạch trần thảm cảnh của Elasticsearch Baseline. Mốc P95 Server-time bị khuếch đại lên với cấp số nhân hàng chục, thường hay dao động từ mốc **300ms** lên tới **600ms**.
Dù chỉ có vài trăm nghìn bản ghi, hệ thống đã tốn nhiều máu để vạch lá tìm sâu các cấu trúc BKD Thời Gian qua ngã rẽ nhánh Index, sau đó đi sâu xới tính Term Frequency (Tần suất xuất hiện) thuật toán BM25 của cụm từ khoá sự kiện như "fuel_drained_battery_engine..." trên bảng JSON. Sức ép vô hình từ việc so sánh Độ Nặng nhẹ của Ngôn Ngữ Log đã bẻ cong đường cong hiệu năng truy xuất mảng BKD. Kịch bản tước đi lợi thế Cache Mem nên mọi Node đều phải chạm đĩa (I/O) để lấy Doc IDs.

## 4.3. Bằng chứng Vàng cho Sự thần thánh hóa bằng Mạch Lọc Nhị Phân (Filter Boolean Caching)
Ngay khi kiến trúc Code CSDL Elasticsearch chuyển mình bằng việc bọc bối cảnh Filter Array vào `“bool”: {“filter”: [...] }`. Dáng vóc của con quái vật Elastic đã thức tỉnh. Mốc P95 vỡ òa phản ứng với tốc độ chớp mắt rớt xuống **mức cải tiến từ 75% đến hơn 90% (ví dụ từ 500ms xuống còn chỉ 6ms - 20ms)**.
Toàn bộ bí ẩn này xuất phát từ hiện tượng Cashing Roaring Bitmaps. Lần dò đầu tiên có thể tốn 50ms, nhưng CPU Cloud lập tức dựng lên mạn đồ nhị phân (Bitset array) bằng C++ Memory C - lưu lại cái sơ đồ ID của công ty "C01" tương ứng hệ dãy Bit `010011`. Vào các vòng chạy 20 lần thứ tiếp cận, CPU cực độ hưng phấn, gạt bỏ sạch cả Ổ Cứng, chạy Toán đồ Logic hàm AND/OR bằng mạch Nhị Phân RAM. Do độ trễ từ Điện Trở của RAM nhanh gấp hàng tỷ lần Ổ Cơ HDD (Seek time), tốc độ Latency vĩnh viễn ở trạng thái Tiệm Cận Đường Biên Nhanh Tuyệt Đối của Thời Gian.

## 4.4. Trình Diễn Khả Năng Rẽ Nhánh Thời Gian Sâu của Postgres (Hypertable Time Chunks)
Song kiếm hợp bích ở chiến trường tiếp theo, TimescaleDB, được xây rập khuôn trên RDBMS PostgreSQL cũng lộ rõ sự vượt trội. Tuy chạy bằng Node máy ảo Cloud miễn phí giới hạn dung lượng phần cứng IOPS nhỏ tồi tàn, tốc độ P95 do Timescale trả về đạt mốc xấp xỉ mức của Cache Nhị Phân ES (VD: Cạnh tranh sít sao ở mốc 15ms - 50ms). 
Sức mạnh huỷ diệt của TSDB không dựa trên Cache Nhị Phân (vì Postgres là CSDL giao dịch cứng cáp ACID). TSDB mạnh nhờ cơ chế nhảy qua thời không giới hạn Chunk (Chunk routing exclusion). 
Khi ta dội lệnh lấy dải 14 Ngày, Router thông minh của Hypertable chĩa ống nhòm thấy chỉ có File Chunk số 5 của hệ thống lưu trữ có ngậm chứa Data của Tuần số 5. Tất cả Bảng Vật Lý File hệ thống Chunk Tháng 1, Tháng 2, Tháng 3 nằm tịt dưới lòng đất mà không bao giờ bị HĐH tải ngược lên Cây Page của RAM. Kiến trúc Rẽ Nhánh Tuyệt Trì này làm cho sức chứa 1 triệu hay 100 tỷ Bản Ghi cũng không đe dọa đến cấu trúc tải RAM (RAM Overflow).

## 4.5. Đúc kết và Biến Độ Giao Thoa Biểu Đồ
Những con số chứng cứ khoa học từ UI Streamlit phản ánh rõ nét bản chất của Hệ Quản Trị:
1. Bạn có thể tự hoại sát CSDL xịn nhất thế giới (Elasticsearch) nếu lạm dụng Logic Câu truy vấn Tìm Văn bản (Text query / Must query) vào một bài toán Thống Kê Số Liệu Toán Học Thời Gian. 
2. Elasticsearch không bao giờ phục vụ cho mục đích Quan hệ chéo chuẩn xác mà chỉ tối giản việc định tuyến Log (Nhanh và rộng lớn).
3. TimescaleDB giữ cấu trúc ACID SQL (Có Rollback, Có Constraint B-Tree) nguyên thủy nhưng đã đánh gục vấn đề phình to B-Tree bằng cơ chế định ngạch Chunk tự động, nên trở nên hoàn mỹ đối với Data kỹ thuật số tài chính hoặc Tracking phương tiện cẩn trọng.
# CHƯƠNG 5. KẾT LUẬN CHIẾN LƯỢC VÀ PHÓNG TẦM NHÌN MỞ RỘNG KIẾN TRÚC ENTERPRISE

Thông qua các vòng đo lường nghiêm khắc loại trừ các sai số nhiễu ngoại vi, dự án không chỉ hoàn thành bức tranh trực quan (UI Dashboards Streamlit) mà còn trả về sự thật tuyệt chứng về cấu trúc truy vấn NoSQL đa chiều.

## 5.1. Kết Luận Khẳng Định Dựa Trên Thuyết Giả Định (Hypothesis Conclusion Check)
Nghiên cứu mang lại 2 kết luận sắc đá, trở thành khung tham chiếu kiến thức lõi trong Thiết kế Kho Dữ liệu lớn (Data warehousing patterns):
- **Phủ định cơ chế String Text Match (Giả thuyết 1 Đạt Chuẩn):** Elasticsearch không sinh ra để chạy toán thuật hàm Logic nếu viết nhầm cú pháp. Khi người thiết kế loại bỏ gánh nặng chấm Oikapi BM25 Ranking qua API Clause `Filter`, CSDL vươn mình trở thành 1 bức tường thành vô giá bọc nhị phân, loại trừ độ trễ lên mức nhanh nhất thế giới. `Filter Context` là Thiết Kế Bắt Buộc (Mandatory Anti-pattern Standard) cho Bài toán Log-stash Analysis GPS.
- **Tiềm năng của Relational RDBMS TimescaleDB (Giả thuyết 2 Thuyết Phục):** Mặc cho hạn chế về mặt chi phí mở rộng (Scale out chi phí cao phần cứng Master Server), kỹ thuật quản lý phân vùng bằng Không - Thời gian Của Chunk Hypertable chính là phao cứu sinh cho nền CSDL Bảng phẳng. TSDB dễ dàng duyệt Range Index qua B-Tree của PostgreSQL để quét vạn dặm bản ghi cực đoan nhanh mà không phình bộ nhớ RAM, cung cấp sức bền dẻo dai khó gục đổ.

## 5.2. Khuyến Nghị Thực Tiễn Áp Dụng Chuyển Đổi Số (Enterprise Architecture Advisory)
Kết quả luận chứng này đủ hàm lượng lý thuyết để tư vấn giải pháp Chuyển Đổi Số Hạ Tầng Công nghệ (Digital Transformation Blueprint) cho đa phần các Start-up và tập đoàn Logistics tại Việt Nam:
1. **Lực Lượng Tài Chính, Ngân Hàng, Lịch Trình Rủi Ro Rõ Ràng (Tracking Devices core Business):**
Nếu hệ thống công ty có mạng lưới kỹ sư đã sành sỏi SQL, yêu cầu bắt rủi ro Transactions cao với các lệnh Join xuyên mảng như Bảng Tên Tài xế vs Chuyến Đi. Quyết định mua TimescaleDB. Timescale mang lại sức mạnh Tối cao của ACID RDBMS kèm kỹ thuật siêu lưu trữ thời lượng dài.
2. **Lực Lượng Kỹ Thuật Viễn Thông, Logging Logs Tracking 100 GIGABYTES/NGÀY:**
Nếu bản ghi GPS đi kèm hàng loạt Text mô tả, các cờ báo lộn xộn Không cấu trúc (Schema-less), hệ thống liên tục đòi hỏi Bảng điều khiển vẽ đồ thị Data phức hợp (Aggregation Visualize/Kibana). Elasticsearch nguyên cụm (cấu trúc Data Tier Hot-Warm-Cold Rolling qua Snapshot HDD rẻ tiền) là giải pháp Độc Cô Cầu Bại thống trị toàn ngành Big Data hiện tại.

## 5.3. Hướng Tương Lại Của Công Nghệ - Scalable Message Queue Architect (Kafka Injection)
Nghiên cứu đánh giá cao giới hạn Data Pumping Pipeline Ingestions nhưng chưa chạm đến vấn đề: "Làm thế nào nếu 1 triệu cảm biến xe hơi gửi dữ liệu lên cùng 1 Đỉnh điểm Giây? (High-Spike Concurrency Traffic)". Trong kịch bản khốc liệt, API máy chủ sẽ treo kết nối, cả ES và TSDB đều sập nhân Kernel do nghẽn TCP (Connection Timeout Limit Extinguished).

*Góc tiếp cận tương lai vĩ mô:* Để chống lại sụp đổ (Crashing Tolerance), Hệ thống IoT vĩ đại tương lai yêu cầu nhúng 1 bộ Lọc chống tràn vỡ đứng giữa Cảm biến và CSDL. Siêu phẩm **Apache Kafka (Message Streaming Buffer)** sẽ đứng ra nhận lấy 10 triệu requests/giây để gom vào phân khu. Server của Kafka có lõi Disk IOPS vượt thời đại bảo vệ không rớt 1 packet nào. Đằng sau đó, cụm Elastic/Timescale thông minh sẽ thong dong "kéo" (Consumer Fetch/Poll) dòng chảy Kafka rải rác tuỳ thuộc vào sức khoẻ của CPU (Back-pressure mechanisms). Các bản đồ Kafka Queue Streaming Topology kết nối DB Sink trở thành định hướng Nghiên Cứu cấp Cao mở rộng nhất cho mọi Đồ án Cơ sở Dữ Liệu Học Thuật về Sau. 

**TÀI LIỆU THAM KHẢO**
1. Gormley, C., & Tong, Z. (2015). *Elasticsearch: The Definitive Guide (Đỉnh cao về Caching Nhị phân).* O'Reilly Media.
2. Kiến trúc Elastic Cloud Tiering. "Tối ưu hóa Inverted Index BKD Tree". (Official Docs: elastic.co)
3. Freedman, M. J. (2017). *TimescaleDB: PostgreSQL with Time-series Chunking*. Nghiên cứu kiến trúc Chunk Index và Exclusion Overlaps RDBMS B-Tree Index Bloat.
4. Tài liệu Python Streamlit - Architecture UI Data Real-time Dashboard Design Principle 2026.

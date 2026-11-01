# Nhật ký sửa bản nội dung Ứng dụng 2 — v2

Ngày sửa: 01/11/2026. Bản gốc: `Ban-giao-Wikispeedia-2026-11-01/02_Noi_dung/Noi-dung-day-du-Ung-dung-2-Wikispeedia.md`, giữ nguyên để không làm sai checksum của gói bàn giao. Bản sửa: [Noi-dung-Ung-dung-2-Wikispeedia-v2.md](Noi-dung-Ung-dung-2-Wikispeedia-v2.md).

Sáu mảng nội dung, dataset Wikispeedia, ví dụ A/B/C/D/X và các số liệu khảo sát được giữ nguyên. Không thêm kết quả thực nghiệm nào.

## 1. Quyết định đã chốt ngày 01/11/2026

| Điểm | Quyết định | Ảnh hưởng tới nội dung |
|---|---|---|
| Duyệt nội dung | Sửa nội dung trước, người dùng đọc lại rồi mới làm thực nghiệm | Bản v2 này là bản để duyệt |
| Công cụ | Tự cài đặt GSP và PrefixSpan bằng Python | Mục 3.7 mới; mục 5.2, 5.5, 5.6 viết lại |
| Đánh giá hữu ích | Có: train/test theo đường đi, Hit@3 + coverage, baseline trang phổ biến; không thêm Markov | Mục 5.10 viết lại; mục 1.4, 1.5, 4.7 bổ sung |
| Nơi chạy | Đo chính trên máy cục bộ; notebook giao để chạy lại trên Kaggle | Mục 6.7 cập nhật |

## 2. Các thay đổi và lý do

| # | Mục | Thay đổi | Lý do |
|---|---|---|---|
| 1 | Đầu tài liệu | Ghi trạng thái v2, các quyết định và thêm quy ước nhãn [Nguồn]/[Khảo sát]/[Minh họa]/[Thiết kế]/[Chưa có] | Yêu cầu bàn giao: tách rõ nguồn chính thức, số liệu tự khảo sát, ví dụ tính tay và phương án đề xuất |
| 2 | 1.4, 1.5 | Tách câu hỏi thứ hai “gợi ý dựa trên mẫu có hữu ích hơn baseline không?”; nói rõ đánh giá offline không đo trải nghiệm người dùng | Đáp ứng mục “so kết quả trên tập test với baseline” trong luồng Notion của nhóm, đồng thời không trộn với câu hỏi so thuật toán |
| 3 | 2.1 | Ghi hai công trình nguồn của dataset theo SNAP | Bản cũ chưa trích dẫn nguồn gốc dataset |
| 4 | 2.6 | Thêm cờ “lượt đến từ quay lại” cho từng lượt ghé, chỉ dùng khi đánh giá | Trang đến sau `<` là trang đã có trong lịch sử, dễ đoán hơn; cần báo cáo riêng lượt tiến để không thổi phồng Hit@3 |
| 5 | 3.2 | Support = số đếm tuyệt đối sup; rsup = sup/\|D\|; ngưỡng nhập dưới dạng r rồi đổi thành min_sup = ⌈r·\|D\|⌉ bằng phép tính chính xác | Thống nhất với Content-v4 của nhóm (support là số đếm). Ví dụ lỗi số thực đã kiểm tra: 0,07 × 100 = 7,000000000000001 trong Python |
| 6 | 3.3–3.6, 4.5, 4.6, 4.8 | Đổi cột/ghi chú “Support” thành “sup (số chuỗi)” và “rsup” | Hệ quả của thay đổi 5; số liệu ví dụ không đổi |
| 7 | 3.4 | Viết lại GSP theo paper: quét dữ liệu mỗi mức, pha nối (bỏ item đầu của s₁ = bỏ item cuối của s₂), pha cắt tỉa (mọi chuỗi con khi không có max-gap), hash tree; tính tay 9 ứng viên mức 2 trong đó 6 có sup = 0 | Bản cũ chưa đối chiếu paper (việc A1 của bàn giao). Đã đọc mục 3, 3.1, 3.2 của Srikant & Agrawal 1996 |
| 8 | 3.4 | Thêm ước lượng 579² ≈ 335 nghìn và 1.123² ≈ 1,26 triệu ứng viên mức 2 ở r = 0,2% và 0,1% | Tính từ `wikispeedia_all_items.csv` của khảo sát (ngưỡng trên 76.193 đường đi). Giải thích vì sao cần chạy thử khả năng hoàn thành |
| 9 | 3.5 | Thêm vị trí khớp sớm nhất, pseudo-projection và kết quả so sánh của paper PrefixSpan như một giả thuyết | Đã đọc tóm tắt, mục 3.3 và tổng kết mục 4 của Pei và cộng sự 2004. Ghi rõ đó là kết quả của paper, không phải của bài |
| 10 | 3.7 (mới) | Mô tả cài đặt Python: cùng đầu vào/đầu ra, chỉ S-extension vì mỗi event một trang, cây tiền tố thay hash tree, pseudo-projection, 4 lớp kiểm tra tính đúng (tính tay, biên, vét cạn, SPMF) | Quyết định công cụ ngày 01/11. Bản `spmf.jar` mới cần Java 25 (class major 69) trong khi máy có Java 8 |
| 11 | 4.5 | Nói thẳng C(h,y)/C(h) là ước lượng kiểu Markov/n-gram bậc m; mẫu đóng vai trò lọc; bài không so với Markov | Tránh trình bày quy tắc như một phương pháp mới; giữ phạm vi “không thêm Markov” đã chốt |
| 12 | 4.6 | Ghi rằng ví dụ ⟨A,B⟩ có C(h)=3, sẽ bị ngưỡng thực nghiệm C(h) ≥ 5 loại | Tránh hiểu nhầm ví dụ là ca thật của thực nghiệm |
| 13 | 4.7 | Cố định quy tắc gợi ý: ngữ cảnh 3→2→1, C(h) ≥ 5, C(h,y) ≥ 2, dùng ngữ cảnh dài nhất có ứng viên, thứ tự xếp hạng, không dò ngưỡng trên test | Bản cũ để trống ngưỡng; đánh giá test cần quy tắc được chốt trước khi xem test |
| 14 | 5.2 | Thay đề xuất SPMF bằng hai bản Python; ghi lý do không dùng SPMF để đo; giữ SPMF làm đối chiếu tính đúng | Quyết định công cụ; rủi ro runtime Java 25 |
| 15 | 5.3 | Quy tắc khi một mức quá nặng: vẫn chạy cả hai, ghi timeout, chỉ thay mức khi cả hai không hoàn thành | Tránh bỏ bớt cấu hình bất lợi cho một nhánh |
| 16 | 5.4 | Thêm chia train 80% / test 20% theo đường đi từ cùng thứ tự xáo trộn; ghi giới hạn cùng IP có thể ở cả hai phía | Thiết kế đánh giá test |
| 17 | 5.5 | Đo bằng `time.perf_counter()` trong tiến trình Python mới cho mỗi lượt; bộ đếm giờ ở chương trình bao ngoài | Thay mô tả JVM bằng môi trường thật sẽ dùng |
| 18 | 5.6 | Bộ nhớ = đỉnh cấp phát Python bằng `tracemalloc`, đo ở lượt riêng vì làm chậm chương trình | Thay heap JVM; nêu rõ loại bộ nhớ được đo |
| 19 | 5.7 | Lịch đo: 1 khởi động + 3 lượt thời gian + 1 lượt bộ nhớ, đổi thứ tự chạy theo lượt; bỏ lượt đo nếu lượt khởi động đã timeout | Cụ thể hóa thiết kế đo |
| 20 | 5.8, 5.9 | Nối với 4 lớp kiểm tra; thêm cột số ứng viên GSP đã sinh vào bảng kết quả | Giúp giải thích chênh lệch bằng cơ chế |
| 21 | 5.10 | Viết lại thành thiết kế đánh giá đầy đủ: ca kiểm tra, ba phương án, Coverage/Hit@1/Hit@3, so trên cùng tập ca, tách lượt tiến, r = 0,2% chính và độ nhạy, quy tắc chọn ca minh họa | Quyết định đánh giá ngày 01/11 |
| 22 | 6.5, 6.6, 6.7 | Cập nhật giới hạn: đánh giá offline, không dùng trang đích, thời gian tuyệt đối của Python, chỉ hỗ trợ event một item | Hệ quả của các quyết định trên |
| 23 | Tham khảo | Thêm 2 paper dataset và 2 paper thuật toán, ghi rõ phần nào đã đối chiếu; sửa liên kết tương đối về gói bàn giao | Bản cũ chưa có paper gốc trong danh mục |

## 3. Nguồn đã kiểm tra thêm trong lần sửa này

- Srikant & Agrawal 1996, PDF do SPMF dẫn: lần sửa 1 chỉ đọc mục 3, 3.1, 3.2 (cấu trúc nhiều lượt quét, nối/cắt tỉa, hash tree). Lần sửa 2 đã đọc toàn văn (xem mục 5).
- Pei và cộng sự 2004, PDF do SPMF dẫn: lần sửa 1 chỉ đọc tóm tắt, mục 3.3 (pseudo-projection) và đoạn tổng kết mục 4. Lần sửa 2 đã đọc toàn văn (xem mục 5).
- Trang SNAP Wikispeedia: bảng thống kê (4.604 bài, 51.318 hoàn thành, 24.875 chưa hoàn thành, 119.882 liên kết) và mục “Sources (citations)”. Trang không mô tả ký hiệu `<`; cách hiểu `<` vẫn lấy từ header của tệp trong archive như bản khảo sát.
- Trang SPMF GSP/PrefixSpan: GSP có tham số độ dài tối thiểu/tối đa; chưa cài ràng buộc gap/window.
- `spmf.jar` tải ngày 29/10/2026 (SHA-256 `4aa46838…dfe6a`): lớp `ca/pfv/spmf/gui/Main.class` có class major version 69, tức cần Java 25 trở lên. Máy cục bộ có Java 1.8.0_511.

Hai paper dataset (West & Leskovec 2012; West, Pineau & Precup 2009) chỉ được trích dẫn theo SNAP, chưa đọc toàn văn.

## 4. Việc còn lại sau khi bản v2 được duyệt

1. Tạo tập dữ liệu thực nghiệm (70.968 chuỗi dự kiến), các tập con và train/test; báo cáo số đếm thật sau lọc.
2. Viết hai bản cài đặt, chạy 4 lớp kiểm tra tính đúng.
3. Chạy thử khả năng hoàn thành, chốt giới hạn thời gian, rồi đo chính.
4. Chạy đánh giá test với baseline; chọn ba ca minh họa theo quy tắc cố định.
5. Điền kết quả vào mục 4.8, 5.9, 5.10, 6.7; giữ nguyên các giới hạn kết luận.
6. Giao notebook chạy được trên Kaggle cùng hướng dẫn.

## 5. Lần sửa 2 (01/11/2026): rà công thức sau khi đọc toàn văn hai paper

Lý do: các công thức sẽ bị hỏi khi trình bày, trong khi lần sửa 1 mới đọc một phần hai paper thuật toán. Lần này đã đọc toàn văn cả hai bản PDF:

- GSP: bản EDBT 1996, 15 trang.
- PrefixSpan: bản IEEE TKDE 2004, 17 trang.

Các trang có định nghĩa và công thức được xem trên hình trang gốc, vì bản trích chữ làm mất ký hiệu toán. Mọi con số trong tài liệu được tính lại bằng code. Ví dụ 5 chuỗi được đếm vét cạn và cho đúng 7 mẫu. Các ngưỡng, tỷ lệ phần trăm, số trang đạt ngưỡng (579 và 1.123) và phép chia 56.774/14.194 đều khớp.

| # | Mục | Thay đổi | Lý do |
|---|---|---|---|
| 24 | 3.1 | Định nghĩa ký hiệu P ⊑ S bằng công thức có cận 1 ≤ i₁ < … < i_k ≤ n; nêu định nghĩa gốc dạng a_j ⊆ b_{i_j} và vì sao nó thu về dấu bằng; thêm bảng đối chiếu ký hiệu với hai paper | ⊑ được dùng ở mục 3.2 nhưng chưa định nghĩa. PrefixSpan dùng chữ S cho cơ sở dữ liệu, dễ nhầm với S là một chuỗi |
| 25 | 3.2 | **Sửa lỗi:** sup được đếm trên tập cặp (sid, S) thay vì tập chuỗi {S ∈ D : …} | Viết theo tập chuỗi sẽ gộp các đường đi trùng nhau. Ví dụ S1 = S3 = ⟨A,B,C⟩ làm sup(⟨A,B⟩) ra 3 thay vì 4. Paper PrefixSpan dùng bộ ⟨sid, s⟩ |
| 26 | 3.2 | Chứng minh một dòng vì sao dùng ⌈r·\|D\|⌉: sup nguyên nên sup ≥ ⌈r\|D\|⌉ ⇔ rsup ≥ r. Ghi rõ dấu ≥ theo PrefixSpan, và cách paper GSP diễn đạt khác (“greater than”; support khi là tỷ lệ, khi là số chuỗi) | Câu hỏi dễ gặp: vì sao làm tròn lên, và vì sao ≥ |
| 27 | 3.4 | Viết pha nối thành công thức; thêm tính chất Apriori dạng P′ ⊑ P ⇒ sup(P) ≤ sup(P′) kèm lý do bắc cầu; ghi ở mức 2 pha cắt tỉa không loại được gì; giải thích từng bước nối ở mức 3 và 4 | Trước đó chỉ mô tả bằng lời |
| 28 | 3.4 | Phân biệt số ứng viên mức 2: GSP gốc n² + n(n−1)/2 (ví dụ: 12; Wikispeedia: 502.572 và 1.891.132), bài chỉ mở rộng chuỗi nên n² (9; 335.241 và 1.261.129) | Paper PrefixSpan có ví dụ 51 = 6×6 + 6×5/2; nếu không ghi rõ, số 9 và 579² sẽ bị cho là sai |
| 29 | 3.4 | Giải thích “contiguous subsequence” của GSP là vị trí trong mẫu, khác “liền kề trong đường đi”; phần 4 đổi “liên tiếp” thành “liền kề” | Tránh hai khái niệm khác nhau cùng một chữ |
| 30 | 3.5 | Định nghĩa e(α,S), hậu tố S/α, D\|α và công thức sup qua dữ liệu chiếu (trường hợp riêng của Bổ đề 3.2); bảng đủ mọi nhánh của ví dụ để thấy 7 mẫu; giải thích ký hiệu `$` | Trước đó chỉ có nhánh ⟨A⟩ |
| 31 | 3.5 | Bổ đề khớp tham lam kết thúc sớm nhất, chứng minh quy nạp, và hệ quả α·⟨y⟩ ⊑ S ⇔ y nằm sau e(α,S). Đã kiểm thêm bằng code trên 20.000 cặp ngẫu nhiên | Đây là cơ sở toán của cả hai bản cài đặt; trước đó chỉ khẳng định bằng lời |
| 32 | 3.5 | Giải thích vì sao Bảng 3 của paper lưu nhiều vị trí ({2, 3, 6}) còn bài chỉ cần một | Nhiều vị trí chỉ cần cho mở rộng itemset |
| 33 | 3.5 | Bổ sung từ mục 4.1 của paper PrefixSpan: GSP do nhóm PrefixSpan tự cài; một cấu hình GSP nhỉnh hơn; dataset click web Gazelle và số đo bộ nhớ 40 MB / 2,7 MB | Trình bày kết quả của paper đầy đủ và trung thực hơn; vẫn chỉ là giả thuyết của bài |
| 34 | 3.7 | Ghi bản GSP của bài không sinh ứng viên cùng event; PrefixSpan chỉ cần một vị trí mỗi chuỗi | Nối với các thay đổi 28 và 32 |
| 35 | 4.5 | Công thức Pos(h,S), C(h), C(h,y); đẳng thức Σ_y C(h,y) = C(h); công thức ước lượng Markov bậc m | Trước đó chỉ định nghĩa bằng lời |
| 36 | 5.4 | Quy tắc chia n_train = ⌊0,8·\|D\|⌋ | Trước đó chưa nói cách làm tròn |
| 37 | 5.10 | Công thức Coverage, Hit@k, Hit@3 trên tập ca có gợi ý; T = Σ(L − 1) | Trước đó chỉ định nghĩa bằng lời |
| 38 | Đầu tài liệu, Tham khảo | Ghi lần sửa 2; ghi đã đọc toàn văn và các mục được dùng; ghi các biểu đồ chỉ đọc qua phần mô tả | Minh bạch phạm vi đã đọc |

Không thay đổi: sáu mảng nội dung, ví dụ A/B/C/D/X, 7 mẫu và các số liệu khảo sát; các quyết định ngày 01/11; chưa có kết quả thực nghiệm.

## 6. Lần sửa 3 (01/11/2026): điền kết quả thực nghiệm

Người dùng duyệt bản v2 sau lần sửa 2. Thực nghiệm chạy đúng thiết kế đã duyệt trên máy cục bộ (Intel i7-14650HX, 32 GB RAM, Windows 11, Python 3.10.20). Không thay đổi quy tắc, ngưỡng hay dải cấu hình nào. Code, dữ liệu và kết quả nằm trong thư mục `thuc-nghiem/`.

| # | Mục | Thay đổi | Nguồn số liệu |
|---|---|---|---|
| 39 | Đầu tài liệu | Ghi trạng thái đã có kết quả; thay nhãn [Chưa có] bằng nhãn [Kết quả] | — |
| 40 | 2.4, 2.7 | Số đếm thật của tập thực nghiệm: 70.968 chuỗi, 470.848 lượt ghé (33.468 từ quay lại), 4.179 trang, độ dài trung bình 6,63, dài nhất 435, train/test 56.774/14.194 | `data/prepare_info.json` |
| 41 | 3.7 | Kết quả bốn lớp kiểm tra tính đúng; lớp 4 đối chiếu SPMF 2.65 ở 4 cấu hình dữ liệu thật | `ket-qua/kiem_tra_tinh_dung.json` |
| 42 | 4.2 | Bỏ chữ “dự kiến”; trỏ tới đầu ra thật ở mục 4.9 | — |
| 43 | 4.9 (mới) | Mẫu thật trên train (1.063 mẫu ở r = 0,2%); phân tích cặp nhiệm vụ của trò chơi; mẫu thể hiện thứ tự; mẫu lặp do thao tác quay lại; ba ca minh họa từ test theo quy tắc cố định | `ket-qua/danh_gia/danh_gia.json`, `ket-qua/phan_tich_phu.json` |
| 44 | 5.3 | Kết quả chạy thử khả năng hoàn thành; giới hạn chốt 600 giây; không mức nào phải thay | `ket-qua/chay_thu/runs.jsonl` |
| 45 | 5.9 | Đổi tên mục; thêm R_M; bảng kết quả 8 cấu hình, 4 biểu đồ và phần đọc kết quả gắn với số ứng viên GSP, bộ nhớ dữ liệu và số phần tử chiếu | `ket-qua/do_chinh/` |
| 46 | 5.10.1 (mới) | Coverage, Hit@1, Hit@3 cho ba phương án trên toàn bộ ca và ca click tiến; Hit@3 trên tập ca có gợi ý; độ dài ngữ cảnh dùng; độ nhạy theo r | `ket-qua/danh_gia/danh_gia.json` |
| 47 | 6.6 | Thêm giới hạn: mọi cấu hình dưới 2 giây; chi phí đọc tệp chung làm R_T ở cấu hình nhẹ thấp hơn chênh lệch của riêng bước khai phá | `ket-qua/phan_tich_phu.json` |
| 48 | 6.7 | Viết lại thành “có thể khẳng định / không khẳng định” sau thực nghiệm | Các mục trên |
| 49 | Tham khảo | Danh mục code, dữ liệu, kết quả và notebook | — |
| 50 | 5.9.1 | Kết quả chạy lại toàn bộ notebook từ thư mục trống: cùng dữ liệu, cùng mẫu, cùng bộ nhớ và tỷ lệ đánh giá; R_T lệch tối đa 0,14 | `ket-qua/chay_lai_notebook/` |

Hai điểm phát sinh khi chạy, đã ghi trong nội dung:

- Nhiều mẫu có sup cao nhất là cặp (trang xuất phát, trang đích) do trò chơi giao lặp lại, chẳng hạn cả 852 đường đi chứa Asteroid → Viking đều đi từ Asteroid tới Viking. Điều này khớp với cảnh báo đã có ở mục 4.1 và 6.3. Phần diễn giải tách các mẫu này khỏi mẫu điều hướng giữa đường đi.
- Ở r = 1%, bản PrefixSpan của bài dùng nhiều bộ nhớ hơn GSP (R_M = 0,70) vì dựng dữ liệu chiếu cho mọi item phổ biến trong một lượt quét. Phần đọc kết quả ghi rõ đây là đặc điểm cài đặt.

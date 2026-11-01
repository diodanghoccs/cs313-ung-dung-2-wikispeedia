# Báo cáo bổ sung: dùng BMS-WebView-1/2 thay hoặc cạnh Wikispeedia được không?

Ngày chạy: 01/11/2026, cùng máy và cùng code với thực nghiệm chính (Intel i7-14650HX, 32 GB RAM, Windows 11, Python 3.10.20). Đây là **phần bổ sung ngoài thiết kế đã duyệt**, báo cáo riêng theo yêu cầu; bản nội dung chính không thay đổi.

Câu hỏi:

1. Bộ BMS-WebView-1/2 có dùng được cho bài toán dự đoán trang tiếp theo không?
2. Trên BMS, chênh lệch GSP – PrefixSpan có rõ hơn trên Wikispeedia không?

## 1. Nguồn dữ liệu

| Tệp | Nguồn | Dung lượng | SHA-256 |
|---|---|---:|---|
| `BMS1_spmf.txt` | <https://www.philippe-fournier-viger.com/spmf/publicdatasets/BMS1_spmf.txt> | 1.525.544 byte | `e797a4be0cd0fd8dc3cd55aad9c842092eacaa649478f693cc71e344552bd887` |
| `BMS2.txt` | <https://www.philippe-fournier-viger.com/spmf/publicdatasets/BMS2.txt> | 3.624.634 byte | `246e33be8961802f58d7e45dd59e58567c74d74275672d5d162c6fbcc60ce999` |

Hai tệp được tải về một thư mục riêng, tách khỏi thư mục code. Trang dataset của SPMF mô tả cả hai là dữ liệu click-stream thương mại điện tử dùng trong KDD Cup 2000 (Gazelle), và ghi rõ **không có tên item**.

## 2. Cấu trúc thật của dữ liệu

Script: `kiem_tra_cau_truc.py`; kết quả: `cau_truc.json`.

| Chỉ số | BMS1 | BMS2 | Wikispeedia (tập thực nghiệm) |
|---|---:|---:|---:|
| Số chuỗi | 59.601 | 77.512 | 70.968 |
| Số item khác nhau | 497 | 3.340 | 4.179 |
| Độ dài trung bình / dài nhất | 2,51 / 267 | 4,62 / 161 | 6,63 / 435 |
| Chuỗi chỉ có 1 item | 32.934 (55,3%) | 24.893 (32,1%) | 0 (đã lọc khi chuẩn bị) |
| Event có nhiều hơn 1 item | 0 | 0 | 0 |
| Chuỗi có ≥ 2 item | 26.667 | 52.619 | 70.968 |
| Trong đó mã item **tăng dần nghiêm ngặt** | **26.667 (100%)** | **52.619 (100%)** | 4.145 (5,8%) |
| Số chuỗi tăng dần kỳ vọng nếu thứ tự là ngẫu nhiên, \(\sum 1/L!\) | ≈ 6.495 | ≈ 8.547 | ≈ 3.625 |
| Chuỗi dài ≥ 6 mà tăng dần | 4.865 / 4.865 | 19.468 / 19.468 | 54 / 35.675 |
| Chuỗi có trang được ghé lại | 0 | 0 | 15.152 |

**Đọc kết quả.** Ở cả hai bộ BMS, **mọi** chuỗi có từ 2 item trở lên đều tăng dần nghiêm ngặt theo mã item, và không chuỗi nào ghé lại một trang. Nếu thứ tự là thứ tự click, xác suất một chuỗi dài L tình cờ tăng dần là 1/L!, chỉ 1/720 với L = 6. Vì vậy:

- thứ tự trong bản SPMF của BMS1/BMS2 là **thứ tự mã sản phẩm**, không phải thứ tự người dùng xem trang;
- mỗi “chuỗi” thực chất là một tập trang được sắp theo mã.

Wikispeedia thì khác: tỷ lệ chuỗi tăng dần gần mức ngẫu nhiên (4.145 so với kỳ vọng ≈ 3.625), và có 15.152 chuỗi ghé lại trang, đúng tính chất của thứ tự click thật.

Báo cáo chỉ khẳng định điều trên cho **bản định dạng SPMF** đã tải. Dữ liệu click thô gốc của KDD Cup 2000 là một nguồn khác; báo cáo này không kiểm tra nguồn đó.

## 3. Đo GSP và PrefixSpan theo cùng quy trình

Script: `so_sanh_ba_bo.py`; kết quả thô: `ket-qua/runs.jsonl`, tổng hợp: `ket-qua/tong_hop.json`.

**Quy trình:**

- Giữ nguyên cách đo của thực nghiệm chính: mỗi lượt một tiến trình Python mới; 1 lượt khởi động, 3 lượt thời gian (lấy trung vị) và 1 lượt bộ nhớ (`tracemalloc`); giới hạn 600 giây mỗi lượt.
- Mẫu dài 1–4; min_sup = ⌈r·|D|⌉.
- Mỗi bộ dữ liệu dùng toàn bộ số chuỗi của nó; Wikispeedia dùng đủ 70.968 chuỗi.
- Ngoài bốn mức r của bài, đo thêm mức 0,05%.
- Tổng 150 lượt, tất cả hoàn thành.
- Ở cả 15 cấu hình, tệp mẫu của GSP và PrefixSpan có cùng SHA-256.

**Đối chiếu SPMF 2.65** (PrefixSpan, độ dài 1–4; `ket-qua/doi_chieu_spmf.json`): ở cả bốn cấu hình kiểm tra, tập (mẫu, sup) của hai bản cài đặt trùng hoàn toàn với SPMF.

| Bộ | r | min_sup | Số mẫu |
|---|---:|---:|---:|
| BMS1 | 0,5% | 299 | 201 |
| BMS1 | 0,1% | 60 | 3.930 |
| BMS2 | 0,5% | 388 | 406 |
| BMS2 | 0,1% | 78 | 7.852 |

**Bảng kết quả.** Thời gian là trung vị 3 lượt; bộ nhớ là đỉnh cấp phát Python. \(R_T=T_{\mathrm{GSP}}/T_{\mathrm{PrefixSpan}}\) và \(R_M=M_{\mathrm{GSP}}/M_{\mathrm{PrefixSpan}}\).

| Bộ | r | min_sup | Số mẫu | Ứng viên GSP mức 2 | GSP (s) | PrefixSpan (s) | R_T | GSP (MB) | PrefixSpan (MB) | R_M |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BMS1 | 1% | 597 | 77 | 4.489 | 0,401 | 0,360 | 1,11 | 8,5 | 18,2 | 0,47 |
| BMS1 | 0,5% | 299 | 201 | 22.500 | 0,539 | 0,483 | 1,12 | 10,8 | 20,5 | 0,53 |
| BMS1 | 0,2% | 120 | 798 | 71.824 | 0,986 | 0,789 | 1,25 | 17,3 | 22,2 | 0,78 |
| BMS1 | 0,1% | 60 | 3.930 | 117.649 | 2,087 | 1,585 | 1,32 | 25,3 | 22,9 | 1,11 |
| BMS1 | 0,05% | 30 | 682.288 | 139.876 | 32,070 | 16,851 | 1,90 | 169,9 | 169,8 | 1,00 |
| BMS2 | 1% | 776 | 81 | 3.136 | 0,724 | 0,597 | 1,21 | 16,5 | 27,4 | 0,60 |
| BMS2 | 0,5% | 388 | 406 | 28.900 | 1,343 | 1,074 | 1,25 | 19,6 | 31,2 | 0,63 |
| BMS2 | 0,2% | 156 | 2.707 | 328.329 | 2,496 | 2,078 | 1,20 | 57,8 | 37,1 | 1,56 |
| BMS2 | 0,1% | 78 | 7.852 | 1.283.689 | 3,943 | 2,768 | 1,42 | 179,0 | 41,1 | 4,35 |
| BMS2 | 0,05% | 39 | 21.401 | 3.437.316 | 6,800 | 3,822 | 1,78 | 477,9 | 44,1 | 10,83 |
| Wikispeedia | 1% | 710 | 102 | 8.836 | 0,763 | 0,660 | 1,16 | 20,2 | 34,0 | 0,59 |
| Wikispeedia | 0,5% | 355 | 287 | 48.400 | 1,100 | 0,882 | 1,25 | 25,5 | 37,8 | 0,68 |
| Wikispeedia | 0,2% | 142 | 1.072 | 388.129 | 1,937 | 1,435 | 1,35 | 67,2 | 43,7 | 1,54 |
| Wikispeedia | 0,1% | 71 | 2.701 | 1.399.489 | 2,730 | 1,547 | 1,77 | 195,0 | 47,7 | 4,09 |
| Wikispeedia | 0,05% | 36 | 6.730 | 4.372.281 | 4,764 | 2,089 | 2,28 | 587,3 | 51,1 | 11,49 |

**Cấu hình Wikispeedia toàn bộ / 0,2% lặp lại cấu hình có trong thực nghiệm chính.**

| Lần đo | GSP (s) | PrefixSpan (s) | R_T |
|---|---:|---:|---:|
| Thực nghiệm chính | 1,726 | 1,246 | 1,38 |
| Lần đo này | 1,937 | 1,435 | 1,35 |

Lần đo này chậm hơn khoảng 12–15% ở cả hai thuật toán, do trạng thái máy khác giữa hai lần đo. Tỷ số gần như không đổi, và số mẫu cùng bộ nhớ trùng hoàn toàn với lần đo chính.

**Đọc kết quả:**

- **Xu hướng chung.** Cả ba bộ đều cho cùng xu hướng như thực nghiệm chính:
    - PrefixSpan nhanh hơn ở mọi cấu hình;
    - R_T tăng khi r giảm;
    - khi r còn ≤ 0,1%, bộ nhớ của GSP tăng vọt theo số ứng viên mức 2, có lúc gấp hơn 10 lần PrefixSpan;
    - ở support cao (1%, 0,5%), PrefixSpan lại tốn bộ nhớ hơn GSP.
- **BMS không cho chênh lệch lớn hơn Wikispeedia.** Ở r ≤ 0,2%, Wikispeedia có R_T lớn nhất trong ba bộ: 1,35 / 1,77 / 2,28, so với BMS2 là 1,20 / 1,42 / 1,78 và BMS1 là 1,25 / 1,32 / 1,90. Ở r = 1%, BMS2 nhỉnh hơn một chút (1,21 so với 1,16). Lý do là Wikispeedia có nhiều trang phổ biến hơn ở cùng ngưỡng: ở 0,05% là 2.091 trang, nên GSP phải sinh 4.372.281 ứng viên mức 2 nhưng chỉ 3.248 ứng viên đạt ngưỡng. BMS1 chỉ có 497 item nên số ứng viên mức 2 không vượt quá 497² = 247.009.
- **BMS1 ở 0,05% bùng nổ mẫu.** Số mẫu lên 682.288, trong đó 601.397 mẫu dài 4. Hệ quả:
    - Cả hai thuật toán chậm hẳn: GSP 32,1 giây, PrefixSpan 16,9 giây.
    - Bộ nhớ hai bên gần như bằng nhau (khoảng 170 MB), có lẽ vì phần lớn là chỗ lưu chính các mẫu kết quả.
    - Ứng viên GSP ở mức 4 phần lớn là mẫu thật: 601.397 trên 688.836, tức 87%, nên GSP ít phí công. Vì vậy R_T chỉ đạt 1,90, dù khối lượng việc lớn.

    Số mẫu dài nhiều như vậy phù hợp với nhận định ở mục 2: mỗi “chuỗi” là một tập trang đã sắp theo mã, nên mọi tập con của một nhóm trang hay đi cùng nhau đều thành “mẫu tuần tự”.

## 4. Kết luận

1. **Không nên dùng bản SPMF của BMS-WebView-1/2 cho bài toán dự đoán trang tiếp theo.** Thứ tự trong chuỗi là thứ tự mã sản phẩm, không phải thứ tự click (100% chuỗi tăng dần, 0 lần ghé lại). Thêm vào đó, 55,3% chuỗi của BMS1 và 32,1% của BMS2 chỉ có 1 item, còn mã trang ẩn danh nên không đọc được mẫu. Một mẫu ⟨a, b⟩ trên dữ liệu này chỉ có nghĩa là “a và b cùng xuất hiện, và mã a nhỏ hơn mã b”.
2. **Để so sánh GSP với PrefixSpan, BMS cũng không cho minh chứng mạnh hơn Wikispeedia.** Ở cùng quy trình và cùng ngưỡng, chênh lệch trên BMS bằng hoặc nhỏ hơn Wikispeedia, trừ mức r = 1%, nơi R_T của BMS2 cao hơn khoảng 0,06 (1,21 so với 1,16).
3. **Trong ba bộ đã đo thật, Wikispeedia vừa phù hợp nhất với ứng dụng, vừa cho chênh lệch rõ nhất ở support thấp.** Các bộ khác chưa đo (FIFA, E-Shop, Kosarak) chưa có minh chứng; không kết luận về chúng.
4. **Kết quả trên BMS củng cố kết luận chính của bài.** Xu hướng “PrefixSpan nhanh hơn, khoảng cách tăng khi support giảm, GSP tốn bộ nhớ theo số ứng viên” lặp lại trên hai bộ dữ liệu thật khác.

## 5. Giới hạn

- Chỉ kiểm tra bản định dạng SPMF của BMS; không kiểm tra dữ liệu click thô gốc của KDD Cup 2000.
- Mức 0,05% và việc đo Wikispeedia toàn bộ ở mọi mức r nằm ngoài thiết kế đã duyệt; chúng chỉ dùng trong báo cáo bổ sung này.
- Cùng các giới hạn của thực nghiệm chính: bản cài đặt Python, mẫu dài tối đa 4, một máy đo.

## 6. Tệp

| Tệp | Nội dung |
|---|---|
| `kiem_tra_cau_truc.py`, `cau_truc.json` | Kiểm tra cấu trúc ba bộ; chuyển BMS sang `data/BMS1_sequences.tsv`, `data/BMS2_sequences.tsv` |
| `so_sanh_ba_bo.py` | Đo (`do`), đối chiếu SPMF (`spmf`), tổng hợp (`tong_hop`) |
| `ket-qua/runs.jsonl`, `ket-qua/tong_hop.json` | 150 lượt đo và bảng tổng hợp |
| `ket-qua/doi_chieu_spmf.json` | Đối chiếu với SPMF |
| `ket-qua/patterns/` | Tệp mẫu đầu ra của từng cấu hình |

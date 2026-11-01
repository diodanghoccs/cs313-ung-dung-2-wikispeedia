# Ứng dụng 2: Dự đoán trang web truy cập tiếp theo trên Wikispeedia

Phần ứng dụng 2 (Next Website Page Prediction) trong bài thuyết trình Sequential Pattern Mining, môn Data Mining CS313.R11. Bài khai phá mẫu chuỗi trên đường đi của người chơi Wikispeedia bằng GSP và PrefixSpan, so sánh thời gian và bộ nhớ của hai thuật toán, rồi dùng mẫu để gợi ý trang tiếp theo và đánh giá trên tập test.

## Nội dung repo

| Đường dẫn | Nội dung |
|---|---|
| `Noi-dung-Ung-dung-2-Wikispeedia-v2.md`, `.html` | Nội dung đầy đủ, bản chốt ngày 01/11/2026. Bản `.html` mở bằng trình duyệt và hiển thị công thức. |
| `Nhat-ky-sua-v2.md`, `.html` | Các lần sửa và lý do |
| `thuc-nghiem/` | Code, dữ liệu đã chuẩn bị, kết quả đo và notebook Kaggle. Hướng dẫn chạy lại ở `thuc-nghiem/README.md`. |
| `thuc-nghiem/bo-sung-bms/` | Báo cáo bổ sung: kiểm tra BMS-WebView-1/2 và đo GSP – PrefixSpan trên ba bộ dữ liệu |
| `notion-import/tao_ban_notion.py` | Tạo bản Markdown để import nội dung vào Notion |

Các đường dẫn `thuc-nghiem/…` nhắc trong nội dung đều tính từ gốc repo này.

## Không có trong repo

- **Archive Wikispeedia gốc.** Notebook tự tải từ SNAP và kiểm tra SHA-256; `thuc-nghiem/data/` đã có sẵn dữ liệu đã chuẩn bị.
- **Dữ liệu và tệp sinh ra của phần bổ sung BMS** (khoảng 41 MB): `thuc-nghiem/bo-sung-bms/data/`, `ket-qua/patterns/`, `ket-qua/tmp/`. Repo vẫn giữ báo cáo, script, `cau_truc.json`, log 150 lượt đo (`ket-qua/runs.jsonl`), bảng tổng hợp và kết quả đối chiếu SPMF. Để tạo lại, tải `BMS1_spmf.txt` và `BMS2.txt` theo đường dẫn ở mục 1 của báo cáo BMS, đối chiếu SHA-256, rồi chạy trong `thuc-nghiem/bo-sung-bms/`:

  ```bash
  python -I kiem_tra_cau_truc.py <BMS1_spmf.txt> <BMS2.txt> ../data/sequences.tsv
  python -I so_sanh_ba_bo.py do
  python -I so_sanh_ba_bo.py tong_hop
  ```

  Lệnh `do` ghi nối vào `ket-qua/runs.jsonl`, nên đổi tên tệp cũ trước khi đo lại.
- **Tệp do `tao_ban_notion.py` sinh ra** (`.zip`, `hinh/`, bản `.md` cho Notion).

## Nguồn dữ liệu

Wikispeedia lấy từ Stanford SNAP: <https://snap.stanford.edu/data/wikispeedia.html>. Trang SNAP liệt kê hai công trình nguồn của dữ liệu (West & Leskovec, WWW 2012; West, Pineau & Precup, IJCAI 2009); danh mục tài liệu tham khảo trong nội dung có đủ thông tin trích dẫn.

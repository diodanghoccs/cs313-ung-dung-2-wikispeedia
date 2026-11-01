# Thực nghiệm Ứng dụng 2: GSP và PrefixSpan trên Wikispeedia

Thư mục này chứa code, dữ liệu đã chuẩn bị và kết quả thô của thực nghiệm trong `../Noi-dung-Ung-dung-2-Wikispeedia-v2.md`. Toàn bộ chạy ngày 01/11/2026 trên Intel i7-14650HX, 32 GB RAM, Windows 11, Python 3.10.20. Code chỉ dùng thư viện chuẩn; riêng `tong_hop.py` dùng matplotlib để vẽ biểu đồ.

## Tệp

| Tệp | Vai trò |
|---|---|
| `spm_wiki.py` | Đọc archive SNAP và khôi phục `<`; chuẩn bị dữ liệu; GSP; PrefixSpan; đếm vét cạn; đo một lượt; bộ gợi ý và đánh giá |
| `kiem_tra_tinh_dung.py` | Bốn lớp kiểm tra tính đúng (lớp 4 cần SPMF) |
| `chay_do.py` | Lịch đo: chạy thử (`thu`) hoặc đo chính (`chinh`), mỗi lượt một tiến trình mới |
| `tong_hop.py` | Bảng kết quả và 4 biểu đồ từ `ket-qua/do_chinh/runs.jsonl` |
| `danh_gia.py` | Đánh giá gợi ý trên tập test, ca minh họa, mẫu tiêu biểu |
| `phan_tich_phu.py` | Số liệu phụ dùng để diễn giải |
| `Ung-dung-2-Wikispeedia-GSP-PrefixSpan.ipynb` | Notebook chạy lại toàn bộ, dùng cho Kaggle |
| `data/` | `sequences.tsv` (70.968 chuỗi đã xáo trộn, seed 20261101), `articles.tsv`, `prepare_info.json` |
| `bo-sung-bms/` | Báo cáo bổ sung ngoài thiết kế: kiểm tra BMS-WebView-1/2 và đo GSP – PrefixSpan trên ba bộ (`BAO-CAO-BMS.md`) |
| `ket-qua/` | Kết quả: `kiem_tra_tinh_dung.json`, `chay_thu/`, `do_chinh/`, `danh_gia/`, `phan_tich_phu.json`, và `chay_lai_notebook/` (lần chạy lại toàn bộ notebook từ thư mục trống) |

## Chạy lại trên máy

Chạy từ thư mục này, theo thứ tự:

```bash
python -I spm_wiki.py prepare --archive <đường dẫn>/wikispeedia_paths-and-graph.tar.gz --outdir data
python -I kiem_tra_tinh_dung.py --spmf <đường dẫn>/SPMF.exe
python -I chay_do.py thu --timeout 1800
python -I chay_do.py chinh --timeout 600
python -I tong_hop.py
python -I danh_gia.py
python -I phan_tich_phu.py
```

Bỏ `--spmf` nếu không có SPMF; lớp 1–3 vẫn chạy. Archive gốc: <https://snap.stanford.edu/data/wikispeedia/wikispeedia_paths-and-graph.tar.gz>, SHA-256 `97697096f5d2dcb77aa69e3992305c6c561de89edb9fb10b5ad9feaf8ba534d5`.

## Chạy trên Kaggle

1. Tạo notebook mới bằng cách import `Ung-dung-2-Wikispeedia-GSP-PrefixSpan.ipynb`.
2. Bật *Internet* trong Settings để notebook tự tải archive từ SNAP, hoặc thêm một Kaggle Dataset chứa `wikispeedia_paths-and-graph.tar.gz`; notebook tự tìm tệp trong `/kaggle/input`.
3. Chọn *Run All*. Notebook ghi lại các tệp `.py`, chuẩn bị dữ liệu, chạy lớp kiểm tra 1–3, đo chính, tổng hợp và đánh giá.

Thời gian tuyệt đối trên Kaggle sẽ khác máy cục bộ. Điều phải lặp lại được là: tập mẫu (cùng SHA-256 ở từng cấu hình), các tỷ lệ đánh giá, và chiều của chênh lệch giữa hai thuật toán.

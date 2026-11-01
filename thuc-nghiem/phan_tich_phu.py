"""Các số liệu phụ dùng để diễn giải kết quả (mục 4.9, 5.9.2, 6.6 của bản nội dung).

    python -I phan_tich_phu.py
Ghi ket-qua/phan_tich_phu.json:
- bộ nhớ và thời gian chỉ để đọc dữ liệu (phần chung của hai thuật toán);
- với một số mẫu hai trang trên train: số đường đi bắt đầu ở trang đầu, kết thúc ở trang cuối, là lượt hoàn thành;
- mẫu lặp United States → United States: số đường đi có lượt về United States bằng thao tác quay lại;
- đường đi đầy đủ của ba ca minh họa.
"""
import json
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spm_wiki as sw  # noqa: E402

DATA = HERE / "data"
PAIRS = [("Asteroid", "Viking"), ("Brain", "Telephone"), ("Theatre", "Zebra"), ("Pyramid", "Bean"),
         ("North_America", "United_States"), ("Animal", "Mammal")]


def read_cost(n, repeats=5):
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        sw.read_sequences(DATA / "sequences.tsv", n)
        times.append(time.perf_counter() - t0)
    tracemalloc.start()
    sw.read_sequences(DATA / "sequences.tsv", n)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return {"n": n, "read_seconds_median": statistics.median(times), "read_peak_mb": peak / 2 ** 20}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    info = json.loads((DATA / "prepare_info.json").read_text(encoding="utf-8"))
    names = sw.read_names(DATA / "articles.tsv")
    ids = {n: i for i, n in enumerate(names)}
    out = {"read_cost": [read_cost(n) for n in (5000, 20000, info["kept"])]}
    train, backs, sids = sw.read_sequences(DATA / "sequences.tsv", info["n_train"], with_back=True)
    pairs = []
    for a, b in PAIRS:
        p = (ids[a], ids[b])
        sup = [i for i, s in enumerate(train) if sw.contains(p, s)]
        pairs.append({"pattern": f"{a} → {b}", "sup": len(sup),
                      "start_at_first": sum(train[i][0] == p[0] for i in sup),
                      "end_at_last": sum(train[i][-1] == p[1] for i in sup),
                      "finished_paths": sum(sids[i].startswith("F") for i in sup),
                      "reverse_sup": sum(sw.contains(p[::-1], s) for s in train)})
    out["pairs_on_train"] = pairs
    us = ids["United_States"]
    sup = [i for i, s in enumerate(train) if sw.contains((us, us), s)]
    out["us_us_on_train"] = {"sup": len(sup), "paths_with_back_visit_to_us": sum(
        any(x == us and bk == 1 for x, bk in zip(train[i], backs[i])) for i in sup)}
    demo = {}
    with open(DATA / "sequences.tsv", encoding="utf-8") as f:
        next(f)
        for line in f:
            sid, pages, back = line.rstrip("\n").split("\t")
            if sid in ("F45426", "F47642"):
                demo[sid] = {"path": [names[int(x)] for x in pages.split()], "back": back}
    out["demo_paths"] = demo
    (HERE / "ket-qua" / "phan_tich_phu.json").write_bytes(
        json.dumps(out, ensure_ascii=False, indent=2).encode("utf-8"))
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

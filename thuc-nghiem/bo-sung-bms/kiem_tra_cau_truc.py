"""Kiểm tra cấu trúc thật của BMS-WebView-1/2 (định dạng SPMF) và so với Wikispeedia.

    python -I kiem_tra_cau_truc.py <BMS1_spmf.txt> <BMS2.txt> <wikispeedia sequences.tsv>
Ghi cau_truc.json cạnh script và chuyển hai tệp BMS sang định dạng sequences.tsv (thư mục data/).

Câu hỏi chính: thứ tự item trong mỗi chuỗi có phải thứ tự click thật không?
Nếu chuỗi được tạo từ một tập hợp rồi sắp theo mã, gần như mọi chuỗi sẽ tăng dần nghiêm ngặt.
Với một chuỗi L item khác nhau xếp ngẫu nhiên, xác suất tình cờ tăng dần chỉ là 1/L!.
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read_spmf(path):
    seqs, multi_item_events = [], 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("@", "#", "%")):
                continue
            events, cur = [], []
            for tok in line.split():
                if tok == "-1":
                    events.append(cur)
                    cur = []
                elif tok == "-2":
                    break
                else:
                    cur.append(int(tok))
            multi_item_events += sum(len(e) > 1 for e in events)
            seqs.append(tuple(x for e in events for x in e))
    return seqs, multi_item_events


def read_tsv(path):
    with open(path, encoding="utf-8") as f:
        next(f)
        return [tuple(map(int, line.split("\t")[1].split())) for line in f]


def profile(seqs, multi_item_events=0):
    lens = [len(s) for s in seqs]
    multi = [s for s in seqs if len(s) >= 2]
    strictly_inc = sum(all(a < b for a, b in zip(s, s[1:])) for s in multi)
    nondecreasing = sum(all(a <= b for a, b in zip(s, s[1:])) for s in multi)
    has_repeat = sum(len(set(s)) < len(s) for s in seqs)
    # số chuỗi kỳ vọng tăng dần nếu thứ tự là ngẫu nhiên (chỉ tính chuỗi có item khác nhau)
    expected = sum(1 / math.factorial(len(s)) for s in multi if len(set(s)) == len(s))
    by_len = Counter(min(len(s), 6) for s in multi)
    inc_by_len = Counter(min(len(s), 6) for s in multi if all(a < b for a, b in zip(s, s[1:])))
    return {
        "sequences": len(seqs), "distinct_items": len({x for s in seqs for x in s}),
        "visits": sum(lens), "mean_len": sum(lens) / len(lens), "max_len": max(lens),
        "len1_sequences": sum(n == 1 for n in lens), "multi_item_events": multi_item_events,
        "seqs_len_ge2": len(multi), "strictly_increasing": strictly_inc,
        "strictly_increasing_pct": 100 * strictly_inc / len(multi),
        "nondecreasing": nondecreasing, "sequences_with_repeated_item": has_repeat,
        "expected_increasing_if_random_order": expected,
        "increasing_by_len": {f"{k}{'+' if k == 6 else ''}": f"{inc_by_len[k]}/{by_len[k]}" for k in sorted(by_len)},
    }


def to_tsv(seqs, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = ["sid\tpages\tback"] + [f"S{i}\t{' '.join(map(str, s))}\t{'0' * len(s)}" for i, s in enumerate(seqs)]
    out.write_bytes(("\n".join(rows) + "\n").encode("utf-8"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bms1, bms2, wiki = map(Path, sys.argv[1:4])
    report = {}
    for name, path in (("BMS1", bms1), ("BMS2", bms2)):
        seqs, multi = read_spmf(path)
        report[name] = profile(seqs, multi)
        to_tsv(seqs, HERE / "data" / f"{name}_sequences.tsv")
    report["Wikispeedia"] = profile(read_tsv(wiki))
    (HERE / "cau_truc.json").write_bytes(json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"))
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

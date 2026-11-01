"""Bốn lớp kiểm tra tính đúng của GSP và PrefixSpan (mục 3.7 của bản nội dung).

Chạy: python -I kiem_tra_tinh_dung.py [--spmf <SPMF.exe>]
Kết quả ghi vào ket-qua/kiem_tra_tinh_dung.json.
"""
import argparse
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spm_wiki as sw  # noqa: E402

A, B, C, D, X = 0, 1, 2, 3, 4


def both(db, min_sup, max_len=sw.MAX_LEN):
    return sw.gsp(db, min_sup, max_len)[0], sw.prefixspan(db, min_sup, max_len)[0]


def layer1():
    """Ví dụ năm chuỗi ở mục 3.3: đúng 7 mẫu và sup đã tính tay."""
    db = [(A, B, C), (A, X, B, C), (A, B, C), (A, B, D), (B, C)]
    min_sup = sw.min_sup_from_ratio("0.4", len(db))
    expected = {(A,): 4, (B,): 5, (C,): 4, (A, B): 4, (A, C): 3, (B, C): 4, (A, B, C): 3}
    g, p = both(db, min_sup)
    gsp_stats = sw.gsp(db, min_sup)[1]
    checks = {
        "min_sup == 2": min_sup == 2,
        "GSP == 7 mẫu tính tay": g == expected,
        "PrefixSpan == 7 mẫu tính tay": p == expected,
        "GSP sinh 9 ứng viên mức 2": gsp_stats["candidates"][2] == 9,
        "GSP sinh 1 ứng viên mức 3": gsp_stats["candidates"][3] == 1,
    }
    return checks


def layer2():
    """Trường hợp biên: trang lặp, khoảng cách, chuỗi trùng, làm tròn ngưỡng, giới hạn độ dài."""
    checks = {}
    g, p = both([(A, B, A)], 1)
    checks["<A,A> có trong A→B→A"] = g.get((A, A)) == 1 == p.get((A, A))
    g, p = both([(A, B)], 1)
    checks["<A,A> không có trong A→B"] = (A, A) not in g and (A, A) not in p
    g, p = both([(A, A, A, A, A)], 1)
    checks["chuỗi lặp chỉ đóng góp 1 lần"] = g == p == {(A,) * k: 1 for k in range(1, 5)}
    g, p = both([(A, X, B, C)], 1)
    checks["mẫu có khoảng cách <A,C>"] = g.get((A, C)) == 1 == p.get((A, C))
    g, p = both([(A, B, C), (A, B, C)], 2)
    checks["đường đi trùng nhau vẫn đếm 2"] = g.get((A, B, C)) == 2 == p.get((A, B, C))
    g, p = both([(A, B, C, D, A, B)], 1, max_len=2)
    checks["giới hạn độ dài 2"] = max(map(len, g)) == 2 == max(map(len, p)) and g == p
    g, p = both([(A, B, C, D, A, B)], 1, max_len=1)
    checks["giới hạn độ dài 1"] = g == p == {(A,): 1, (B,): 1, (C,): 1, (D,): 1}
    g, p = both([(A, B), (C, D)], 3)
    checks["ngưỡng quá cao cho tập rỗng"] = g == p == {}
    checks["ceil(0,07 × 100) = 7 (chuỗi)"] = sw.min_sup_from_ratio("0.07", 100) == 7
    checks["ceil(0,07 × 100) = 7 (số thực)"] = sw.min_sup_from_ratio(0.07, 100) == 7
    checks["ceil(0,002 × 20.000) = 40"] = sw.min_sup_from_ratio("0.002", 20000) == 40
    checks["ceil(0,002 × 56.774) = 114"] = sw.min_sup_from_ratio("0.002", 56774) == 114
    checks["ceil(0,001 × 5.000) = 5"] = sw.min_sup_from_ratio("0.001", 5000) == 5
    return checks


def layer3(trials=600, seed=sw.SEED):
    """So với cách đếm vét cạn trên nhiều cơ sở dữ liệu ngẫu nhiên nhỏ."""
    rng = random.Random(seed)
    failures = []
    total_patterns = 0
    for t in range(trials):
        alphabet = rng.randint(2, 7)
        db = [tuple(rng.randrange(alphabet) for _ in range(rng.randint(1, 10)))
              for _ in range(rng.randint(1, 30))]
        min_sup = rng.randint(1, 6)
        max_len = rng.randint(1, 4)
        ref = sw.brute_force(db, min_sup, max_len)
        g, p = both(db, min_sup, max_len)
        total_patterns += len(ref)
        if not (g == ref == p):
            failures.append({"trial": t, "db": db, "min_sup": min_sup, "max_len": max_len})
    return {f"{trials} CSDL ngẫu nhiên: GSP == PrefixSpan == vét cạn": not failures,
            "_total_reference_patterns": total_patterns, "_failures": failures[:3]}


def layer4(spmf_exe, data, configs=((5000, "0.01"), (5000, "0.005"), (5000, "0.002"), (20000, "0.002"))):
    """Đối chiếu với SPMF PrefixSpan trên tập con Wikispeedia thật (n chuỗi đầu theo thứ tự xáo trộn)."""
    checks, info = {}, {}
    with tempfile.TemporaryDirectory(dir=HERE / "ket-qua") as tmp:
        tmp = Path(tmp)
        for n, r in configs:
            db = sw.read_sequences(data, n)
            inp = tmp / f"spmf_input_{n}.txt"
            # SPMF: mỗi event kết thúc bằng -1, mỗi chuỗi bằng -2; cộng 1 để mã trang luôn dương
            inp.write_bytes("".join(" ".join(f"{x + 1} -1" for x in s) + " -2\n" for s in db).encode("utf-8"))
            out = tmp / f"spmf_{n}_{r}.txt"
            pct = f"{float(r) * 100:g}%"
            subprocess.run([spmf_exe, "run", "PrefixSpan", str(inp), str(out), pct, "1", str(sw.MAX_LEN)],
                           check=True, capture_output=True, timeout=900)
            spmf = {}
            for line in out.read_text(encoding="utf-8").splitlines():
                if line.startswith("@") or not line.strip():
                    continue
                left, sup = line.split("#SUP:")
                spmf[tuple(int(x) - 1 for x in left.split() if x != "-1")] = int(sup)
            min_sup = sw.min_sup_from_ratio(r, len(db))
            g, p = both(db, min_sup)
            info[f"{n}/{r}"] = {"n": len(db), "min_sup": min_sup, "spmf_patterns": len(spmf),
                                "gsp_patterns": len(g), "prefixspan_patterns": len(p)}
            checks[f"n={len(db)}, r={pct} (min_sup={min_sup}): GSP == PrefixSpan == SPMF"] = g == p == spmf
    return checks, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spmf", default=None)
    ap.add_argument("--data", default=str(HERE / "data" / "sequences.tsv"))
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    (HERE / "ket-qua").mkdir(exist_ok=True)
    report = {"layer1": layer1(), "layer2": layer2(), "layer3": layer3()}
    if args.spmf:
        report["layer4"], report["layer4_info"] = layer4(args.spmf, args.data)
    ok = True
    for name in ("layer1", "layer2", "layer3", "layer4"):
        for k, v in report.get(name, {}).items():
            if k.startswith("_"):
                continue
            ok &= bool(v)
            print(f"[{'ĐẠT' if v else 'LỖI'}] {name}: {k}")
    report["all_passed"] = ok
    (HERE / "ket-qua" / "kiem_tra_tinh_dung.json").write_bytes(
        json.dumps(report, ensure_ascii=False, indent=2, default=str).encode("utf-8"))
    print("TẤT CẢ ĐẠT" if ok else "CÓ LỖI")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

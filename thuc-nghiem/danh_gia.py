"""Đánh giá hữu ích trên tập test (mục 4.7 và 5.10 của bản nội dung).

Train = floor(0,8·|D|) đường đi đầu theo thứ tự đã xáo trộn, test = phần còn lại.
Mẫu khai phá trên train bằng cả hai thuật toán; chỉ dùng khi hai tập (mẫu, sup) trùng nhau.
    python -I danh_gia.py [--ratios 0.002 0.01 0.005 0.001] [--algos gsp prefixspan]
Kết quả: ket-qua/danh_gia/danh_gia.json và ca_minh_hoa.md.
"""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spm_wiki as sw  # noqa: E402

DATA = HERE / "data"


def ratio(a, b):
    return {"num": a, "den": b, "value": a / b if b else None}


def summarize(raw):
    out = {}
    for g, c in raw["groups"].items():
        T = c["T"]
        res = {"T": T}
        for name in ("baseline", "pattern", "pattern+fill"):
            res[name] = {"coverage": ratio(c[f"{name}.cov"], T), "hit1": ratio(c[f"{name}.hit1"], T),
                         "hit3": ratio(c[f"{name}.hit3"], T)}
        res["covered_subset"] = {"T_cov": c["cov.T"],
                                 "pattern_hit3": ratio(c["cov.pattern.hit3"], c["cov.T"]),
                                 "baseline_hit3": ratio(c["cov.baseline.hit3"], c["cov.T"])}
        out[g] = res
    out["context_len"] = raw["context_len"]
    return out


def demo_cases(rec, test, backs, sids, names):
    """Ca đầu tiên theo thứ tự test cho mỗi loại: gợi ý trúng, gợi ý trượt, không đủ bằng chứng."""
    found = {}
    for i, t, hist, ans, forward in sw.test_cases(test, backs):
        ctx, ranked = rec.explain(hist)
        kind = "khong_du_bang_chung" if not ranked else (
            "trung" if ans in [e["page"] for e in ranked] else "truot")
        if kind in found:
            continue
        tried = []
        for m in range(min(rec.max_context, len(hist)), 0, -1):
            h = tuple(hist[-m:])
            n_ok = sum(1 for y, chy in rec.c_hy[h].items()
                       if chy >= rec.min_transition and h + (y,) in rec.patterns)
            tried.append({"context": [names[p] for p in h], "c_h": rec.c_h.get(h, 0),
                          "qualified_candidates": n_ok if rec.c_h.get(h, 0) >= rec.min_context else 0})
        found[kind] = {
            "sid": sids[i], "t": t, "history": [names[p] for p in hist], "answer": names[ans],
            "answer_is_forward_click": forward, "context": [names[p] for p in ctx], "tried": tried,
            "suggestions": [dict(e, page=names[e["page"]]) for e in ranked],
        }
        if len(found) == 3:
            break
    return found


def example_patterns(patterns, names, top=10):
    """Mẫu tiêu biểu theo quy tắc cố định: sup cao nhất theo độ dài; cặp hai trang khác nhau kèm sup
    chiều ngược; mẫu quay về dạng x→y→x với x ≠ y; mẫu lặp một trang x→x."""
    def fmt(p):
        return " → ".join(names[x] for x in p)

    def ranked(cond):
        return sorted(((c, p) for p, c in patterns.items() if cond(p)), key=lambda t: (-t[0], t[1]))[:top]
    out = {}
    for k in (2, 3, 4):
        out[f"len{k}"] = [{"pattern": fmt(p), "sup": c} for c, p in ranked(lambda p, k=k: len(p) == k)]
    out["order"] = [{"pattern": fmt(p), "sup": c, "reverse_sup": patterns.get(p[::-1], 0)}
                    for c, p in ranked(lambda p: len(p) == 2 and p[0] != p[1])]
    out["return_xyx"] = [{"pattern": fmt(p), "sup": c}
                         for c, p in ranked(lambda p: len(p) == 3 and p[0] == p[2] != p[1])]
    out["repeat_xx"] = [{"pattern": fmt(p), "sup": c} for c, p in ranked(lambda p: len(p) == 2 and p[0] == p[1])]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratios", nargs="+", default=["0.002", "0.01", "0.005", "0.001"])
    ap.add_argument("--algos", nargs="+", default=["gsp", "prefixspan"])
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    outdir = HERE / "ket-qua" / "danh_gia"
    outdir.mkdir(parents=True, exist_ok=True)
    info = json.loads((DATA / "prepare_info.json").read_text(encoding="utf-8"))
    n_train = info["n_train"]
    names = sw.read_names(DATA / "articles.tsv")
    train = sw.read_sequences(DATA / "sequences.tsv", n_train)
    test, backs, sids = sw.read_sequences(DATA / "sequences.tsv", None, start=n_train, with_back=True)
    report = {"n_train": len(train), "n_test": len(test),
              "rules": {"max_context": sw.MAX_CONTEXT, "min_C_h": sw.MIN_CONTEXT_COUNT,
                        "min_C_hy": sw.MIN_TRANSITION_COUNT, "max_len": sw.MAX_LEN},
              "by_ratio": {}}
    for r in args.ratios:
        min_sup = sw.min_sup_from_ratio(r, len(train))
        mined, seconds = {}, {}
        for algo in args.algos:
            t0 = time.perf_counter()
            mined[algo] = sw.ALGORITHMS[algo](train, min_sup)[0]
            seconds[algo] = time.perf_counter() - t0
        first = mined[args.algos[0]]
        same = all(m == first for m in mined.values())
        if not same:
            raise SystemExit(f"r={r}: hai tập mẫu khác nhau, dừng đánh giá")
        rec = sw.Recommender(train, first)
        t0 = time.perf_counter()
        res = summarize(sw.evaluate(rec, test, backs))
        res.update({"min_sup": min_sup, "n_patterns": len(first),
                    "by_length": dict(Counter(len(p) for p in first)),
                    "algos_checked": args.algos, "outputs_identical": same,
                    "mining_seconds_untimed_context": seconds,
                    "eval_seconds": time.perf_counter() - t0,
                    "baseline_pages": [names[p] for p in rec.popular[:4]]})
        if r == args.ratios[0]:
            res["demo_cases"] = demo_cases(rec, test, backs, sids, names)
            res["example_patterns"] = example_patterns(first, names)
        report["by_ratio"][r] = res
        a = res["all"]
        print(f"r={r} min_sup={min_sup} patterns={len(first)} identical={same} | "
              f"T={a['T']} cov={a['pattern']['coverage']['value']:.4f} "
              f"hit3 pattern={a['pattern']['hit3']['value']:.4f} fill={a['pattern+fill']['hit3']['value']:.4f} "
              f"baseline={a['baseline']['hit3']['value']:.4f}", flush=True)
    (outdir / "danh_gia.json").write_bytes(json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()

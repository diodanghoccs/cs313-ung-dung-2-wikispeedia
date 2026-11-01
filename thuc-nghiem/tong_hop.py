"""Tổng hợp kết quả đo chính thành bảng và biểu đồ (mục 5.9 của bản nội dung).

    python -I tong_hop.py [--indir ket-qua/do_chinh]
Ghi: bang_ket_qua.md, tong_hop.json và các biểu đồ PNG trong cùng thư mục.
"""
import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
LABEL = {"gsp": "GSP", "prefixspan": "PrefixSpan"}
COLOR = {"gsp": "#c2410c", "prefixspan": "#1d4ed8"}


def load(indir):
    runs = [json.loads(line) for line in open(indir / "runs.jsonl", encoding="utf-8")]
    table = defaultdict(lambda: {"times": [], "status": []})
    for r in runs:
        key = (int(r["n"]), r["r"], r["algo"])
        row = table[key]
        row.setdefault("groups", set()).add(r["group"])
        if r["label"] == "warmup":
            row["warmup_status"] = r["status"]
        elif r["mode"] == "time":
            row["status"].append(r["status"])
            if r["status"] == "ok":
                row["times"].append(r["seconds"])
                row.update(min_sup=r["min_sup"], n_patterns=r["n_patterns"], sha=r["sha256"],
                           stats=r["stats"], by_length=r["by_length"])
        elif r["mode"] == "mem" and r["status"] == "ok":
            row["peak_mb"] = r["peak_bytes"] / 2 ** 20
            row["mem_seconds"] = r["seconds"]
    return table


def summarize(table):
    configs = sorted({(n, r) for n, r, _ in table}, key=lambda t: (t[0], -float(t[1])))
    rows = []
    for n, r in configs:
        g, p = table.get((n, r, "gsp")), table.get((n, r, "prefixspan"))
        entry = {"n": n, "r": r, "groups": sorted(set().union(*(x.get("groups", set()) for x in (g, p) if x)))}
        for name, x in (("gsp", g), ("prefixspan", p)):
            ok = x and x["times"] and all(s == "ok" for s in x["status"])
            entry[name] = {
                "status": "ok" if ok else (x.get("warmup_status") or "missing") if x else "missing",
                "times": x["times"] if x else [],
                "median": statistics.median(x["times"]) if ok else None,
                "min": min(x["times"]) if ok else None, "max": max(x["times"]) if ok else None,
                "peak_mb": x.get("peak_mb") if x else None,
                "n_patterns": x.get("n_patterns") if x else None,
                "min_sup": x.get("min_sup") if x else None,
                "sha": x.get("sha") if x else None,
                "stats": x.get("stats") if x else None,
                "by_length": x.get("by_length") if x else None,
            }
        both_ok = entry["gsp"]["status"] == entry["prefixspan"]["status"] == "ok"
        entry["outputs_identical"] = both_ok and entry["gsp"]["sha"] == entry["prefixspan"]["sha"]
        entry["R_T"] = entry["gsp"]["median"] / entry["prefixspan"]["median"] if both_ok else None
        entry["R_M"] = (entry["gsp"]["peak_mb"] / entry["prefixspan"]["peak_mb"]
                        if both_ok and entry["prefixspan"]["peak_mb"] else None)
        rows.append(entry)
    return rows


def vn(x, digits=0):
    """Định dạng số kiểu Việt Nam: dấu chấm hàng nghìn, dấu phẩy thập phân."""
    if x is None:
        return "—"
    s = f"{x:,.{digits}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def vn_ratio(r):
    return vn(float(r) * 100, 1 if float(r) * 1000 % 10 else 0) + "%"


def markdown(rows):
    head = ("| \\|D\\| | r | min_sup | Thuật toán | Thời gian 3 lượt (s) | Trung vị (s) | Đỉnh cấp phát Python (MB) "
            "| Số mẫu | Ứng viên GSP mức 2 / 3 / 4 | Đầu ra trùng | R_T | R_M |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
    lines = [head]
    for e in rows:
        for name in ("gsp", "prefixspan"):
            x = e[name]
            cand = "—"
            if name == "gsp" and x["stats"]:
                c = x["stats"]["candidates"]
                cand = " / ".join(vn(c.get(str(k), c.get(k, 0))) for k in (2, 3, 4))
            times = "; ".join(vn(t, 3) for t in x["times"]) if x["status"] == "ok" else x["status"]
            same = ("có" if e["outputs_identical"] else "KHÔNG") if name == "gsp" else ""
            rt = vn(e["R_T"], 2) if name == "gsp" else ""
            rm = vn(e["R_M"], 2) if name == "gsp" else ""
            lines.append(f"| {vn(e['n'])} | {vn_ratio(e['r'])} | {vn(x['min_sup'])} | {LABEL[name]} | {times} | "
                         f"{vn(x['median'], 3)} | {vn(x['peak_mb'], 1)} | {vn(x['n_patterns'])} | {cand} | "
                         f"{same} | {rt} | {rm} |")
    return "\n".join(lines) + "\n"


def plot(rows, outdir):
    by_r = [e for e in rows if "nguong" in e["groups"]]
    by_n = [e for e in rows if "quy_mo" in e["groups"] or (e["n"] == 20000 and e["r"] == "0.002")]
    by_r.sort(key=lambda e: -float(e["r"]))
    by_n.sort(key=lambda e: e["n"])
    specs = [
        (by_r, lambda e: vn_ratio(e["r"]), "median", "Thời gian trung vị (s)",
         "Thời gian theo ngưỡng r (|D| = 20.000, độ dài ≤ 4)", "thoi_gian_theo_nguong.png", "Ngưỡng r"),
        (by_n, lambda e: vn(e["n"]), "median", "Thời gian trung vị (s)",
         "Thời gian theo số chuỗi (r = 0,2%, độ dài ≤ 4)", "thoi_gian_theo_quy_mo.png", "Số chuỗi |D|"),
        (by_r, lambda e: vn_ratio(e["r"]), "peak_mb", "Đỉnh cấp phát Python (MB)",
         "Bộ nhớ theo ngưỡng r (|D| = 20.000, độ dài ≤ 4)", "bo_nho_theo_nguong.png", "Ngưỡng r"),
        (by_n, lambda e: vn(e["n"]), "peak_mb", "Đỉnh cấp phát Python (MB)",
         "Bộ nhớ theo số chuỗi (r = 0,2%, độ dài ≤ 4)", "bo_nho_theo_quy_mo.png", "Số chuỗi |D|"),
    ]
    for data, xl, key, ylabel, title, fname, xlabel in specs:
        fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
        # trục số chuỗi theo tỷ lệ thật; trục ngưỡng r là các mức rời rạc
        xs = [e["n"] for e in data] if data is by_n else list(range(len(data)))
        for name in ("gsp", "prefixspan"):
            ys = [e[name][key] for e in data]
            ax.plot(xs, ys, marker="o", color=COLOR[name], label=LABEL[name], linewidth=2)
            if key == "median":
                lo = [e[name]["min"] for e in data]
                hi = [e[name]["max"] for e in data]
                ax.fill_between(xs, lo, hi, color=COLOR[name], alpha=0.15, linewidth=0)
        ax.set_xticks(xs, [xl(e) for e in data])
        if data is by_n:
            plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=11)
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(outdir / fname)
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", default=str(HERE / "ket-qua" / "do_chinh"))
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    indir = Path(args.indir)
    rows = summarize(load(indir))
    md = markdown(rows)
    (indir / "bang_ket_qua.md").write_bytes(md.encode("utf-8"))
    (indir / "tong_hop.json").write_bytes(json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8"))
    plot(rows, indir)
    print(md)


if __name__ == "__main__":
    main()

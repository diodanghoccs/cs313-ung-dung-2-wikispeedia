"""So sánh GSP và PrefixSpan trên BMS1, BMS2 và Wikispeedia (toàn bộ) theo cùng quy trình đo của bài.

    python -I so_sanh_ba_bo.py do [--timeout 600]        # 1 khởi động + 3 lượt thời gian + 1 lượt bộ nhớ
    python -I so_sanh_ba_bo.py spmf --spmf <SPMF.exe> --bms1 <BMS1_spmf.txt> --bms2 <BMS2.txt>
    python -I so_sanh_ba_bo.py tong_hop
Kết quả trong ket-qua/ cạnh script. Đây là phần bổ sung, ngoài thiết kế đã duyệt của bài.
"""
import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPM = ROOT / "spm_wiki.py"
sys.path.insert(0, str(ROOT))
import spm_wiki as sw  # noqa: E402

DATASETS = {
    "BMS1": HERE / "data" / "BMS1_sequences.tsv",
    "BMS2": HERE / "data" / "BMS2_sequences.tsv",
    "Wikispeedia": ROOT / "data" / "sequences.tsv",
}
RATIOS = ("0.01", "0.005", "0.002", "0.001", "0.0005")
ALGOS = ("gsp", "prefixspan")
OUT = HERE / "ket-qua"


def n_of(path):
    return sum(1 for _ in open(path, encoding="utf-8")) - 1


def run_one(name, r, algo, mode, label, timeout):
    path = DATASETS[name]
    tag = f"{name}_r{r}_{algo}"
    out, js = OUT / "patterns" / f"{tag}.tsv", OUT / "tmp" / f"{tag}_{label}.json"
    cmd = [sys.executable, "-I", str(SPM), "bench", "--algo", algo, "--data", str(path), "--n", str(n_of(path)),
           "--r", r, "--mode", mode, "--out", str(out), "--json", str(js)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
        rec = json.loads(js.read_text(encoding="utf-8"))
        rec["status"] = "ok"
    except subprocess.TimeoutExpired:
        rec = {"algo": algo, "r": r, "mode": mode, "status": "timeout"}
    except subprocess.CalledProcessError as e:
        rec = {"algo": algo, "r": r, "mode": mode, "status": "error", "stderr": e.stderr.decode()[-1500:]}
    rec.update({"dataset": name, "label": label})
    with open(OUT / "runs.jsonl", "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec) + "\n")
    shown = f"{rec['seconds']:.3f}s" if rec["status"] == "ok" else rec["status"]
    peak = f" peak={rec['peak_bytes'] / 2**20:.1f}MB" if rec.get("peak_bytes") else ""
    print(f"{name:12s} r={r:7s} {algo:10s} {label:7s} {shown}{peak} patterns={rec.get('n_patterns', '-')}", flush=True)
    return rec


def do(timeout):
    (OUT / "patterns").mkdir(parents=True, exist_ok=True)
    (OUT / "tmp").mkdir(exist_ok=True)
    for name in DATASETS:
        for r in RATIOS:
            alive = {a: run_one(name, r, a, "time", "warmup", timeout)["status"] == "ok" for a in ALGOS}
            for rep in (1, 2, 3):
                for a in (ALGOS if rep % 2 else ALGOS[::-1]):
                    if alive[a]:
                        run_one(name, r, a, "time", f"time{rep}", timeout)
            for a in ALGOS:
                if alive[a]:
                    run_one(name, r, a, "mem", "mem", timeout)


def spmf(spmf_exe, bms1, bms2):
    """Đối chiếu tập (mẫu, sup) của hai bản cài đặt với SPMF PrefixSpan (độ dài 1–4)."""
    sources = {"BMS1": Path(bms1), "BMS2": Path(bms2)}
    report = {}
    with tempfile.TemporaryDirectory(dir=OUT) as tmp:
        for name, src in sources.items():
            db = sw.read_sequences(DATASETS[name])
            for r in ("0.005", "0.001"):
                out = Path(tmp) / f"{name}_{r}.txt"
                pct = f"{float(r) * 100:g}%"
                subprocess.run([spmf_exe, "run", "PrefixSpan", str(src), str(out), pct, "1", str(sw.MAX_LEN)],
                               check=True, capture_output=True, timeout=1800)
                ref = {}
                for line in out.read_text(encoding="utf-8").splitlines():
                    if line.startswith("@") or not line.strip():
                        continue
                    left, sup = line.split("#SUP:")
                    ref[tuple(int(x) for x in left.split() if x != "-1")] = int(sup)
                min_sup = sw.min_sup_from_ratio(r, len(db))
                g, p = sw.gsp(db, min_sup)[0], sw.prefixspan(db, min_sup)[0]
                report[f"{name} r={pct}"] = {"min_sup": min_sup, "spmf": len(ref), "gsp": len(g),
                                             "prefixspan": len(p), "identical": g == p == ref}
                print(name, pct, report[f"{name} r={pct}"], flush=True)
    (OUT / "doi_chieu_spmf.json").write_bytes(json.dumps(report, indent=2).encode("utf-8"))


def tong_hop():
    runs = [json.loads(line) for line in open(OUT / "runs.jsonl", encoding="utf-8")]
    rows = []
    for name in DATASETS:
        for r in RATIOS:
            e = {"dataset": name, "r": r}
            for a in ALGOS:
                sel = [x for x in runs if x["dataset"] == name and x["r"] == r and x["algo"] == a]
                times = [x["seconds"] for x in sel if x["label"].startswith("time") and x["status"] == "ok"]
                mem = [x for x in sel if x["mode"] == "mem" and x["status"] == "ok"]
                ok = [x for x in sel if x["status"] == "ok"]
                e[a] = {"median": statistics.median(times) if len(times) == 3 else None,
                        "times": times, "peak_mb": mem[0]["peak_bytes"] / 2 ** 20 if mem else None,
                        "status": "ok" if len(times) == 3 else (sel[0]["status"] if sel else "missing"),
                        "n_patterns": ok[0]["n_patterns"] if ok else None,
                        "min_sup": ok[0]["min_sup"] if ok else None, "n": ok[0]["n"] if ok else None,
                        "sha": ok[0]["sha256"] if ok else None,
                        "candidates": ok[0]["stats"].get("candidates") if ok and a == "gsp" else None}
            g, p = e["gsp"], e["prefixspan"]
            e["identical"] = g["sha"] is not None and g["sha"] == p["sha"]
            e["R_T"] = g["median"] / p["median"] if g["median"] and p["median"] else None
            e["R_M"] = g["peak_mb"] / p["peak_mb"] if g["peak_mb"] and p["peak_mb"] else None
            rows.append(e)
    (OUT / "tong_hop.json").write_bytes(json.dumps(rows, indent=2).encode("utf-8"))
    for e in rows:
        g, p = e["gsp"], e["prefixspan"]
        c = g["candidates"] or {}
        print(f"{e['dataset']:12s} r={e['r']:7s} n={g['n']} min_sup={g['min_sup']} patterns={g['n_patterns']} "
              f"C2={c.get('2')} GSP={g['median']} PS={p['median']} R_T={e['R_T']} "
              f"memG={g['peak_mb']} memP={p['peak_mb']} R_M={e['R_M']} same={e['identical']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["do", "spmf", "tong_hop"])
    ap.add_argument("--timeout", type=float, default=600)
    ap.add_argument("--spmf")
    ap.add_argument("--bms1")
    ap.add_argument("--bms2")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(exist_ok=True)
    if args.cmd == "do":
        do(args.timeout)
    elif args.cmd == "spmf":
        spmf(args.spmf, args.bms1, args.bms2)
    else:
        tong_hop()


if __name__ == "__main__":
    main()

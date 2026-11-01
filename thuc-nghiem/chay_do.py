"""Điều phối phép đo GSP vs PrefixSpan (mục 5.3–5.7 của bản nội dung).

Mỗi lượt là một tiến trình Python mới: python -I spm_wiki.py bench ...
    python -I chay_do.py thu      # chạy thử khả năng hoàn thành: 1 lượt thời gian mỗi cấu hình
    python -I chay_do.py chinh --timeout 600
                                  # đo chính: 1 khởi động + 3 lượt thời gian + 1 lượt bộ nhớ
Kết quả: ket-qua/<tên>/runs.jsonl, tệp mẫu đầu ra và machine.json.
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPM = HERE / "spm_wiki.py"
DATA = HERE / "data" / "sequences.tsv"
ALGOS = ("gsp", "prefixspan")

# (nhóm thí nghiệm, số chuỗi, r); cấu hình 20.000 / 0,2% dùng chung cho hai nhóm
FULL_N = None  # None = toàn bộ tập hợp lệ


def configs(full_n):
    out = [("nguong", 20000, r) for r in ("0.01", "0.005", "0.002", "0.001")]
    out += [("quy_mo", n, "0.002") for n in (5000, 10000, 40000, full_n)]
    return out


def machine_info():
    info = {"python": sys.version, "platform": platform.platform(), "cpu_count": os.cpu_count()}
    try:
        if sys.platform == "win32":
            info["cpu"] = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
                capture_output=True, text=True, timeout=60).stdout.strip()
        else:
            info["cpu"] = next(line.split(":", 1)[1].strip() for line in open("/proc/cpuinfo")
                               if line.startswith("model name"))
    except Exception as e:  # thông tin phụ, không chặn phép đo
        info["cpu"] = f"unknown ({e})"
    try:
        import psutil
        info["ram_bytes"] = psutil.virtual_memory().total
    except Exception:
        info["ram_bytes"] = None
    return info


def run_one(outdir, group, n, r, algo, mode, label, timeout):
    tag = f"n{n}_r{r}_{algo}"
    out = outdir / "patterns" / f"{tag}.tsv"
    js = outdir / "tmp" / f"{tag}_{label}.json"
    cmd = [sys.executable, "-I", str(SPM), "bench", "--algo", algo, "--data", str(DATA), "--n", str(n),
           "--r", r, "--mode", mode, "--out", str(out), "--json", str(js)]
    t0 = time.perf_counter()
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
        rec = json.loads(js.read_text(encoding="utf-8"))
        rec["status"] = "ok"
    except subprocess.TimeoutExpired:
        rec = {"algo": algo, "n": n, "r": r, "mode": mode, "status": "timeout", "timeout_s": timeout}
    except subprocess.CalledProcessError as e:
        rec = {"algo": algo, "n": n, "r": r, "mode": mode, "status": "error",
               "stderr": e.stderr.decode("utf-8", "replace")[-2000:]}
    rec.update({"group": group, "label": label, "wall_process_s": time.perf_counter() - t0})
    with open(outdir / "runs.jsonl", "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec) + "\n")
    shown = f"{rec.get('seconds', 0):.2f}s" if rec["status"] == "ok" else rec["status"]
    peak = f" peak={rec['peak_bytes'] / 2**20:.1f}MB" if rec.get("peak_bytes") else ""
    print(f"{group:7s} n={n:6d} r={r:6s} {algo:10s} {label:8s} {shown}{peak} "
          f"patterns={rec.get('n_patterns', '-')}", flush=True)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["thu", "chinh"])
    ap.add_argument("--timeout", type=float, default=1800)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    full_n = sum(1 for _ in open(DATA, encoding="utf-8")) - 1
    outdir = Path(args.outdir or HERE / "ket-qua" / ("chay_thu" if args.mode == "thu" else "do_chinh"))
    (outdir / "patterns").mkdir(parents=True, exist_ok=True)
    (outdir / "tmp").mkdir(exist_ok=True)
    meta = {"machine": machine_info(), "timeout_s": args.timeout, "mode": args.mode, "full_n": full_n,
            "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    (outdir / "machine.json").write_bytes(json.dumps(meta, indent=2).encode("utf-8"))
    for group, n, r in configs(full_n):
        if args.mode == "thu":
            for algo in ALGOS:
                run_one(outdir, group, n, r, algo, "time", "thu", args.timeout)
            continue
        alive = {}
        for algo in ALGOS:  # lượt khởi động, không tính
            alive[algo] = run_one(outdir, group, n, r, algo, "time", "warmup", args.timeout)["status"] == "ok"
        for rep in (1, 2, 3):  # lượt lẻ GSP trước, lượt chẵn PrefixSpan trước
            order = ALGOS if rep % 2 == 1 else ALGOS[::-1]
            for algo in order:
                if alive[algo]:
                    run_one(outdir, group, n, r, algo, "time", f"time{rep}", args.timeout)
        for algo in ALGOS:
            if alive[algo]:
                run_one(outdir, group, n, r, algo, "mem", "mem", args.timeout)
    meta["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    (outdir / "machine.json").write_bytes(json.dumps(meta, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()

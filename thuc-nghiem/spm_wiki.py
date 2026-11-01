"""GSP và PrefixSpan tự cài đặt cho Ứng dụng 2: dự đoán trang tiếp theo trên Wikispeedia.

Mỗi event là đúng một trang, nên một chuỗi là tuple mã trang và mẫu cũng là tuple mã trang.
Chỉ có mở rộng chuỗi (S-extension); không có mẫu dạng <(a b)>.

Dùng như thư viện (import) hoặc dòng lệnh:
    python -I spm_wiki.py prepare --archive <tar.gz> --outdir <thư mục>
    python -I spm_wiki.py bench --algo gsp|prefixspan --data <sequences.tsv> --n N --r 0.002
                                --maxlen 4 --mode time|mem --out <patterns.tsv> --json <run.json>
Chỉ dùng thư viện chuẩn của Python.
"""
import argparse
import hashlib
import json
import math
import random
import sys
import tarfile
import time
import tracemalloc
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from urllib.parse import unquote

SEED = 20261101
MAX_LEN = 4


# ---------------------------------------------------------------- dữ liệu

def read_wikispeedia(archive_path):
    """Đọc archive SNAP, khôi phục thao tác quay lại '<' bằng ngăn xếp.

    Trả về (names, records, stats). records là list (sid, seq, back): seq là tuple mã trang theo
    articles.tsv, back[i] = 1 nếu lượt ghé thứ i đến từ thao tác quay lại.
    """
    with tarfile.open(archive_path, "r:gz") as tar:
        members = {m.name.rsplit("/", 1)[-1]: m for m in tar.getmembers() if m.isfile()}

        def lines(filename):
            for raw in tar.extractfile(members[filename]):
                text = raw.decode("utf-8").rstrip("\r\n")
                if text and not text.startswith("#"):
                    yield text

        articles = list(lines("articles.tsv"))
        ids = {name: i for i, name in enumerate(articles)}
        names = [unquote(name) for name in articles]
        records, stats = [], Counter()
        for kind, n_fields in (("finished", 5), ("unfinished", 6)):
            for row, line in enumerate(lines(f"paths_{kind}.tsv")):
                fields = line.split("\t")
                assert len(fields) == n_fields, fields
                stats[f"raw_{kind}"] += 1
                stack, seq, back, ok = [], [], [], True
                for token in fields[3].split(";"):
                    if token == "<":
                        if len(stack) < 2:
                            ok = False
                            break
                        stack.pop()
                        seq.append(stack[-1])
                        back.append(1)
                    elif token in ids:
                        stack.append(ids[token])
                        seq.append(ids[token])
                        back.append(0)
                    else:
                        ok = False
                        break
                if not ok:
                    stats["unresolvable"] += 1
                    continue
                records.append((f"{kind[0].upper()}{row}", tuple(seq), tuple(back)))
    return names, records, stats


def prepare(archive_path, outdir, seed=SEED):
    """Giữ chuỗi có ít nhất 2 lượt, xáo trộn một lần bằng seed cố định, ghi ra outdir."""
    names, records, stats = read_wikispeedia(archive_path)
    kept = [r for r in records if len(r[1]) >= 2]
    random.Random(seed).shuffle(kept)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rows = ["sid\tpages\tback"]
    rows += [f"{sid}\t{' '.join(map(str, seq))}\t{''.join(map(str, back))}" for sid, seq, back in kept]
    (outdir / "sequences.tsv").write_bytes(("\n".join(rows) + "\n").encode("utf-8"))
    (outdir / "articles.tsv").write_bytes(
        ("id\tname\n" + "".join(f"{i}\t{n}\n" for i, n in enumerate(names))).encode("utf-8"))
    lengths = [len(r[1]) for r in kept]
    info = {
        "seed": seed,
        "raw_paths": len(records) + stats["unresolvable"],
        "raw_finished": stats["raw_finished"],
        "raw_unfinished": stats["raw_unfinished"],
        "unresolvable": stats["unresolvable"],
        "dropped_len1": len(records) - len(kept),
        "kept": len(kept),
        "visits": sum(lengths),
        "back_visits": sum(sum(r[2]) for r in kept),
        "distinct_pages": len({p for r in kept for p in r[1]}),
        "mean_len": sum(lengths) / len(lengths),
        "max_len": max(lengths),
        "n_train": math.floor(Fraction(4, 5) * len(kept)),
    }
    info["n_test"] = info["kept"] - info["n_train"]
    (outdir / "prepare_info.json").write_bytes(json.dumps(info, indent=2).encode("utf-8"))
    return info


def read_sequences(path, n=None, start=0, with_back=False):
    """Đọc n chuỗi kể từ dòng start (theo thứ tự đã xáo trộn) của sequences.tsv."""
    seqs, backs, sids = [], [], []
    with open(path, encoding="utf-8") as f:
        next(f)
        for i, line in enumerate(f):
            if i < start:
                continue
            if n is not None and len(seqs) >= n:
                break
            sid, pages, back = line.rstrip("\n").split("\t")
            seqs.append(tuple(map(int, pages.split())))
            if with_back:
                backs.append(tuple(map(int, back)))
                sids.append(sid)
    return (seqs, backs, sids) if with_back else seqs


def read_names(path):
    with open(path, encoding="utf-8") as f:
        next(f)
        return [line.rstrip("\n").split("\t", 1)[1] for line in f]


# ---------------------------------------------------------------- ngưỡng

def min_sup_from_ratio(r, n_sequences):
    """min_sup = ceil(r * |D|) tính bằng phân số chính xác. r nhận chuỗi '0.002' hoặc số thực."""
    return math.ceil(Fraction(str(r)) * n_sequences)


def contains(pattern, seq):
    """pattern ⊑ seq theo khớp tham lam từ trái sang."""
    it = iter(seq)
    return all(any(x == y for y in it) for x in pattern)


# ---------------------------------------------------------------- GSP

def gsp(db, min_sup, max_len=MAX_LEN):
    """GSP (Srikant & Agrawal 1996) cho event một item, không ràng buộc gap/window.

    Mỗi mức k: sinh C_k bằng nối + cắt tỉa, đặt C_k vào cây tiền tố, quét toàn bộ db một lần để đếm.
    Trả về (patterns, stats) với patterns: dict tuple -> sup.
    """
    stats = {"candidates": {}, "frequent": {}}
    item_count = Counter()
    for s in db:
        item_count.update(set(s))
    level = {(x,): c for x, c in item_count.items() if c >= min_sup}
    stats["candidates"][1] = len(item_count)
    stats["frequent"][1] = len(level)
    patterns = dict(level)
    k = 2
    while level and k <= max_len:
        candidates = _gsp_generate(sorted(level), k)
        stats["candidates"][k] = len(candidates)
        if not candidates:
            break
        counts = _gsp_count(db, candidates, k)
        level = {c: n for c, n in zip(candidates, counts) if n >= min_sup}
        stats["frequent"][k] = len(level)
        patterns.update(level)
        del candidates, counts
        k += 1
    return patterns, stats


def _gsp_generate(prev, k):
    """Pha nối + pha cắt tỉa. prev là list mẫu độ dài k-1 đã sắp xếp."""
    if k == 2:
        items = [p[0] for p in prev]
        return [(a, b) for a in items for b in items]
    by_prefix = defaultdict(list)
    for s in prev:
        by_prefix[s[:-1]].append(s[-1])
    prev_set = set(prev)
    out = []
    for s1 in prev:
        for y in by_prefix.get(s1[1:], ()):
            c = s1 + (y,)
            # bỏ vị trí 0 cho s2 và vị trí k-1 cho s1, đều thuộc prev; chỉ cần kiểm tra vị trí giữa
            if all(c[:i] + c[i + 1:] in prev_set for i in range(1, k - 1)):
                out.append(c)
    return out


def _gsp_count(db, candidates, k):
    """Đếm support bằng cây tiền tố (thay hash tree của paper) và khớp sớm nhất."""
    trie = {}
    for idx, c in enumerate(candidates):
        node = trie
        for x in c[:-1]:
            node = node.setdefault(x, {})
        node[c[-1]] = idx
    counts = [0] * len(candidates)
    for s in db:
        _gsp_visit(trie, s, 0, k, counts)
    return counts


def _gsp_visit(node, s, start, depth_left, counts):
    seen = set()
    for j in range(start, len(s)):
        x = s[j]
        if x in seen:
            continue
        seen.add(x)
        child = node.get(x)
        if child is None:
            continue
        if depth_left == 1:
            counts[child] += 1
        else:
            _gsp_visit(child, s, j + 1, depth_left - 1, counts)


# ---------------------------------------------------------------- PrefixSpan

def prefixspan(db, min_sup, max_len=MAX_LEN):
    """PrefixSpan (Pei và cộng sự 2004) với pseudo-projection (mã chuỗi, vị trí bắt đầu hậu tố).

    Mỗi chuỗi trong dữ liệu chiếu giữ một vị trí: ngay sau lần khớp sớm nhất của tiền tố.
    Trả về (patterns, stats).
    """
    stats = {"projected_dbs": 0, "projected_entries": 0}
    patterns = {}
    root = [(sid, 0) for sid in range(len(db))]
    _ps_grow((), root, db, min_sup, max_len, patterns, stats)
    return patterns, stats


def _ps_grow(prefix, projected, db, min_sup, max_len, patterns, stats):
    count = Counter()
    for sid, start in projected:
        s = db[sid]
        if start < len(s):
            count.update(set(s[start:]))
    frequent = [x for x, c in count.items() if c >= min_sup]
    if not frequent:
        return
    for x in frequent:
        patterns[prefix + (x,)] = count[x]
    if len(prefix) + 1 >= max_len:
        return
    wanted = set(frequent)
    children = defaultdict(list)
    for sid, start in projected:
        s = db[sid]
        seen = set()
        for j in range(start, len(s)):
            x = s[j]
            if x in wanted and x not in seen:
                seen.add(x)
                children[x].append((sid, j + 1))
    del count, wanted
    stats["projected_dbs"] += len(children)
    stats["projected_entries"] += sum(map(len, children.values()))
    for x in frequent:
        _ps_grow(prefix + (x,), children.pop(x), db, min_sup, max_len, patterns, stats)


ALGORITHMS = {"gsp": gsp, "prefixspan": prefixspan}


# ---------------------------------------------------------------- kiểm tra

def brute_force(db, min_sup, max_len=MAX_LEN):
    """Liệt kê mọi chuỗi con khác nhau của từng chuỗi; chỉ dùng cho dữ liệu nhỏ."""
    count = Counter()
    for s in db:
        subs = set()
        for k in range(1, min(max_len, len(s)) + 1):
            for idx in combinations(range(len(s)), k):
                subs.add(tuple(s[i] for i in idx))
        count.update(subs)
    return {p: c for p, c in count.items() if c >= min_sup}


def pattern_lines(patterns):
    return [" ".join(map(str, p)) + "\t" + str(c) for p, c in sorted(patterns.items(), key=lambda t: (len(t[0]), t[0]))]


def write_patterns(path, patterns):
    data = ("\n".join(pattern_lines(patterns)) + "\n").encode("utf-8")
    Path(path).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def read_patterns(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                p, c = line.rstrip("\n").split("\t")
                out[tuple(map(int, p.split()))] = int(c)
    return out


# ---------------------------------------------------------------- đo một lượt

def bench_once(algo, data, n, r, max_len, mode, out):
    """Một lượt đo trong tiến trình hiện tại: đọc -> khai phá -> ghi. Bộ đếm giờ bao ngoài thuật toán."""
    if mode == "mem":
        tracemalloc.start()
    t0 = time.perf_counter()
    db = read_sequences(data, n)
    min_sup = min_sup_from_ratio(r, len(db))
    patterns, stats = ALGORITHMS[algo](db, min_sup, max_len)
    digest = write_patterns(out, patterns)
    seconds = time.perf_counter() - t0
    peak = None
    if mode == "mem":
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
    by_len = Counter(len(p) for p in patterns)
    return {
        "algo": algo, "n": len(db), "r": str(r), "min_sup": min_sup, "max_len": max_len, "mode": mode,
        "seconds": seconds, "peak_bytes": peak, "n_patterns": len(patterns),
        "by_length": {str(k): by_len[k] for k in sorted(by_len)}, "sha256": digest, "stats": stats,
    }


# ---------------------------------------------------------------- gợi ý và đánh giá

MAX_CONTEXT = 3
MIN_CONTEXT_COUNT = 5     # C(h) >= 5
MIN_TRANSITION_COUNT = 2  # C(h,y) >= 2


class Recommender:
    """Quy tắc mục 4.7: ngữ cảnh 3 -> 2 -> 1, lọc bằng mẫu phổ biến, xếp theo C(h,y)/C(h)."""

    def __init__(self, train, patterns, max_context=MAX_CONTEXT,
                 min_context=MIN_CONTEXT_COUNT, min_transition=MIN_TRANSITION_COUNT):
        self.patterns = patterns
        self.max_context = max_context
        self.min_context = min_context
        self.min_transition = min_transition
        self.c_h = Counter()
        self.c_hy = defaultdict(Counter)
        visits = Counter()
        for s in train:
            visits.update(s)
            for m in range(1, max_context + 1):
                for i in range(len(s) - m):
                    h = s[i:i + m]
                    self.c_h[h] += 1
                    self.c_hy[h][s[i + m]] += 1
        self.popular = [p for p, _ in sorted(visits.items(), key=lambda t: (-t[1], t[0]))[:max_context + 10]]

    def explain(self, history):
        """Trả về (context, ranked) với ranked là list dict bằng chứng; ([], []) nếu thiếu bằng chứng."""
        for m in range(min(self.max_context, len(history)), 0, -1):
            h = tuple(history[-m:])
            ch = self.c_h.get(h, 0)
            if ch < self.min_context:
                continue
            ranked = []
            for y, chy in self.c_hy[h].items():
                sup = self.patterns.get(h + (y,))
                if chy >= self.min_transition and sup is not None:
                    ranked.append({"page": y, "c_h": ch, "c_hy": chy, "score": chy / ch, "sup": sup})
            if ranked:
                ranked.sort(key=lambda e: (-e["score"], -e["c_hy"], -e["sup"], e["page"]))
                return h, ranked[:3]
        return (), []

    def pattern_top(self, history, k=3):
        return [e["page"] for e in self.explain(history)[1][:k]]

    def baseline_top(self, history, k=3):
        return [p for p in self.popular if p != history[-1]][:k]

    def filled_top(self, history, k=3):
        out = self.pattern_top(history, k)
        for p in self.baseline_top(history, k + len(out)):
            if len(out) >= k:
                break
            if p not in out:
                out.append(p)
        return out


def test_cases(test_seqs, test_backs):
    """Mọi vị trí t = 1..L-1 của mọi đường đi test: (chỉ số đường đi, t, lịch sử, đáp án, là click tiến)."""
    for i, (s, b) in enumerate(zip(test_seqs, test_backs)):
        for t in range(1, len(s)):
            yield i, t, s[:t], s[t], b[t] == 0


def evaluate(rec, test_seqs, test_backs):
    """Coverage, Hit@1, Hit@3 cho ba phương án; tách toàn bộ ca và ca click tiến."""
    variants = {"baseline": rec.baseline_top, "pattern": rec.pattern_top, "pattern+fill": rec.filled_top}
    groups = {"all": Counter(), "forward": Counter()}
    context_len = Counter()
    for _, _, hist, ans, forward in test_cases(test_seqs, test_backs):
        ctx, ranked = rec.explain(hist)
        context_len[len(ctx)] += 1
        tops = {"pattern": [e["page"] for e in ranked]}
        tops["baseline"] = rec.baseline_top(hist)
        tops["pattern+fill"] = rec.filled_top(hist)
        for g in (["all", "forward"] if forward else ["all"]):
            c = groups[g]
            c["T"] += 1
            covered = bool(tops["pattern"])
            for name in variants:
                top = tops[name]
                c[f"{name}.cov"] += bool(top)
                c[f"{name}.hit1"] += bool(top) and top[0] == ans
                c[f"{name}.hit3"] += ans in top
            if covered:
                c["cov.T"] += 1
                c["cov.pattern.hit3"] += ans in tops["pattern"]
                c["cov.baseline.hit3"] += ans in tops["baseline"]
    return {"groups": {g: dict(c) for g, c in groups.items()}, "context_len": dict(context_len)}


# ---------------------------------------------------------------- dòng lệnh

def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--archive", required=True)
    p.add_argument("--outdir", required=True)
    b = sub.add_parser("bench")
    b.add_argument("--algo", choices=sorted(ALGORITHMS), required=True)
    b.add_argument("--data", required=True)
    b.add_argument("--n", type=int, required=True)
    b.add_argument("--r", required=True)
    b.add_argument("--maxlen", type=int, default=MAX_LEN)
    b.add_argument("--mode", choices=["time", "mem"], default="time")
    b.add_argument("--out", required=True)
    b.add_argument("--json", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "prepare":
        print(json.dumps(prepare(args.archive, args.outdir), indent=2))
    else:
        res = bench_once(args.algo, args.data, args.n, args.r, args.maxlen, args.mode, args.out)
        Path(args.json).write_bytes(json.dumps(res).encode("utf-8"))
        print(json.dumps({k: res[k] for k in ("algo", "n", "min_sup", "mode", "seconds", "peak_bytes", "n_patterns")}))


if __name__ == "__main__":
    sys.exit(main())

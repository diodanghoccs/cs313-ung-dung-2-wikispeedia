"""Tạo bản Markdown để import vào Notion từ bản nội dung v2 (không sửa nội dung, chỉ đổi định dạng).

    python -I tao_ban_notion.py
Đầu ra cạnh script: Ung-dung-2-Wikispeedia.md, hinh/*.png, Ung-dung-2-Wikispeedia-Notion.zip,
và gói thử nhỏ thu-import.zip để kiểm tra cách Notion nhận công thức và hình trước khi import bản đầy đủ.

Các phép đổi:
- công thức \( … \) thành $…$, khối \[ … \] thành khối $$ (mỗi dấu $$ một dòng riêng);
- dấu < và > trong công thức thành \lt và \gt, để không bị hiểu nhầm là thẻ HTML;
- liên kết tương đối tới tệp trên máy (nhật ký sửa, thư mục thực nghiệm, gói bàn giao) chỉ giữ chữ;
- 4 biểu đồ trỏ tới hinh/;
- "Hit@" ngoài công thức viết thành "Hit\\@", vì Notion tự biến "Hit@3" thành liên kết email
  (đã thử ngày 01/11/2026: bản thoát ký tự hiện đúng "Hit@3" và không thành liên kết).

    python -I tao_ban_notion.py --bo-ghi-chu   # bỏ khối ghi chú phiên bản ở đầu tài liệu
"""
import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "Noi-dung-Ung-dung-2-Wikispeedia-v2.md"
CHARTS = HERE.parent / "thuc-nghiem" / "ket-qua" / "do_chinh"
OUT_MD = HERE / "Ung-dung-2-Wikispeedia.md"
OUT_IMG = HERE / "hinh"
OUT_ZIP = HERE / "Ung-dung-2-Wikispeedia-Notion.zip"
TEST_ZIP = HERE / "thu-import.zip"

INLINE = re.compile(r"\\\((.+?)\\\)")
IMAGE = re.compile(r"!\[([^\]]*)\]\(thuc-nghiem/ket-qua/do_chinh/([^)]+\.png)\)")
LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


def math(expr):
    return expr.replace("<", r"\lt ").replace(">", r"\gt ").strip()


def drop_local_link(m):
    return m.group(0) if m.group(2).startswith(("http://", "https://")) else m.group(1)


def escape_at(line):
    """Thoát "Hit@" ở phần chữ thường, không đụng công thức $…$ và mã `…`."""
    parts = re.split(r"(\$[^$\n]+\$|`[^`\n]+`)", line)
    return "".join(p if i % 2 else p.replace("Hit@", "Hit\\@") for i, p in enumerate(parts))


def drop_version_notes(text):
    """Bỏ khối trích dẫn đầu tiên (ghi chú phiên bản) cùng dòng trống ngay sau nó."""
    lines = text.split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith(">"))
    end = start
    while end < len(lines) and lines[end].startswith(">"):
        end += 1
    while end < len(lines) and not lines[end].strip():
        end += 1
    return "\n".join(lines[:start] + lines[end:])


def convert(text):
    out, in_display, in_code = [], False, False
    for line in text.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
            out.append(line)
        elif in_code:
            out.append(line)
        elif line.strip() in (r"\[", r"\]"):
            in_display = line.strip() == r"\["
            out.append("$$")
        elif in_display:
            out.append(math(line))
        else:
            line = INLINE.sub(lambda m: "$" + math(m.group(1)) + "$", line)
            line = IMAGE.sub(lambda m: f"![{m.group(1)}](hinh/{m.group(2)})", line)
            out.append(escape_at(LINK.sub(drop_local_link, line)))
    return "\n".join(out)


def check(src, dst):
    n_inline = len(INLINE.findall(src))
    n_display = sum(1 for line in src.split("\n") if line.strip() == r"\[")
    left = [i + 1 for i, line in enumerate(dst.split("\n")) if re.search(r"\\[\(\)\[\]]", line) and "`" not in line]
    dollars = sum(1 for line in dst.split("\n") if line == "$$")
    local = [m.group(2) for m in LINK.finditer(dst) if not m.group(2).startswith(("http", "hinh/"))]
    no_display = re.sub(r"^\$\$\n.*?\n\$\$$", "", dst, flags=re.S | re.M)
    plain = re.sub(r"\$[^$\n]+\$|`[^`\n]+`", "", no_display)
    bare_at = len(re.findall(r"Hit@", plain))
    print(f"inline: {n_inline}, display: {n_display}, dòng $$: {dollars}, "
          f"còn ký hiệu \\( \\) \\[ \\]: {left}, liên kết cục bộ còn lại: {local}, "
          f"Hit\\@ đã thoát: {plain.count('Hit' + chr(92) + '@')}, Hit@ chưa thoát: {bare_at}")
    assert dollars == 2 * n_display and not left and not local and not bare_at


def write_zip(path, md_name, md_text, images):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(md_name, md_text.encode("utf-8"))
        for img in images:
            z.write(img, f"hinh/{img.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bo-ghi-chu", action="store_true", help="bỏ khối ghi chú phiên bản ở đầu tài liệu")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    src = SRC.read_text(encoding="utf-8")
    if args.bo_ghi_chu:
        src = drop_version_notes(src)
    dst = convert(src)
    check(src, dst)
    OUT_MD.write_bytes(dst.encode("utf-8"))
    OUT_IMG.mkdir(exist_ok=True)
    images = sorted(CHARTS.glob("*.png"))
    for img in images:
        shutil.copy2(img, OUT_IMG / img.name)
    copied = [OUT_IMG / img.name for img in images]
    write_zip(OUT_ZIP, OUT_MD.name, dst, copied)

    # Gói thử: một công thức trong dòng có dấu gạch dưới, một khối công thức, một bảng có \| và một hình
    test = "\n".join([
        "# Thử import",
        "",
        "Công thức trong dòng: $\\operatorname{sup}_D(P)=|\\{(sid,S)\\in D : P\\sqsubseteq S\\}|$ và $1\\le i_1\\lt i_2$.",
        "",
        "$$",
        "\\operatorname{min\\_sup}=\\lceil r\\cdot|D|\\rceil",
        "$$",
        "",
        "| \\|D\\| | r | min_sup |",
        "|---|---|---|",
        "| 20.000 | 0,2% | 40 |",
        "",
        f"![Biểu đồ thử](hinh/{copied[0].name})",
        "",
    ])
    write_zip(TEST_ZIP, "thu-import.md", test, copied[:1])
    for p in (OUT_MD, OUT_ZIP, TEST_ZIP, *copied):
        print(p, p.stat().st_size)


if __name__ == "__main__":
    main()

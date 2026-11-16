"""Đo và đề xuất cách xếp dòng câu trích dẫn hook (cỡ 50 px, khung 960 px, dấu câu cuối dòng treo tới 990 px).

Luật (người dùng chốt 02-10, 03-10, 23-10):
- Mặc định là LẤP ĐẦY: nhồi chữ tới hết khung rồi mới xuống dòng (= make_headline trong plan.py).
- Chỉ tự đặt `headline_lines` khi lấp đầy buộc phải cắt đôi một cụm ("VỀ / NHÀ") hoặc để chữ mồ côi
  ("TIN NHẤT" một mình). Khi đó chọn cách xếp gần lấp đầy nhất mà các dòng dài gần bằng nhau.
- KHÔNG BAO GIỜ để một dòng chỉ 2–3 chữ trong khi dòng khác gần đầy.

Chạy: python do_tieu_de.py "Câu trích dẫn hook."            -> bản lấp đầy + các phương án 3 và 4 dòng
      python do_tieu_de.py "Câu…" --ngoac                    -> phương án có ngoặc kép “ ” (bản lấp đầy luôn có)
      python do_tieu_de.py --do "Dòng 1" "Dòng 2" "Dòng 3"   -> chỉ đo bề rộng các dòng tự viết
"""
import sys, os, re, json
from itertools import combinations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan
from common import SPEC, FONT_XBOLD, vn_upper
from PIL import ImageFont

FONT = ImageFont.truetype(FONT_XBOLD, SPEC["head_size"])
MAXW = SPEC["head_max_w"]
NO_END = {"và", "hay", "hoặc", "nhưng", "mà", "ở", "tại", "của", "với"}   # không treo cuối dòng
DINH_SAU = {"nổi", "kịp", "xuể", "lắm", "đâu"}                                  # không mở đầu dòng ("XOAY / NỔI")


def w(s):
    return round(FONT.getlength(vn_upper(s)))


def fits(s):
    return FONT.getlength(vn_upper(re.sub(r"[”,.:;!?]+$", "", s))) <= MAXW and FONT.getlength(vn_upper(s)) <= MAXW + 30


def options(text, quote=False):
    t = re.sub(r"[.!…]+$", "", text.strip())
    words = t.split()
    low = [x.lower() for x in words]
    links = plan.compound_links(low)
    tags = plan.pos_tags(low)
    ok_break, cost = [], {}
    for i in range(len(words) - 1):
        a, b = plan.bare(words[i]), plan.bare(words[i + 1])
        comma = bool(plan.COMMA_END.search(words[i]))
        if links[i] or (a + " " + b) in plan.PAIRS:
            continue
        if not comma and (a in NO_END or b in plan.BIND_BACK or b in DINH_SAU):   # "VÀ / CON", "KHỎE / NHẤT", "XOAY / NỔI"
            continue
        c = 25 * plan.grammar_cost(tags[i], tags[i + 1])
        if not comma and (a in plan.BIND_FWD or a in {"chẳng", "không", "chưa", "đã", "sẽ", "đang", "rất"}):
            c += 150                                                   # "CHẲNG / PHẢI", "MÀ LÀ / NGƯỜI"
        if not comma and tags[i] == "P" and tags[i + 1] in ("V", "R"):
            c += 150                                                   # chủ ngữ | động từ: "TÔI / NGHĨ"
        if comma:
            c -= 60                                                    # ngắt ở dấu phẩy là tự nhiên nhất
        ok_break.append(i + 1)
        cost[i + 1] = c
    res = []
    for n in (3, 4):
        for cut in combinations(ok_break, n - 1):
            idx = [0, *cut, len(words)]
            lines = [" ".join(words[idx[k]:idx[k + 1]]) for k in range(n)]
            if quote:
                lines[0], lines[-1] = "“" + lines[0], lines[-1] + "”"
            if not all(fits(l) for l in lines):
                continue
            ws = [w(l) for l in lines]
            short = min(len(l.split()) for l in lines)
            orphan = 400 if short <= 3 and max(ws) > 700 else 0
            hole = round(0.2 * sum(MAXW - x for x in ws))                # gần lấp đầy: ít chỗ trống hơn thì tốt hơn
            res.append((max(ws) - min(ws) + orphan + hole + sum(cost[c] for c in cut), n, lines, ws, orphan))
    res.sort(key=lambda r: (r[0], r[1]))
    return res


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "--do":
        for l in a[1:]:
            print(f"{w(l):5d} px  {'OK ' if fits(l) else 'LỐ '} {vn_upper(l)}")
        return
    quote = "--ngoac" in a
    text = [x for x in a if x != "--ngoac"][0]
    g = plan.make_headline(text)["lines"]
    gw = [w(l) for l in g]
    print("Lấp đầy (mặc định, plan.py tự dùng):")
    for l, x in zip(g, gw):
        print(f"  {x:5d} px  {l}")
    if len(g[-1].split()) <= 2 or (len(g) > 1 and min(gw) < 0.45 * max(gw)):
        print("  !! có dòng cụt/mồ côi -> cân nhắc headline_lines bên dưới")
    print("\nPhương án đặt headline_lines (điểm thấp = dòng đều + ngắt đúng chỗ; ★ = không có dòng cụt):")
    for score, n, lines, ws, orphan in options(text, quote)[:8]:
        star = " " if orphan else "★"
        print(f" {star} {n} dòng {ws}  lệch {max(ws) - min(ws)} px, điểm {score}")
        print("     " + json.dumps(lines, ensure_ascii=False))


if __name__ == "__main__":
    main()

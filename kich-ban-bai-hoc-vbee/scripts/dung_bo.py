"""Dựng bộ kịch bản "Bài học từ…": kiểm luật, sinh bản đọc Vbee, xuất JSON và trang HTML để chủ kênh duyệt.

Đầu vào: <thư_mục>/bo.json, một mảng các bài {n, who, title, h, body, nguon, url, goc, doi} (mẫu: examples/bo_mau.json)
  n      số thứ tự, thành tên MP3 "NN - title.mp3"   who    nhân vật         title  tiêu đề ngắn
  h      câu hook (15–20 tiếng)                      body   thân bài một mạch, số viết bằng chữ, tên viết đúng gốc
  nguon  sự kiện, nơi, ngày                          url    danh sách link nguồn    goc  nguyên văn    doi  chỗ đã Việt hoá
Chạy: python dung_bo.py <thư_mục> <tên-bộ>                  ví dụ: python dung_bo.py D:/ssan/kb0511 30-kich-ban-moi-05-11
      python dung_bo.py <thư_mục> <tên-bộ> --chi-hook       bước duyệt hook: trang chỉ có hook + nguồn (body để rỗng được)
      python dung_bo.py <thư_mục> <tên-bộ> --ghi-loai-tru   chủ kênh đã duyệt xong: cộng hook vào data/loai_tru.txt
Ra:   <thư_mục>/<tên-bộ>.json (đủ trường + tts, tieng, kytu)  <thư_mục>/vbee_<tên-bộ>.json ({n, title, text})
      ~/Downloads/<tên-bộ>.html (trang duyệt; toàn bộ dữ liệu nằm trong <script id="data">)
Dòng có "<<<" là vi phạm luật, sửa tới khi hết.
"""
import sys, os, re, json, html

K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(K, "data")
GAPS = [0.05, 0.1, 0.08]          # nhịp nghỉ giữa các câu thân bài (giây), câu cuối 0.12, sau hook 0.08
TONG = (176, 188)                 # tổng tiếng hook + thân: 36–39 s ở Ngọc Huyền 1.1x (4,91 tiếng/giây, đo bộ 3)
HOOK = (15, 20)
CAM = ["Bill Gates", "Coco Chanel", "Chanel", "Benjamin Franklin", "Phil Knight", "Ray Dalio", "Sam Walton",
       "Andrew Carnegie", "Oprah", "Masayoshi Son", "Derek Sivers", "Naval", "Tim Ferriss", "Paul Graham",
       "Morgan Housel", "Kevin Kelly", "Taiichi Ohno", "Estée Lauder", "Howard Schultz"]
KHUON = ["câu này không bảo bạn", "tối nay hãy", "tối nay, hãy", "tuần này hãy", "lần tới hãy", "lần tới, hãy"]


def tieng(s):
    return len(re.sub(r"<break[^>]*>", " ", s).split())


def phien_am():
    cap = json.load(open(os.path.join(DATA, "phien_am.json"), encoding="utf-8"))["cap"]
    return sorted(cap, key=lambda p: -len(p[0]))          # cụm dài thay trước ("Warren Buffett" trước "Buffett")


def doc(t, cap):
    for a, b in cap:
        t = re.sub(r"(?<![\w-])" + re.escape(a) + r"(?![\w-])", b, t)
    return t


def tts_of(h, body, cap):
    s = re.split(r"(?<=[.?!])\s+", doc(body, cap).strip())
    out = doc(h, cap) + " <break time=0.08s/> "
    for i, x in enumerate(s):
        out += x
        if i < len(s) - 1:
            out += " <break time=%ss/> " % (0.12 if i == len(s) - 2 else GAPS[i % 3])
    return out


def bo_dau(s):
    return set(re.findall(r"\w+", s.lower()))


def gan_trung(h, cu):
    """Câu cũ giống nhất (Jaccard theo tập chữ) — >= 0.5 coi như trùng ý, cần đọc lại."""
    a = bo_dau(h)
    best = max(((len(a & bo_dau(c)) / max(1, len(a | bo_dau(c))), c) for c in cu), default=(0, ""))
    return best


def kiem(L, chi_hook):
    cu = [l.strip() for l in open(os.path.join(DATA, "loai_tru.txt"), encoding="utf-8") if l.strip()]
    loi = 0
    dem = {}
    for x in L:
        dem[x["who"]] = dem.get(x["who"], 0) + 1
    for x in L:
        msg = []
        th = tieng(x["h"])
        if not HOOK[0] <= th <= HOOK[1]:
            msg.append(f"hook {th} tiếng (cần {HOOK[0]}–{HOOK[1]})")
        if not chi_hook:
            tg = x["tieng"]                    # đếm trên bản đọc Vbee (tên đã phiên âm) vì đó mới là thứ được đọc
            if not TONG[0] <= tg <= TONG[1]:
                msg.append(f"tổng {tg} tiếng (cần {TONG[0]}–{TONG[1]})")
            if re.search(r"\d", x["body"]):
                msg.append("thân bài có chữ số, phải viết bằng chữ")
            if any(k in x["body"].lower() for k in KHUON):
                msg.append("có câu khuôn bị cấm")
        if re.search(r"\d", x["h"]):
            msg.append("hook có chữ số, phải viết bằng chữ")
        if dem[x["who"]] > 2:
            msg.append(f"{x['who']} có {dem[x['who']]} bài (tối đa 2)")
        if any(c.lower() in x["who"].lower() for c in CAM):
            msg.append("nhân vật nằm trong danh sách loại")
        if not x.get("url"):
            msg.append("thiếu URL nguồn")
        sc, c = gan_trung(x["h"], cu)
        if sc >= 0.5:
            msg.append(f"gần trùng câu cũ ({sc:.2f}): {c}")
        for y in L:
            if y is not x and y["n"] > x["n"]:
                s2 = len(bo_dau(x["h"]) & bo_dau(y["h"])) / max(1, len(bo_dau(x["h"]) | bo_dau(y["h"])))
                if s2 >= 0.5:
                    msg.append(f"gần trùng bài {y['n']:02d}")
        tong = "" if chi_hook else f"tổng {x['tieng']:3d}"
        print(f"{x['n']:02d} {x['who'][:20]:20s} hook {th:2d} {tong}  {'<<< ' + '; '.join(msg) if msg else 'OK'}")
        loi += bool(msg)
    fam = sum(1 for x in L if re.search(r"\b(cha|mẹ|bố|con cái|gia đình|vợ|chồng)\b", x["h"].lower()))
    if fam * 3 > len(L):
        print(f"<<< {fam}/{len(L)} hook về cha mẹ/gia đình, nên dưới 1/3")
    print(f"{len(L)} bài, {loi} bài cần sửa")


CSS = """:root{--bg:#faf8f5;--fg:#1d1b18;--mut:#6b655c;--card:#fff;--acc:#b8090a;--line:#e7e1d8}
@media (prefers-color-scheme:dark){:root{--bg:#151412;--fg:#ece8e1;--mut:#a39b8f;--card:#1f1d1a;--acc:#ff5a4f;--line:#33302b}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:860px;margin:0 auto;padding:24px 16px 64px} h1{font-size:26px;margin:0 0 4px} .lead{color:var(--mut);margin:0 0 24px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:0 0 16px}
.no{font-weight:700;color:var(--acc)} .who{color:var(--mut);font-size:14px} h2{font-size:20px;line-height:1.4;margin:6px 0 10px}
.body{margin:0 0 10px} pre{white-space:pre-wrap;font-size:13px;background:var(--bg);padding:10px;border-radius:8px}
.src{font-size:13px;color:var(--mut);margin:6px 0 0} a{color:var(--acc)} details{margin-top:8px;font-size:14px}"""


def trang(L, ten, chi_hook):
    e = html.escape
    the = []
    for x in L:
        src = "".join(f' <a href="{e(u)}" target="_blank" rel="noopener">[{i + 1}]</a>' for i, u in enumerate(x.get("url") or []))
        p = [f'<article class="card"><div class="no">{x["n"]:02d}</div>'
             f'<div class="who">{e(x["who"])} · {e(x.get("title", ""))}</div><h2>“{e(x["h"])}”</h2>']
        if not chi_hook:
            p.append(f'<p class="body">{e(x["body"])}</p>')
        p.append(f'<p class="src">Nguồn: {e(x.get("nguon") or "")}{src}</p>')
        if x.get("goc") or x.get("doi"):
            p.append(f'<details><summary>Nguyên văn và chỗ đã Việt hoá</summary><p>{e(x.get("goc") or "")}</p>'
                     f'<p>{e(x.get("doi") or "")}</p></details>')
        if not chi_hook:
            p.append(f'<details><summary>Bản đọc Vbee ({x["tieng"]} tiếng)</summary><pre>{e(x["tts"])}</pre></details>')
        p.append("</article>")
        the.append("".join(p))
    lead = ("Danh sách hook chờ duyệt. Thân bài sẽ viết sau khi hook được chốt." if chi_hook else
            "Hook đã duyệt, thân bài viết một mạch. Giọng Ngọc Huyền 1.1x, mỗi bài khoảng 36–39 giây. "
            f"MP3 sẽ nằm trong thư mục <b>Downloads/{e(ten)}</b>.")
    data = json.dumps(L, ensure_ascii=False).replace("</", "<\\/")
    return (f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(ten)}</title><style>{CSS}</style></head><body><main><h1>{len(L)} kịch bản “Bài học từ…” · {e(ten)}</h1>'
            f'<p class="lead">{lead}</p>{"".join(the)}<script id="data" type="application/json">{data}</script></main></body></html>')


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    thu_muc, ten = a[0], a[1]
    chi_hook = "--chi-hook" in a
    L = json.load(open(os.path.join(thu_muc, "bo.json"), encoding="utf-8"))
    L.sort(key=lambda x: x["n"])
    if "--ghi-loai-tru" in a:
        p = os.path.join(DATA, "loai_tru.txt")
        cu = {l.strip() for l in open(p, encoding="utf-8")}
        moi = [x["h"].strip() for x in L if x["h"].strip() not in cu]
        with open(p, "a", encoding="utf-8") as f:
            f.writelines(h + "\n" for h in moi)
        print(f"đã cộng {len(moi)} hook vào {p}")
        return
    if not chi_hook:
        cap = phien_am()
        for x in L:
            x["tts"] = tts_of(x["h"], x["body"], cap)
            x["tieng"] = tieng(x["tts"])
            x["kytu"] = len(re.sub(r"<break[^>]*>", "", x["tts"]))
    kiem(L, chi_hook)
    if not chi_hook:
        json.dump(L, open(os.path.join(thu_muc, ten + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        V = [{"n": x["n"], "title": "%02d - %s" % (x["n"], x["title"]), "text": x["tts"]} for x in L]
        json.dump(V, open(os.path.join(thu_muc, "vbee_" + ten + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
        print("tổng ký tự (điểm Vbee):", sum(x["kytu"] for x in L))
    out = os.path.join(os.path.expanduser("~"), "Downloads", ten + ".html")
    open(out, "w", encoding="utf-8").write(trang(L, ten, chi_hook))
    print("trang duyệt:", out)


if __name__ == "__main__":
    main()

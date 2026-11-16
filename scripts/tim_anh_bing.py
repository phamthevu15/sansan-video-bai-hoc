"""Tìm ảnh nhân vật trên Bing Images (ảnh lớn), bỏ ảnh đã dùng ở video cũ, dựng bảng thu nhỏ có đánh số để chọn bằng mắt.

Bước 1 – tìm:   python tim_anh_bing.py <thư_mục_làm_việc> tim "张一鸣 演讲" "Zhang Yiming portrait" ... [--bo-qua <thư mục video cũ> ...]
                -> <work>/_bing.json (danh sách) + <work>/_bing_0.jpg, _bing_1.jpg … (48 ảnh/bảng, số vàng = chỉ số)
Bước 2 – chọn:  python tim_anh_bing.py <thư_mục_làm_việc> chon 1,10,13,21
                -> <work>/_chon.json đúng định dạng của tai_anh_web.py ([key, url_ảnh, trang_nguồn, tên_miền])
Bước 3 – tải:   python tai_anh_web.py <thư_mục_làm_việc> <work>/_chon.json, rồi loc_trung_anh.py để soát trùng.

Mẹo từ khoá: nhân vật châu Á thì tìm bằng tên gốc (张一鸣, 李嘉诚, 柳井正) + 演讲/采访/年会, ảnh sạch hơn hẳn tìm tiếng Anh.
`--bo-qua` nhận thư mục làm việc của các video cũ cùng nhân vật: URL nào đã có trong images/manifest.json bị loại.
Ảnh Bing chỉ là chỗ tìm; vẫn phải loại ảnh có watermark, chữ chèn, ảnh ghép, ảnh chụp màn hình TV.
"""
import sys, os, io, re, json, html, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def bing(q, pages=2):
    # Thử /images/async trước, rỗng thì thử /images/search. Hai đường này thất thường theo ngày:
    # 29-10 /search trả 0 ảnh, 31-10 /async trả rỗng với từ khoá chữ Hán/Nhật (tiếng Anh vẫn chạy).
    # Cả hai cùng rỗng thì tìm bằng từ khoá tiếng Anh/romaji, hoặc chạy fetch trong trình duyệt của app.
    out = []
    for ep in ("async", "search"):
        for first in range(0, 35 * pages, 35):
            u = (f"https://www.bing.com/images/{ep}?q=" + urllib.parse.quote(q)
                 + f"&first={first}&count=35&qft=+filterui:imagesize-large&mmasync=1&form=IRFLTR")
            req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "vi,zh-CN;q=0.9,en;q=0.8"})
            t = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
            for m in re.findall(r'\sm="([^"]+)"', t):
                try:
                    d = json.loads(html.unescape(m))
                    out.append([d["murl"], d.get("purl", ""), d.get("turl", "")])
                except Exception:
                    pass
        if out:
            break
    return out


def used_urls(dirs):
    s = set()
    for d in dirs:
        p = os.path.join(d, "images", "manifest.json")
        if os.path.exists(p):
            for e in json.load(open(p, encoding="utf-8")):
                s.add(e.get("url"))
                s.add(e.get("source_page_url"))
    return s


def tim(work, args):
    skip = []
    if "--bo-qua" in args:
        k = args.index("--bo-qua")
        args, skip = args[:k], args[k + 1:]
    used = used_urls(skip)
    seen, rows = set(), []
    for q in args:
        try:
            r = bing(q)
        except Exception as e:
            print(q, "LỖI", e)
            continue
        n = 0
        for m, p, tu in r:
            if m not in seen and m not in used:
                seen.add(m)
                rows.append([q, m, p, tu])
                n += 1
        print(f"{q}: {len(r)} kết quả, {n} mới")

    def get(i):
        try:
            b = urllib.request.urlopen(urllib.request.Request(rows[i][3], headers={"User-Agent": UA}), timeout=20).read()
            return i, Image.open(io.BytesIO(b)).convert("RGB")
        except Exception:
            return i, None

    ims = dict(ThreadPoolExecutor(12).map(get, range(len(rows))))
    json.dump(rows, open(os.path.join(work, "_bing.json"), "w", encoding="utf-8"), ensure_ascii=False)
    ok = [i for i in range(len(rows)) if ims[i] is not None]
    cw, ch, cols, per = 300, 220, 8, 48
    for s in range(0, len(ok), per):
        part = ok[s:s + per]
        sh = Image.new("RGB", (cw * cols, ch * ((len(part) + cols - 1) // cols)), "white")
        d = ImageDraw.Draw(sh)
        for j, i in enumerate(part):
            im = ims[i].copy()
            im.thumbnail((cw - 6, ch - 22))
            x, y = (j % cols) * cw, (j // cols) * ch
            sh.paste(im, (x + 3, y + 20))
            d.rectangle([x, y, x + 60, y + 18], fill="yellow")
            d.text((x + 4, y + 3), str(i), fill="black")
        sh.save(os.path.join(work, f"_bing_{s // per}.jpg"), quality=80)
    print(f"{len(rows)} ảnh mới, {(len(ok) + per - 1) // per} bảng _bing_*.jpg trong {work}")


def chon(work, sel):
    rows = json.load(open(os.path.join(work, "_bing.json"), encoding="utf-8"))
    out = []
    for i in [int(x) for x in sel.split(",") if x.strip()]:
        if i >= len(rows):
            sys.exit(f"Không có ảnh số {i} (chỉ có 0..{len(rows) - 1}). Chạy lại bước tim.")
        q, m, p, t = rows[i]
        out.append([f"b{i}", m, p, urllib.parse.urlparse(p).netloc.replace("www.", "")])
    fn = os.path.join(work, "_chon.json")
    json.dump(out, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(out), "ảnh ->", fn)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    work, cmd = sys.argv[1], sys.argv[2]
    os.makedirs(work, exist_ok=True)
    tim(work, sys.argv[3:]) if cmd == "tim" else chon(work, sys.argv[3])

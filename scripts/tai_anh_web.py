"""Tải ảnh báo chí theo danh sách [key, url_ảnh, trang_nguồn, tên_báo] (JSON) vào <thư mục>/web/ và dựng bảng xem nhanh _web_sheet.jpg.

Dùng khi Commons không đủ ảnh nhân vật (luật người dùng 27-09: được dùng ảnh báo chí, cấm watermark/chữ chèn).
Danh sách thường lấy từ Bing Images (bộ lọc imagesize-wallpaper), thuộc tính `m` của a.iusc: murl, purl.
Chạy: python tai_anh_web.py <thư_mục_làm_việc> <danh_sách.json>
"""
import urllib.request, urllib.parse, os, json, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw

work, lst = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(work, "web"), exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}
L = json.load(open(lst, encoding="utf-8"))
json.dump(L, open(os.path.join(work, "web", "list.json"), "w", encoding="utf-8"), ensure_ascii=False)


def get(x):
    k, u = x[0], urllib.parse.quote(x[1], safe=":/?&=%#+,;@!~*'()[]")   # link có chữ Nhật/dấu cách
    fn = os.path.join(work, "web", k + ".jpg")
    if os.path.exists(fn):
        return k, "ok"
    for _ in range(2):
        try:
            d = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
            open(fn + ".t", "wb").write(d)
            Image.open(fn + ".t").convert("RGB").save(fn, quality=95)
            os.remove(fn + ".t")
            return k, "ok"
        except Exception as e:
            err = str(e)[:60]
    return k, err


r = list(ThreadPoolExecutor(6).map(get, L))
print("lỗi:", [x for x in r if x[1] != "ok"])
fs = [(x[0], os.path.join(work, "web", x[0] + ".jpg")) for x in L if os.path.exists(os.path.join(work, "web", x[0] + ".jpg"))]
W, H, cols = 300, 220, 7
rows = (len(fs) + cols - 1) // cols
sh = Image.new("RGB", (W * cols, (H + 20) * rows), "white")
d = ImageDraw.Draw(sh)
for i, (k, f) in enumerate(fs):
    im = Image.open(f)
    w, h = im.size
    im.thumbnail((W, H))
    x, y = (i % cols) * W, (i // cols) * (H + 20)
    sh.paste(im, (x, y))
    d.text((x + 3, y + H + 3), "%d %s %dx%d" % (i, k, w, h), fill="black")
sh.save(os.path.join(work, "_web_sheet.jpg"), quality=80)
print(len(fs), "ảnh")

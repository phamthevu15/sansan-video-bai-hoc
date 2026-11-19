"""Dựng bảng thu nhỏ đánh số từ file mã ảnh Bing (id@tsN, lấy trong trình duyệt của app).
Dùng khi tim_anh_bing.py gọi từ Python bị Bing trả kết quả rác; cách lấy mã xem references/chon-anh.md.
Chạy: python mk_sheet.py <thư_mục_làm_việc>   (đọc <thư_mục>/_th_ids.txt, ghi <thư_mục>/_br_N.jpg)"""
import sys, os, io, urllib.request
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor
w = sys.argv[1]
ids = open(os.path.join(w, '_th_ids.txt'), encoding='utf-8').read().split()
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def get(i):
    tid, host = ids[i].split('@')
    tid = tid if tid.startswith(('OIP', 'OIF')) else 'OIP.' + tid
    try:
        b = urllib.request.urlopen(urllib.request.Request(f"https://{host}.mm.bing.net/th?id={tid}&pid=15.1", headers=UA), timeout=20).read()
        return i, Image.open(io.BytesIO(b)).convert('RGB')
    except Exception:
        return i, None


ims = dict(ThreadPoolExecutor(12).map(get, range(len(ids))))
ok = [i for i in range(len(ids)) if ims[i] is not None]
cw, ch, cols, per = 300, 220, 8, 64
for s in range(0, len(ok), per):
    part = ok[s:s + per]
    sh = Image.new('RGB', (cw * cols, ch * ((len(part) + cols - 1) // cols)), 'white')
    d = ImageDraw.Draw(sh)
    for j, i in enumerate(part):
        im = ims[i].copy(); im.thumbnail((cw - 6, ch - 22)); x, y = (j % cols) * cw, (j // cols) * ch
        sh.paste(im, (x + 3, y + 20)); d.rectangle([x, y, x + 60, y + 18], fill='yellow'); d.text((x + 4, y + 3), str(i), fill='black')
    sh.save(os.path.join(w, f'_br_{s // per}.jpg'), quality=78)
print(len(ids), len(ok), 'sheets', (len(ok) + per - 1) // per)

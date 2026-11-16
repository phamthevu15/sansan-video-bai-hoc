"""Soát ảnh trùng: ảnh ứng viên so với ảnh đã dùng ở các video cũ (cùng nhân vật) và so với nhau.

Chạy: python loc_trung_anh.py <thư_mục_ảnh_ứng_viên> [<thư mục làm việc video cũ> ...]
      ví dụ: python loc_trung_anh.py D:/ssan/video-moi/web D:/ssan/video-cu-1 D:/ssan/video-cu-2
-> in từng ảnh: kích thước, khoảng cách aHash 16x16 tới ảnh đã dùng gần nhất, các ứng viên giống nhau;
   dựng <thư_mục_ảnh_ứng_viên>/../_loc_trung.jpg (nhãn ĐỎ = nghi trùng, VÀNG = mới).

Ngưỡng: aHash < 55 (trên 256) là nghi trùng; md5 trùng là trùng chắc. aHash KHÔNG bắt được ảnh cùng buổi chụp
nhưng khác khung (vd cùng bức tường, cùng áo): luôn xem bảng bằng mắt cạnh ảnh cũ trước khi chốt.
Báo chí đăng lại một ảnh dưới nhiều URL (cafef/cafebiz, sina/sohu) nên md5 khác mà ảnh vẫn là một.
"""
import sys, os, glob, hashlib
from PIL import Image, ImageDraw

NGUONG = 55


def ah(p, n=16):
    im = Image.open(p).convert("L").resize((n, n))
    px = list(im.getdata())
    m = sum(px) / len(px)
    return [1 if v > m else 0 for v in px]


def dist(a, b):
    return sum(x != y for x, y in zip(a, b))


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cand_dir, old = sys.argv[1], sys.argv[2:]
    used = []
    for d in old:
        for f in sorted(glob.glob(os.path.join(d, "images", "*.jpg"))):
            used.append((f, ah(f), md5(f)))
    cands = sorted(f for f in glob.glob(os.path.join(cand_dir, "*.jpg")) if not os.path.basename(f).startswith("_"))
    H = {f: ah(f) for f in cands}
    M = {f: md5(f) for f in cands}
    rows = []
    for f in cands:
        best = min(((dist(H[f], u), uf, um == M[f]) for uf, u, um in used), default=(999, "", False))
        near = [os.path.basename(g)[:-4] for g in cands if g != f and (dist(H[f], H[g]) < NGUONG or M[g] == M[f])]
        k, sz = os.path.basename(f)[:-4], Image.open(f).size
        trung = best[2] or best[0] < NGUONG
        note = ("TRÙNG md5 " if best[2] else f"aHash {best[0]:3d} ") + (os.path.relpath(best[1]) if best[0] < 60 else "")
        print(f"{'!! ' if trung else '   '}{k:12s} {sz[0]}x{sz[1]:<5d} {note}  giống ứng viên: {near or '-'}")
        rows.append((k, f, sz, trung, best[0]))
    cw, ch, cols = 330, 250, 7
    sh = Image.new("RGB", (cw * cols, ch * ((len(rows) + cols - 1) // cols or 1)), "white")
    d = ImageDraw.Draw(sh)
    for j, (k, f, sz, trung, s) in enumerate(rows):
        im = Image.open(f).convert("RGB")
        im.thumbnail((cw - 6, ch - 24))
        x, y = (j % cols) * cw, (j // cols) * ch
        sh.paste(im, (x + 3, y + 22))
        d.rectangle([x, y, x + cw - 4, y + 20], fill="red" if trung else "yellow")
        d.text((x + 4, y + 4), f"{k} {sz[0]}x{sz[1]} a{s}", fill="black")
    out = os.path.join(os.path.dirname(os.path.abspath(cand_dir)), "_loc_trung.jpg")
    sh.save(out, quality=82)
    print("bảng:", out)


if __name__ == "__main__":
    main()

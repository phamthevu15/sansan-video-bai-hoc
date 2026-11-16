"""Đổi chữ thương hiệu trên ribbon kem của khuôn hook (17-10-2026: kênh SanSan Academy bị gậy, chuyển sang SEE THE LIGHT).

Đầu vào: assets/hook_template_sansan.png (khuôn gốc tách từ video mẫu, chữ "SANSAN ACADEMY").
Đầu ra:  assets/hook_template_stl.png (chữ mới, cùng màu đỏ, cùng chiều cao chữ hoa, cùng độ giãn chữ, căn giữa đúng chỗ cũ).

Cách làm: đo lại chữ cũ ngay trên khuôn (vị trí, chiều cao chữ hoa, khoảng cách chữ, khoảng trắng giữa từ),
xoá chữ cũ bằng inpaint màu kem, vẽ chữ mới siêu mẫu x4 rồi thu nhỏ để biên chữ mịn như bản gốc.
Chạy: python make_brand_template.py "SEE THE LIGHT" [font.ttf]
"""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
SRC = os.path.join(ASSETS, "hook_template_sansan.png")
DST = os.path.join(ASSETS, "hook_template_stl.png")
TEXT = sys.argv[1] if len(sys.argv) > 1 else "SEE THE LIGHT"
FONT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ASSETS, "fonts", "BeVietnamPro-Medium.ttf")
# vùng kem chứa chữ (đo trên khuôn 1080x1920): x 237–711, y 1110–1179; chữ nằm trọn trong x 276–673
BOX = (274, 1118, 676, 1172)

im = np.array(Image.open(SRC).convert("RGBA"))
x0, y0, x1, y1 = BOX
reg = im[y0:y1, x0:x1, :3].astype(np.int32)
txt = (reg[..., 0] > 120) & (reg[..., 1] < 150) & (reg[..., 2] < 150)      # chữ đỏ (cả viền khử răng cưa)
soft = (reg.sum(2) < 640)                                                    # biên pha kem
mask = (txt | (soft & cv2.dilate(txt.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)))
ys, xs = np.where(txt)
cap_top, cap_bot = ys.min() + y0, ys.max() + y0
cap = cap_bot - cap_top + 1
red = np.median(reg[txt & (reg[..., 1] < 40)], 0)
cols = np.where(txt.any(0))[0]
glyphs, s = [], None
for x in range(cols.min(), cols.max() + 2):
    on = x <= cols.max() and txt[:, x].any()
    if on and s is None:
        s = x
    if not on and s is not None:
        glyphs.append((s + x0, x - 1 + x0)); s = None
gaps = [b[0] - a[1] - 1 for a, b in zip(glyphs, glyphs[1:])]
word_gap = max(gaps)
letter_gap = float(np.median([g for g in gaps if g < word_gap * 0.7]))
center = (glyphs[0][0] + glyphs[-1][1]) / 2
print("chữ cũ: %d glyph, cao chữ hoa %d px (y %d–%d), khoảng chữ %.1f px, khoảng từ %d px, tâm x %.1f, đỏ %s"
      % (len(glyphs), cap, cap_top, cap_bot, letter_gap, word_gap, center, red.astype(int).tolist()))

# xoá chữ cũ: dựng lại dải kem bằng nội suy theo cột giữa các hàng kem sạch ngay trên và dưới chữ
# (inpaint để lại vệt trắng vì chữ gốc có quầng sáng mảnh quanh nét)
ta, tb = cap_top - 6, cap_bot + 6                  # dải thay thế
top = im[ta - 5:ta, x0:x1, :3].astype(np.float32).mean(0)
bot = im[tb + 1:tb + 6, x0:x1, :3].astype(np.float32).mean(0)
top = cv2.GaussianBlur(top[None], (0, 0), sigmaX=8, sigmaY=0.1)[0]
bot = cv2.GaussianBlur(bot[None], (0, 0), sigmaX=8, sigmaY=0.1)[0]
for k, y in enumerate(range(ta, tb + 1)):
    t = (k + 0.5) / (tb - ta + 1)
    im[y, x0:x1, :3] = np.clip(top * (1 - t) + bot * t, 0, 255).astype(np.uint8)
# nối mép trái/phải dải thay thế cho khỏi lộ đường cắt
for xe in (x0, x1 - 1):
    sl = im[ta:tb + 1, xe - 3:xe + 4, :3].astype(np.float32)
    im[ta:tb + 1, xe - 3:xe + 4, :3] = cv2.GaussianBlur(sl, (0, 0), 1.5).astype(np.uint8)

# vẽ chữ mới siêu mẫu x4
SS = 4
def cap_h(f):
    b = f.getbbox("H"); return b[3] - b[1]
size = 10
while cap_h(ImageFont.truetype(FONT, size * SS)) < cap * SS:
    size += 1
f = ImageFont.truetype(FONT, size * SS)
# bề rộng từng chữ theo hộp mực thật, xếp với khoảng chữ / khoảng từ đo được
items, x = [], 0.0
for ch in TEXT:
    if ch == " ":
        x += (word_gap - letter_gap) * SS
        continue
    b = f.getbbox(ch)
    items.append((ch, x - b[0], b))
    x += (b[2] - b[0]) + letter_gap * SS
total = x - letter_gap * SS
W = int(total + 40 * SS); H = int((cap + 30) * SS)
lay = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(lay)
base_y = 15 * SS + cap * SS            # đường chân chữ hoa
for ch, xx, b in items:
    d.text((20 * SS + xx, base_y), ch, font=f, fill=255, anchor="ls")
lay = lay.resize((W // SS, H // SS), Image.LANCZOS)
a = np.array(lay).astype(np.float32) / 255
ox = int(round(center - total / SS / 2)) - 20
oy = cap_bot + 1 - (15 + cap)
h, w = a.shape
seg = im[oy:oy + h, ox:ox + w, :3].astype(np.float32)
seg = seg * (1 - a[..., None]) + red[None, None, :] * a[..., None]
im[oy:oy + h, ox:ox + w, :3] = np.clip(seg, 0, 255).astype(np.uint8)
Image.fromarray(im).save(DST)
print("chữ mới: %r, font %s cỡ %d, rộng %.0f px -> %s" % (TEXT, os.path.basename(FONT), size, total / SS, DST))

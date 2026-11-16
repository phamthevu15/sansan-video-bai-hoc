"""Thông số chuẩn đo từ 4 video mẫu SanSan Academy (bản 25/09: Lee Kun-hee, Akio Morita)
và các tiện ích dùng chung. Mọi con số ở đây là số đo thật, xem references/thong-so-thiet-ke.md.
"""
import os, glob, shutil, subprocess, json

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SKILL_DIR, "assets")
FONT_BOLD = os.path.join(ASSETS, "fonts", "Inter-Bold.ttf")
FONT_XBOLD = os.path.join(ASSETS, "fonts", "Inter-ExtraBold.ttf")
# 17-10-2026: kênh SanSan Academy bị gậy -> ribbon đổi chữ thành SEE THE LIGHT (scripts/make_brand_template.py).
# Khuôn cũ giữ ở assets/hook_template_sansan.png (= hook_template.png).
HOOK_TEMPLATE = os.path.join(ASSETS, "hook_template_stl.png")

SPEC = {
    # khung hình
    "W": 1080, "H": 1920, "FPS": 30,
    # ---- HOOK (0 -> lúc câu thứ hai bắt đầu)
    "hook_pan_px": 194.0,          # ảnh chân dung trượt trái 194 px (18% x 1080), tuyến tính
    "hook_zone_h": 1160,           # ảnh phủ kín vùng 0..1160 (dưới đó là nền đỏ đặc)
    "hook_face_y": 430,            # điểm nhấn (mắt) đặt quanh y=430
    "label_font": "bold", "label_size": 34, "label_x": 68, "label_baseline": 1227, "label_stroke": 2,
    "head_font": "xbold", "head_size": 50, "head_x": 68, "head_baselines": [1311, 1386, 1461],
    "head_stroke": 3, "head_max_w": 960,   # lề phải 52 px; 944 (lề đối xứng) làm "THÀNH CÔNG," rơi xuống dòng để trống 366 px
    "text_stroke_rgba": (0, 0, 0, 148),   # viền chữ hook: đen 58% -> thành đỏ sẫm trên nền đỏ
    # ---- THÂN VIDEO
    "fg_base_w": 926,              # ảnh chính rộng 926 px (lề 77 px mỗi bên) ở scale 1.0
    "fg_center": (540, 960),
    "zoom_k": (1.10, 1.11),        # zoom 10-11%, tuyến tính, tâm (540,960)
    "pan_w": 1026,                 # ảnh pan rộng cố định 1026 px (0.95 W)
    "pan_px": 89.0,                # pan: tâm đi từ 540+44.5 -> 540-44.5 (hoặc ngược lại)
    "bg_blur_sigma": 25.0,         # nền = chính ảnh phủ kín khung x scale ảnh, Gauss sigma 25
    "bg_gain": 0.385,              # độ sáng nền 38.5%
    "bg_grad_y0": 1080, "bg_grad_alpha": 0.55,   # phủ đen tuyến tính từ y=1080 (0) tới đáy (0.55)
    "shadow_sigma": 25.0, "shadow_opacity": 0.60,  # bóng đổ quanh ảnh chính, không lệch
    # ---- PHỤ ĐỀ (ASS / libass, karaoke \kf)
    "sub_font_size_px": 37,        # Inter Bold, chữ hoa cao 26 px
    "sub_baseline": 1452, "sub_center_x": 540,
    "sub_outline": 4, "sub_shadow": 2,
    "sub_white": "&H00FFFFFF", "sub_yellow": "&H0000D4FF",   # #FFD400
    "sub_max_words": 6, "sub_target_words": 5, "sub_max_w": 930,
    "sub_lead": 0.03,              # bù độ trễ của mốc CTC (s)
    "sub_tail": 0.08,              # giữ chữ sau từ cuối câu trước khi ẩn (s)
    # ---- NHỊP CẮT ẢNH
    "shot_min": 1.9, "shot_max": 4.5,
    "pause_sentence": 0.15,        # khoảng lặng tối thiểu để coi là hết câu
    # ---- ÂM THANH / XUẤT FILE
    "loudnorm": "I=-16:TP=-1.5:LRA=11",
    "crf": 18,
}

FUNCTION_WORDS = set("""của và với là những các một cho để thì mà nhưng rằng khi nếu vì về từ trong trên
đến bằng như cũng đã đang sẽ không rất có hay hoặc nên do bởi tại theo sang ra vào lại được bị này đó ấy
ở mọi mỗi nhiều ít hơn nhất càng""".split())


def ffmpeg_bin(name="ffmpeg"):
    p = shutil.which(name)
    if p:
        return p
    local = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))
    pats = [os.path.join(local, "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "*", "bin", name + ".exe"),
            os.path.join("C:\\", "ffmpeg", "bin", name + ".exe")]
    for pat in pats:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    raise SystemExit(f"Không tìm thấy {name}. Cài bằng: winget install Gyan.FFmpeg")


def probe_duration(path):
    out = subprocess.run([ffmpeg_bin("ffprobe"), "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True).stdout
    return float(out.strip())


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, p):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def vn_upper(s):
    return s.upper()

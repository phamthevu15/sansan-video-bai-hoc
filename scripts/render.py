"""Bước 5: dựng MP4 từ plan.json.

    python render.py work/plan.json out.mp4 [--preview]

- Hook: ảnh chân dung trượt trái 194 px + template nền đỏ + nhãn + câu trích dẫn.
- Thân: nền mờ (chính ảnh đó) + bóng đổ + ảnh chính pan/zoom tuyến tính.
- Phụ đề karaoke ASS (libass, \\kf) đốt thẳng vào hình trong cùng lượt ffmpeg.
- Âm thanh: loudnorm 2 lượt về -16 LUFS / -1.5 dBTP, AAC 48 kHz mono.
--preview: chỉ dựng 1 frame mỗi 0.5 s ra ảnh PNG để soát nhanh (không ra MP4).
"""
import sys, os, json, math, subprocess, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SPEC, FONT_BOLD, FONT_XBOLD, HOOK_TEMPLATE, ffmpeg_bin, load_json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = SPEC["W"], SPEC["H"], SPEC["FPS"]


# ------------------------------------------------------------------ tiện ích ảnh
def load_rgb(path):
    im = Image.open(path)
    try:
        from PIL import ImageOps
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass
    im = im.convert("RGB")
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)


def resize_to(img, w, h):
    interp = cv2.INTER_AREA if w < img.shape[1] else cv2.INTER_CUBIC
    return cv2.resize(img, (max(1, int(round(w))), max(1, int(round(h)))), interpolation=interp)


# ------------------------------------------------------------------ chữ hook
def text_layer(lines, font_path, size, x, baselines, stroke, rgba_stroke):
    """Lớp RGBA: chữ trắng + viền (đen 58%) vẽ tách mặt nạ rồi ghép để không lem."""
    font = ImageFont.truetype(font_path, size)
    fill = Image.new("L", (W, H), 0)
    strk = Image.new("L", (W, H), 0)
    df, ds = ImageDraw.Draw(fill), ImageDraw.Draw(strk)
    for line, by in zip(lines, baselines):
        df.text((x, by), line, font=font, fill=255, anchor="ls")
        ds.text((x, by), line, font=font, fill=255, anchor="ls", stroke_width=stroke, stroke_fill=255)
    f = np.asarray(fill, np.float32) / 255
    s = np.asarray(strk, np.float32) / 255
    a_s = s * rgba_stroke[3] / 255.0
    out_a = f + a_s * (1 - f)
    rgb = (f[..., None] * 255 + (1 - f[..., None]) * a_s[..., None] * np.array(rgba_stroke[:3], np.float32)) \
        / np.maximum(out_a[..., None], 1e-6)
    lay = np.zeros((H, W, 4), np.float32)
    lay[..., :3] = rgb[..., ::-1]  # BGR
    lay[..., 3] = out_a
    return lay


def over(dst, lay):
    """Ghép lớp BGRA (float 0..1 alpha) lên ảnh BGR float."""
    a = lay[..., 3:4]
    return dst * (1 - a) + lay[..., :3] * a


def build_hook_static(hook):
    tpl = cv2.imread(HOOK_TEMPLATE, cv2.IMREAD_UNCHANGED).astype(np.float32)
    tpl_l = np.concatenate([tpl[..., :3], tpl[..., 3:4] / 255.0], 2)
    head = hook["headline"]
    n = len(head["lines"])
    bl = SPEC["head_baselines"][:n] if n <= 3 else [SPEC["head_baselines"][0] + 75 * i for i in range(n)]
    lab = text_layer([hook["label"]], FONT_BOLD, SPEC["label_size"], SPEC["label_x"], [SPEC["label_baseline"]],
                     SPEC["label_stroke"], SPEC["text_stroke_rgba"])
    hl = text_layer(head["lines"], FONT_XBOLD, head["size"], SPEC["head_x"], bl, SPEC["head_stroke"],
                    SPEC["text_stroke_rgba"])
    return tpl_l, lab, hl


class HookRenderer:
    def __init__(self, hook, base_dir):
        self.hook = hook
        img = load_rgb(os.path.join(base_dir, hook["image"]))
        ih, iw = img.shape[:2]
        zone_w, zone_h = W + SPEC["hook_pan_px"], SPEC["hook_zone_h"]
        sc = max(zone_w / iw, zone_h / ih)
        self.photo = resize_to(img, iw * sc, ih * sc)
        ph = self.photo.shape[0]
        face = hook.get("face_y", 0.33) * ph
        self.y0 = float(np.clip(SPEC["hook_face_y"] - face, zone_h - ph, 0))
        # gộp template + nhãn + câu trích dẫn thành một lớp premultiplied để mỗi frame chỉ ghép 1 lần
        P = np.zeros((H, W, 3), np.float32)
        A = np.zeros((H, W, 1), np.float32)
        for lay in build_hook_static(hook):
            a = lay[..., 3:4]
            P = lay[..., :3] * a + P * (1 - a)
            A = a + A * (1 - a)
        A1 = A[..., 0]
        self.C = np.clip(P / np.maximum(A, 1e-4) + 0.5, 0, 255).astype(np.uint8)   # màu lớp phủ (bỏ premultiply)
        self.A, self.inv_A = A1.astype(np.float32), (1 - A1).astype(np.float32)
        self.n1 = hook["n1"]

    def frame(self, n):
        p = n / max(1, self.n1 - 1)
        x = -SPEC["hook_pan_px"] * p
        M = np.float32([[1, 0, x], [0, 1, self.y0]])
        f = cv2.warpAffine(self.photo, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return cv2.blendLinear(self.C, f, self.A, self.inv_A)


# ------------------------------------------------------------------ thân video
class ShotRenderer:
    def __init__(self, shot, base_dir):
        img = load_rgb(os.path.join(base_dir, shot["image"]))
        ih, iw = img.shape[:2]
        self.shot = shot
        self.n0, self.n1 = shot["n0"], shot["n1"]
        mo = shot["motion"]
        k = shot.get("k") or SPEC["zoom_k"][0]
        bw = SPEC["fg_base_w"]
        if mo.startswith("pan"):
            s_a = s_b = SPEC["pan_w"] / bw
            half = SPEC["pan_px"] / 2
            dx_a, dx_b = (half, -half) if mo == "pan_left" else (-half, half)
        elif mo == "zoom_in":
            s_a, s_b, dx_a, dx_b = 1.0, k, 0, 0
        elif mo == "zoom_out":
            s_a, s_b, dx_a, dx_b = k, 1.0, 0, 0
        else:
            s_a = s_b = 1.0; dx_a = dx_b = 0
        self.s_a, self.s_b, self.dx_a, self.dx_b = s_a, s_b, dx_a, dx_b
        smax = max(s_a, s_b)
        self.smax = smax
        # ảnh chính dựng sẵn ở kích thước lớn nhất của shot
        fw = bw * smax
        fh = fw * ih / iw
        self.fg = resize_to(img, fw, fh)
        self.fg_a = np.full(self.fg.shape[:2], 255, np.uint8)
        self.bh = bw * ih / iw  # chiều cao ở scale 1.0
        # nền: phủ kín khung x scale lớn nhất, làm mờ ở 1/2 độ phân giải
        q = 2
        cover = max(W / iw, H / ih)
        bgw, bgh = iw * cover * smax / q, ih * cover * smax / q
        bg = resize_to(img, bgw, bgh).astype(np.float32)
        self.bg = cv2.GaussianBlur(bg, (0, 0), SPEC["bg_blur_sigma"] / q)
        self.q = q
        # bóng đổ: hình chữ nhật đen làm mờ, dựng ở 1/2 độ phân giải có đệm
        pad = int(SPEC["shadow_sigma"] * 3)
        sw, sh = int(round(fw / q)) + 2 * pad // q, int(round(fh / q)) + 2 * pad // q
        sm = np.zeros((sh, sw), np.float32)
        sm[pad // q: sh - pad // q, pad // q: sw - pad // q] = 1
        self.sh = cv2.GaussianBlur(sm, (0, 0), SPEC["shadow_sigma"] / q) * SPEC["shadow_opacity"]
        self.sh_pad = pad // q
        # hệ số sáng nền theo hàng (nửa độ phân giải)
        ys = (np.arange(H // q) + 0.5) * q
        grad = np.clip((ys - SPEC["bg_grad_y0"]) / (H - SPEC["bg_grad_y0"]), 0, 1) * SPEC["bg_grad_alpha"]
        self.row_gain = (SPEC["bg_gain"] * (1 - grad)).astype(np.float32)[:, None, None]
        self.cover = cover

    def params(self, n):
        span = max(1, self.n1 - self.n0 - 1)
        p = min(1.0, max(0.0, (n - self.n0) / span))
        s = self.s_a + (self.s_b - self.s_a) * p
        dx = self.dx_a + (self.dx_b - self.dx_a) * p
        return s, dx

    def frame(self, n):
        s, dx = self.params(n)
        cx, cy = SPEC["fg_center"][0] + dx, SPEC["fg_center"][1]
        q = self.q
        # nền
        r = s / self.smax
        bgh, bgw = self.bg.shape[:2]
        M = np.float32([[r, 0, cx / q - bgw * r / 2], [0, r, cy / q - bgh * r / 2]])
        bg = cv2.warpAffine(self.bg, M, (W // q, H // q), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # bóng đổ
        fw = SPEC["fg_base_w"] * s
        fh = self.bh * s
        shh, shw = self.sh.shape
        rs = (fw / q) / (shw - 2 * self.sh_pad)
        Ms = np.float32([[rs, 0, (cx - fw / 2) / q - self.sh_pad * rs], [0, rs, (cy - fh / 2) / q - self.sh_pad * rs]])
        sha = cv2.warpAffine(self.sh, Ms, (W // q, H // q), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        bg = bg * self.row_gain * (1 - sha[..., None])
        f = cv2.resize(np.clip(bg + 0.5, 0, 255).astype(np.uint8), (W, H), interpolation=cv2.INTER_LINEAR)
        # ảnh chính
        rf = s / self.smax
        fgh, fgw = self.fg.shape[:2]
        Mf = np.float32([[rf, 0, cx - fgw * rf / 2], [0, rf, cy - fgh * rf / 2]])
        fg = cv2.warpAffine(self.fg, Mf, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        fa = cv2.warpAffine(self.fg_a, Mf, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        a = fa.astype(np.float32) * (1 / 255.0)
        return cv2.blendLinear(fg, f, a, 1 - a)


# ------------------------------------------------------------------ phụ đề ASS
def ass_time(t):
    t = max(0.0, t)
    # LÀM TRÒN XUỐNG (không làm tròn gần nhất): ASS chỉ có độ phân giải 1/100 s, làm tròn lên
    # 4,166 -> 4,17 là muộn hơn frame 125 (4,1667 s) và phụ đề hiện trễ 1 frame.
    cs = int(t * 100 + 1e-6)
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def build_ass(subs, path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
ScaledBorderAndShadow: yes
WrapStyle: 2
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter,46,{SPEC['sub_yellow']},{SPEC['sub_white']},&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,{SPEC['sub_outline']},{SPEC['sub_shadow']},2,20,20,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for c in subs:
        t_in, t_out = c["t_in"], c["t_out"]
        t_in = int(t_in * 100 + 1e-6) / 100   # mốc karaoke tính từ đúng thời điểm Dialogue bắt đầu
        ws = c["words"]
        # mốc tích luỹ tính bằng centi-giây, lấy hiệu của giá trị đã làm tròn để không trôi
        marks = [t_in] + [max(t_in, w["s"]) for w in ws] + [max(ws[-1]["e"], ws[-1]["s"] + 0.12)]
        for i in range(1, len(marks)):
            marks[i] = max(marks[i], marks[i - 1])
        cs = [int(round((m - t_in) * 100)) for m in marks]
        parts = []
        if cs[1] > 0:
            parts.append("{\\k%d}" % cs[1])
        for i, w in enumerate(ws):
            d = cs[i + 2] - cs[i + 1]
            sep = " " if i < len(ws) - 1 else ""
            parts.append("{\\kf%d}%s%s" % (max(1, d), w["w"], sep))
        text = "{\\an2\\pos(%d,%d)}" % (SPEC["sub_center_x"], SPEC["sub_baseline"] + 10) + "".join(parts)
        lines.append(f"Dialogue: 0,{ass_time(t_in)},{ass_time(t_out)},Sub,,0,0,0,,{text}")
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(head + "\n".join(lines) + "\n")


# ------------------------------------------------------------------ âm thanh
def loudnorm_filter(audio):
    ff = ffmpeg_bin()
    r = subprocess.run([ff, "-hide_banner", "-nostats", "-i", audio, "-af",
                        f"loudnorm={SPEC['loudnorm']}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    txt = r.stderr
    js = json.loads(txt[txt.rindex("{"):txt.rindex("}") + 1])
    return (f"loudnorm={SPEC['loudnorm']}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
            f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")


# ------------------------------------------------------------------ main
def main(plan_p, out_p, preview=False):
    plan = load_json(plan_p)
    base = os.path.dirname(os.path.abspath(plan_p))
    cfg_dir = plan.get("base_dir") or base
    N = plan["n_frames"]
    hook = HookRenderer(plan["hook"], cfg_dir)
    shots = plan["shots"]
    cache = {}

    def get_frame(n):
        if n < plan["hook"]["n1"]:
            return hook.frame(n)
        for i, s in enumerate(shots):
            if s["n0"] <= n < s["n1"]:
                if i not in cache:
                    cache.clear()
                    cache[i] = ShotRenderer(s, cfg_dir)
                return cache[i].frame(n)
        return cache[max(cache)].frame(n) if cache else hook.frame(n)

    work = tempfile.mkdtemp(prefix="ssv_")
    fonts = os.path.join(work, "subfonts")
    os.makedirs(fonts)
    shutil.copy(FONT_BOLD, fonts)
    build_ass(plan["subs"], os.path.join(work, "subs.ass"))
    shutil.copy(os.path.join(work, "subs.ass"), os.path.join(base, "subs.ass"))

    if preview:
        outdir = out_p
        os.makedirs(outdir, exist_ok=True)
        ff = ffmpeg_bin()
        pick = [a for a in sys.argv if a.startswith("--frames=")]
        frames = [int(x) for x in pick[0].split("=", 1)[1].split(",")] if pick else range(0, N, FPS // 2)
        for n in frames:
            f = get_frame(n)
            raw = os.path.join(work, "f.png")
            cv2.imwrite(raw, f)
            t = n / FPS
            subprocess.run([ff, "-v", "error", "-y", "-i", "f.png", "-vf",
                            f"settb=1/1000000,setpts={t}/TB,subtitles=subs.ass:fontsdir=subfonts",
                            os.path.join(os.path.abspath(outdir), f"p_{n:05d}.png")], cwd=work, check=True)
        print("preview ->", outdir)
        return

    af = loudnorm_filter(plan["audio"])
    ff = ffmpeg_bin()
    cmd = [ff, "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", plan["audio"],
           "-filter_complex", f"[0:v]subtitles=subs.ass:fontsdir=subfonts,format=yuv420p[v];"
                              f"[1:a]{af},aresample=48000,aformat=channel_layouts=mono[a]",
           "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(SPEC["crf"]), "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
           os.path.abspath(out_p)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, cwd=work)
    for n in range(N):
        f = get_frame(n)
        p.stdin.write(f.tobytes())
        if n % 150 == 0:
            print(f"  frame {n}/{N}", flush=True)
    p.stdin.close()
    p.wait()
    if p.returncode != 0:
        raise SystemExit("ffmpeg lỗi")
    print("xong ->", out_p)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(a[0], a[1], preview="--preview" in sys.argv)

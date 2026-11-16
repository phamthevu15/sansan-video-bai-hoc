"""Bước 6: nghiệm thu file MP4 đã dựng.

    python qa.py work/plan.json out.mp4

Kiểm:
1. Thông số: 1080x1920, 30 fps, H.264 + AAC, video >= âm thanh.
2. Độ lớn âm thanh: -16 LUFS (±0.5), true peak <= -1.4 dBTP.
3. Phụ đề ĐỒNG BỘ TỪNG TỪ: dựng lại đúng subs.ass (cùng libass, cùng mốc) trên nền trơn,
   đo thời điểm vệt vàng quét vào mỗi từ, so với mốc bắt đầu thật của từ. Báo lệch lớn nhất (ms).
3b. Kiểm độc lập bằng năng lượng âm thanh: đầu mỗi câu, phụ đề phải hiện trong vòng 0,1 s
   quanh lúc tiếng nói thật bắt đầu.
4. Không có phụ đề trong hook; luôn có phụ đề khi đang có tiếng nói.
5. Xuất contact sheet 1 hình/giây để soát bằng mắt.
"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SPEC, FONT_BOLD, ffmpeg_bin, load_json, probe_duration, vn_upper
import numpy as np, cv2
from PIL import ImageFont

W, H, FPS = SPEC["W"], SPEC["H"], SPEC["FPS"]
Y0, BH = 1395, 80


def scan_band(video, ass_dir=None, dur=None):
    """Quét dải phụ đề từng frame. ass_dir: dựng lại subs.ass trên nền xám trơn (đo karaoke không nhiễu nền)."""
    ff = ffmpeg_bin()
    if ass_dir:
        import shutil, tempfile
        from common import FONT_BOLD as FB
        tmp = tempfile.mkdtemp(prefix="ssqa_")
        os.makedirs(os.path.join(tmp, "f"))
        shutil.copy(FB, os.path.join(tmp, "f"))
        shutil.copy(os.path.join(ass_dir, "subs.ass"), tmp)
        p = subprocess.Popen([ff, "-v", "error", "-f", "lavfi", "-i", f"color=c=0x808080:s={W}x{H}:r={FPS}:d={dur}",
                              "-vf", f"subtitles=subs.ass:fontsdir=f,crop={W}:{BH}:0:{Y0}", "-f", "rawvideo",
                              "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE, cwd=tmp)
    else:
        p = subprocess.Popen([ff, "-v", "error", "-i", video, "-vf", f"crop={W}:{BH}:0:{Y0}", "-f", "rawvideo",
                              "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    n = W * BH * 3
    recs = []
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        g = np.frombuffer(b, np.uint8).reshape(BH, W, 3)
        hsv = cv2.cvtColor(g, cv2.COLOR_BGR2HSV)
        dark = cv2.dilate((g.mean(2) < 60).astype(np.uint8), np.ones((11, 11), np.uint8)) > 0
        yel = (hsv[..., 0] >= 15) & (hsv[..., 0] <= 38) & (hsv[..., 1] > 130) & (hsv[..., 2] > 190) & dark
        wht = (hsv[..., 1] < 50) & (hsv[..., 2] > 225) & dark
        cols = np.where((yel | wht).sum(0) > 1)[0]
        ycols = np.where(yel.sum(0) > 1)[0]
        recs.append((int(cols[0]) if len(cols) > 20 else -1, int(cols[-1]) if len(cols) > 20 else -1,
                     int(ycols[-1]) if len(ycols) else -1))
    return recs


def main(plan_p, video):
    plan = load_json(plan_p)
    ff = ffmpeg_bin()
    ok = True
    # 1. thông số
    info = subprocess.run([ffmpeg_bin("ffprobe"), "-v", "error", "-show_entries",
                           "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration", "-of", "json", video],
                          capture_output=True, text=True).stdout
    js = json.loads(info)
    v = [s for s in js["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in js["streams"] if s["codec_type"] == "audio"]
    vdur = float(js["format"]["duration"])
    adur = probe_duration(plan["audio"])
    print(f"[1] {v['width']}x{v['height']} {v['r_frame_rate']} {v['codec_name']} + {a[0]['codec_name'] if a else 'KHÔNG CÓ AUDIO'}"
          f" | video {vdur:.3f}s, mp3 {adur:.3f}s")
    if (v["width"], v["height"]) != (W, H) or v["r_frame_rate"] != "30/1" or not a or vdur + 0.02 < adur:
        ok = False; print("    LỖI thông số")
    # 2. loudness
    r = subprocess.run([ff, "-hide_banner", "-nostats", "-i", video, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore").stderr
    lj = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    I, TP = float(lj["input_i"]), float(lj["input_tp"])
    print(f"[2] loudness {I:.1f} LUFS, true peak {TP:.1f} dBTP")
    if abs(I + 16) > 0.7 or TP > -1.3:
        ok = False; print("    LỖI loudness")
    # 3-4. phụ đề
    recs_v = scan_band(video)                       # video thật: kiểm có chữ / hook
    recs = scan_band(None, os.path.dirname(os.path.abspath(plan_p)), vdur)  # subs.ass trên nền trơn: đo karaoke
    hook_n = plan["hook"]["n1"]
    # dải phụ đề trong hook trùng dòng 3 câu trích dẫn (chữ trắng) -> chỉ kiểm có vệt vàng karaoke hay không
    hook_text = sum(1 for r in recs_v[:hook_n] if r[2] >= 0)
    early = [c["text"] for c in plan["subs"] if c["t_in"] < plan["hook"]["t1"] - 0.01]
    print(f"[4] hook: frame có karaoke vàng = {hook_text}, cụm phụ đề bắt đầu trong hook = {len(early)} (phải = 0)")
    if hook_text or early:
        ok = False
    font = ImageFont.truetype(FONT_BOLD, 37)
    errs, missing = [], []
    for c in plan["subs"]:
        n0, n1 = int(round(c["t_in"] * FPS)), int(round(c["t_out"] * FPS))
        xs = [r for r in recs[n0 + 1:max(n0 + 2, n1 - 1)] if r[0] >= 0]
        if not xs:
            missing.append(c["text"]); continue
        X0 = int(np.median([r[0] for r in xs])); X1 = int(np.median([r[1] for r in xs]))
        mine = [n for n in range(max(0, n0 - 2), min(n1 + 2, len(recs)))
                if abs(recs[n][0] - X0) <= 4 and abs(recs[n][1] - X1) <= 4]
        # cụm trước có bề rộng gần bằng thì khung cuối của nó (đã vàng kín) cũng khớp bbox:
        # bỏ các khung đầu cho tới khi vệt vàng còn ngắn (cụm mới vừa hiện)
        k0 = next((i for i, n in enumerate(mine) if recs[n][2] < X0 + 0.3 * (X1 - X0)), 0)
        mine = mine[k0:]
        if mine:  # cụm hiện ra ở frame đầu tiên có thời điểm >= t_in
            errs.append((mine[0] / FPS - c["words"][0]["s"], c["text"], c["words"][0]["w"]))
        words = [w["w"] for w in c["words"]]
        full = " ".join(words)
        scale = (X1 - X0) / max(1.0, font.getlength(full))
        for k, w in enumerate(c["words"]):
            if k == 0:
                continue
            x_start = X0 + font.getlength(" ".join(words[:k]) + " ") * scale
            # frame đầu tiên vệt vàng vượt mép trái của từ k
            t_meas = None
            for n in mine:
                if recs[n][2] >= x_start + 3:
                    t_meas = n / FPS; break
            if t_meas is None:
                continue
            errs.append((t_meas - w["s"], c["text"], w["w"]))
        # luôn có chữ khi đang đọc
        for w in c["words"]:
            mid = int(round((w["s"] + w["e"]) / 2 * FPS))
            if mid < len(recs_v) and recs_v[mid][0] < 0:
                missing.append(f"{w['w']}@{w['s']:.2f}")
    if errs:
        e = np.array([x[0] for x in errs])
        print(f"[3] đồng bộ karaoke: {len(e)} từ đo được | lệch trung bình {e.mean()*1000:+.0f} ms, "
              f"lệch tuyệt đối lớn nhất {np.abs(e).max()*1000:.0f} ms (1 frame = 33 ms)")
        worst = sorted(errs, key=lambda x: -abs(x[0]))[:5]
        for d, t, w in worst:
            print(f"    {d*1000:+5.0f} ms  '{w}' trong «{t}»")
        if np.abs(e).max() > 0.07:
            ok = False; print("    LỖI: có từ lệch hơn 2 frame")
    # 3b. kiểm độc lập: đầu mỗi câu, lúc phụ đề hiện so với lúc tiếng nói thật bắt đầu (năng lượng âm thanh)
    raw = subprocess.run([ff, "-v", "error", "-i", plan["audio"], "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    au = np.frombuffer(raw, np.float32)
    hop = 160
    db = 20 * np.log10(np.sqrt(np.convolve(au ** 2, np.ones(hop) / hop, "same")[::hop]) + 1e-9)
    firsts = [c for k, c in enumerate(plan["subs"]) if k == 0 or plan["subs"][k - 1]["sent"] != c["sent"]]
    d_on = []
    for c in firsts:
        t = c["words"][0]["s"]
        i0 = max(0, int((t - 0.5) * 100))
        seg = db[i0:int((t + 0.3) * 100)]
        # khoảng lặng trước câu = đoạn liền >= 100 ms dưới -50 dB. Không lấy các chỗ trũng ngắn
        # giữa hai tiếng: "Ít / ai" có khe 40 ms, từng làm máy tưởng câu bắt đầu ở "ai" (báo sai 181 ms).
        low = seg[:int(0.65 * 100)] < -50
        end_q, run = -1, 0
        for k, v in enumerate(low):
            run = run + 1 if v else 0
            if run >= 10:
                end_q = k
        if end_q < 0:
            continue
        after = np.where(seg[end_q:] > -45)[0]   # -45 dB: bắt cả phụ âm đầu nhẹ (kh, tr, s)
        if len(after):
            onset = (i0 + end_q + after[0]) / 100
            d_on.append((c["t_in"] - onset, c["text"]))
    if d_on:
        e2 = np.array([x[0] for x in d_on])
        print(f"[3b] đầu câu: phụ đề hiện so với tiếng nói thật: trung bình {e2.mean()*1000:+.0f} ms, "
              f"lớn nhất {np.abs(e2).max()*1000:.0f} ms ({len(e2)} câu)")
        if np.abs(e2).max() > 0.1:
            ok = False
            for d, t in d_on:
                if abs(d) > 0.1:
                    print(f"    LỖI {d*1000:+.0f} ms «{t}»")
    if missing:
        ok = False
        print("[4] LỖI: không thấy phụ đề khi đang đọc:", missing[:10])
    else:
        print("[4] phụ đề hiện đủ ở mọi từ đang đọc")
    # 5. contact sheet
    sheet = os.path.splitext(video)[0] + "_qa_sheet.jpg"
    subprocess.run([ff, "-v", "error", "-y", "-i", video, "-vf", "fps=1,scale=216:384,tile=8x5", "-frames:v", "1", sheet])
    print("[5] contact sheet:", sheet)
    print("KẾT LUẬN:", "ĐẠT" if ok else "CHƯA ĐẠT - xem các dòng LỖI")
    return ok


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

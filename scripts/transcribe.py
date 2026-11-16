"""Bước 1: nhận dạng giọng nói tiếng Việt từ MP3 (faster-whisper) -> bản nháp lời thoại.

    python transcribe.py voice.mp3 work/asr.json [large-v3-turbo]

In ra từng câu kèm mốc thời gian và ghi `work/asr.json` + `work/script_draft.txt`.
Bản nháp CHƯA dùng được ngay: phải sửa tên riêng / từ nhận sai rồi lưu thành
`work/script.txt`, sau đó chạy align.py để lấy mốc từng từ chính xác.
Mốc thời gian của Whisper lệch tới 0,4 s ở đầu câu và tên riêng, KHÔNG dùng cho karaoke.
"""
import sys, os, json, time
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
from faster_whisper import WhisperModel

audio, out = sys.argv[1], sys.argv[2]
model_name = sys.argv[3] if len(sys.argv) > 3 else "large-v3-turbo"
t = time.time()
m = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=max(2, (os.cpu_count() or 4) - 2))
segs, info = m.transcribe(audio, language="vi", word_timestamps=True, beam_size=5,
                          vad_filter=False, condition_on_previous_text=True)
words, lines = [], []
for s in segs:
    for w in s.words:
        words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)})
    lines.append(s.text.strip())
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}", flush=True)
low = [w for w in words if w["p"] < 0.6]
if low:
    print("Từ độ tin cậy thấp (soi kỹ):", ", ".join(f"{w['w']}@{w['s']:.2f}" for w in low))

# ---- Dò đoạn BỊ SÓT: Whisper có lúc bỏ qua nguyên 5-6 giây lời (đã gặp ở video Napoleon Hill).
# Tìm khoảng có tiếng nói (năng lượng > -40 dB) dài > 0.8 s mà không có từ nào, rồi bóc lại riêng.
import subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ffmpeg_bin
raw = subprocess.run([ffmpeg_bin(), "-v", "error", "-i", audio, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                     capture_output=True).stdout
au = np.frombuffer(raw, np.float32)
db = 20 * np.log10(np.sqrt(np.convolve(au ** 2, np.ones(160) / 160, "same")[::160]) + 1e-9)  # 10 ms/khung
speech = db > -40
covered = np.zeros_like(speech)
for w in words:
    covered[int(w["s"] * 100):int(w["e"] * 100) + 1] = True
covered = np.convolve(covered.astype(float), np.ones(61), "same") > 0   # nới 0,3 s mỗi bên
miss = speech & ~covered
gaps, i = [], 0
while i < len(miss):
    if miss[i]:
        j = i
        while j < len(miss) and (miss[j] or (j + 30 < len(miss) and miss[j:j + 30].any())):
            j += 1
        if (j - i) / 100 > 0.8:
            gaps.append((i / 100, j / 100))
        i = j
    else:
        i += 1
merged = []
for g in gaps:  # gộp các khoảng sót cách nhau < 1 s (chỉ là nhịp nghỉ giữa câu) thành một đoạn
    if merged and g[0] - merged[-1][1] < 1.0:
        merged[-1] = (merged[-1][0], g[1])
    else:
        merged.append(g)
gaps = merged
recovered = []
for g0, g1 in gaps:
    a, b = max(0, g0 - 1.0), g1 + 1.0
    clip = os.path.join(os.path.dirname(os.path.abspath(out)), f"gap_{a:.1f}.wav")
    subprocess.run([ffmpeg_bin(), "-v", "error", "-y", "-ss", str(a), "-to", str(b), "-i", audio, clip])
    segs2, _ = m.transcribe(clip, language="vi", beam_size=5, vad_filter=False, condition_on_previous_text=False)
    txt = " ".join(s.text.strip() for s in segs2)
    recovered.append({"from": a, "to": b, "text": txt})
    print(f"!! ĐOẠN BỊ SÓT {g0:.2f}-{g1:.2f}s (bóc lại {a:.1f}-{b:.1f}s): {txt}")
if gaps:
    print("!! Ghép các đoạn trên vào đúng chỗ trong script.txt (đoạn bóc lại có lề 1 s, sẽ trùng vài từ ở hai đầu).")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"model": model_name, "duration": info.duration, "segments": lines, "words": words,
               "missed": recovered}, f, ensure_ascii=False, indent=1)
draft = os.path.join(os.path.dirname(os.path.abspath(out)), "script_draft.txt")
with open(draft, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("xong %.0fs -> %s, %s" % (time.time() - t, out, draft))

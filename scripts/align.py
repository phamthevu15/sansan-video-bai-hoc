"""Căn chỉnh cưỡng bức (CTC forced alignment) lời thoại đã sửa với file âm thanh.

Dùng mô hình wav2vec2 tiếng Việt, chạy Viterbi trên ma trận xác suất CTC để lấy
mốc bắt đầu/kết thúc thật của từng từ (độ phân giải 20 ms).

    python align.py voice.mp3 script.txt words.json

script.txt là lời thoại ĐÃ SỬA (đúng tên riêng, đúng chính tả, có dấu câu). Kết quả in ra
hai danh sách cần rà: từ khớp yếu và chỗ khác giữa lời thoại với bản mô hình tự nghe.
"""
import sys, os, json, re, subprocess, unicodedata
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ffmpeg_bin

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
FF = ffmpeg_bin()
MODEL = "nguyenvulebinh/wav2vec2-base-vietnamese-250h"

def load_audio(path, sr=16000):
    b = subprocess.run([FF, "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32)

SPOKEN = re.compile(r"^(.*?)\{([^}]+)\}(.*)$")


def words_of(script):
    """Tách lời thoại thành danh sách từ (giữ dấu câu dính theo từ).

    Cú pháp hiển thị khác cách đọc: `5{năm}`, `1990{một_nghìn_chín_trăm_chín_mươi},`
    -> phụ đề hiện "5" / "1990," nhưng căn chỉnh theo âm đọc thật (gạch dưới = cách chữ).
    """
    return [w for w in re.split(r"\s+", script.strip()) if w]


def split_spoken(w):
    """Trả về (chữ hiển thị, [các âm tiết đọc])."""
    m = SPOKEN.match(w)
    if m:
        return m.group(1) + m.group(3), m.group(2).split("_")
    return w, [w]


def norm_token(w):
    w = unicodedata.normalize("NFC", w.lower())
    return re.sub(r"[^\w]", "", w)

def main(audio, script_path, out):
    import torch
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
    proc = Wav2Vec2Processor.from_pretrained(MODEL)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL).eval()
    vocab = proc.tokenizer.get_vocab()
    blank = proc.tokenizer.pad_token_id
    delim = vocab.get("|")

    wav = load_audio(audio)
    dur = len(wav) / 16000
    with torch.inference_mode():
        emis = []
        # audio ngắn (<= 90 s) chạy một lượt để không cắt ngang từ; dài hơn thì chia khúc 30 s
        step = len(wav) if len(wav) <= 16000 * 90 else 16000 * 30
        for s in range(0, len(wav), step):
            chunk = wav[s:s + step]
            iv = proc(chunk, sampling_rate=16000, return_tensors="pt").input_values
            lg = model(iv).logits[0]
            emis.append(torch.log_softmax(lg, -1).numpy())
        E = np.concatenate(emis, 0)
    T = E.shape[0]
    fr = dur / T

    script = open(script_path, encoding="utf-8").read()
    raw_words = words_of(script)
    disp = [split_spoken(w)[0] for w in raw_words]
    spoken = [split_spoken(w)[1] for w in raw_words]
    toks, owner = [], []
    for wi, parts in enumerate(spoken):
        for part in parts:
            chars = [c for c in norm_token(part) if c in vocab]
            if not chars:
                continue
            if toks and delim is not None:
                toks.append(delim); owner.append(-1)
            for c in chars:
                toks.append(vocab[c]); owner.append(wi)
    missing = [w for w, parts in zip(disp, spoken) if not [c for p in parts for c in norm_token(p) if c in vocab]]
    if missing:
        print("cảnh báo: từ không có ký tự trong bộ từ vựng:", missing)

    # Viterbi CTC: chuỗi mở rộng blank, t, blank, t, ..., blank
    S = 2 * len(toks) + 1
    ext = np.full(S, blank, np.int64); ext[1::2] = toks
    NEG = -1e9
    dp = np.full(S, NEG); dp[0] = E[0, ext[0]]; dp[1] = E[0, ext[1]]
    bp = np.zeros((T, S), np.int8)
    can_skip = np.zeros(S, bool)
    can_skip[3::2] = ext[3::2] != ext[1:-2:2]
    for t in range(1, T):
        stay = dp
        prev1 = np.concatenate([[NEG], dp[:-1]])
        prev2 = np.concatenate([[NEG, NEG], dp[:-2]])
        prev2 = np.where(can_skip, prev2, NEG)
        cand = np.stack([stay, prev1, prev2])
        arg = cand.argmax(0)
        dp = cand[arg, np.arange(S)] + E[t, ext]
        bp[t] = arg
    s = S - 1 if dp[S - 1] > dp[S - 2] else S - 2
    path = np.zeros(T, np.int64)
    for t in range(T - 1, -1, -1):
        path[t] = s
        s -= int(bp[t, s])
    # gom khung theo từ
    starts, ends = {}, {}
    for t in range(T):
        st = path[t]
        if st % 2 == 1:
            wi = owner[st // 2]
            if wi >= 0:
                starts.setdefault(wi, t)
                ends[wi] = t
    words = []
    for wi, w in enumerate(disp):
        if wi in starts:
            words.append({"w": w, "s": round(starts[wi] * fr, 3), "e": round((ends[wi] + 1) * fr, 3)})
        else:
            words.append({"w": w, "s": None, "e": None})
    # nội suy cho từ thiếu mốc
    for i, x in enumerate(words):
        if x["s"] is None:
            p = next((words[j]["e"] for j in range(i - 1, -1, -1) if words[j]["e"] is not None), 0.0)
            n = next((words[j]["s"] for j in range(i + 1, len(words)) if words[j]["s"] is not None), dur)
            x["s"], x["e"] = round(p, 3), round(n, 3)
    # ---- Kiểm tra 1: điểm khớp từng từ (log-prob token đúng so với token mạnh nhất ở cùng khung)
    best = E.max(1)
    wscore = {}
    for t in range(T):
        st = path[t]
        if st % 2 == 1:
            wi = owner[st // 2]
            if wi >= 0:
                wscore.setdefault(wi, []).append(E[t, ext[st]] - best[t])
    for wi, x in enumerate(words):
        sc = wscore.get(wi)
        x["score"] = round(float(np.mean(sc)), 2) if sc else None
    weak = [(x["w"], x["s"], x["score"]) for x in words if x["score"] is not None and x["score"] < -1.5]
    # ---- Kiểm tra 2: mô hình tự nghe (greedy CTC) rồi so với lời thoại
    inv = {v: k for k, v in vocab.items()}
    am = E.argmax(1)
    heard, prev = [], None
    for t in range(T):
        k = int(am[t])
        if k != prev and k != blank:
            heard.append(inv.get(k, ""))
        prev = k
    heard_words = [w for w in "".join(heard).replace("|", " ").split() if w]
    import difflib
    ref, ref_own = [], []
    for wi, parts in enumerate(spoken):
        for p in parts:
            ref.append(norm_token(p)); ref_own.append(wi)
    sm = difflib.SequenceMatcher(a=ref, b=heard_words, autojunk=False)
    diffs = []
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op != "equal":
            w0 = ref_own[a0] if a0 < len(ref_own) else None
            t0 = words[w0]["s"] if w0 is not None else dur
            diffs.append({"t": t0, "script": " ".join(ref[a0:a1]), "heard": " ".join(heard_words[b0:b1])})
    json.dump({"audio": audio, "duration": round(dur, 3), "frame": fr, "words": words,
               "check": {"weak_words": weak, "diff_vs_heard": diffs, "heard_text": " ".join(heard_words)}},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(words)} từ, thời lượng {dur:.2f}s -> {out}")
    print("== TỪ KHỚP YẾU (điểm < -1.5, cần nghe/rà lại):")
    for w, t0, sc in weak:
        print(f"   {t0:6.2f}s  {w}  ({sc})")
    print("== KHÁC BIỆT giữa lời thoại và bản mô hình tự nghe (lỗi chính tả ghi âm của mô hình là bình thường, chỉ soi tên riêng/từ lạ):")
    for d in diffs:
        print(f"   {d['t']:6.2f}s  script: {d['script']!r:40s} nghe: {d['heard']!r}")

if __name__ == "__main__":
    main(*sys.argv[1:4])

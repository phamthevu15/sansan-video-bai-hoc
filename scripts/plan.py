"""Bước 3: lập kế hoạch dựng từ words.json (đã căn chỉnh) + config.json -> plan.json

    python plan.py work/words.json work/config.json work/plan.json

- Hook = câu đầu tiên (câu trích dẫn). Hook kết thúc đúng lúc câu thứ hai bắt đầu.
- Mỗi câu sau hook = 1 ảnh; câu ngắn < shot_min gộp với câu kế; câu dài > shot_max
  tách ở ranh giới cụm phụ đề gần điểm chia đều nhất.
- Chuyển động: pan/zoom xen kẽ (pan trái -> zoom in -> pan phải -> zoom out ...),
  ảnh dọc không pan, shot cuối luôn zoom in.
- Phụ đề: tách cụm theo nghĩa (không cắt từ ghép, không cắt tên riêng), <= 6 chữ,
  <= 930 px, ẩn trong khoảng nghỉ giữa các câu.

Chạy lần đầu khi chưa có ảnh để xem danh sách shot và nội dung từng shot, rồi
điền `images` trong config (đúng số lượng) và chạy lại.
"""
import sys, os, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SPEC, FONT_BOLD, FONT_XBOLD, FUNCTION_WORDS, load_json, save_json, probe_duration, vn_upper
from PIL import ImageFont, Image

FPS = SPEC["FPS"]
SENT_END = re.compile(r"[.!?…]+[\"”»)]*$")
COMMA_END = re.compile(r"[,;:]+[\"”»)]*$")
CONJ = {"và", "nhưng", "mà", "hay", "hoặc", "thì", "để", "vì", "nếu", "khi", "rồi", "còn", "nên", "bởi"}
# ngắt TRƯỚC những từ này là tự nhiên (liên từ, giới từ mở cụm mới)
BREAK_BEFORE = CONJ | {"cho", "trong", "trên", "dưới", "với", "bằng", "đến", "tới", "từ", "trước", "sau",
                       "vẫn", "cũng", "như", "giữa", "ngoài", "qua", "tại"}
# không kết thúc cụm bằng những từ "kéo" từ phía sau (hư từ, loại từ, động từ cầu khiến)
BIND_FWD = FUNCTION_WORDS | {"lời", "dòng", "chiếc", "cái", "con", "sự", "việc", "cách", "khoản", "tự", "bất",
                             "khiến", "giúp", "hãy", "đừng", "chỉ", "luôn", "dần", "phải", "biết", "cùng",
                             "người", "bạn", "nó", "ta", "mình", "họ", "chúng", "thật", "vừa", "quá", "chưa", "đều", "cả",
                             "cứ", "vẫn", "còn", "thường"}
# không mở đầu cụm bằng những từ "dính" vào từ phía trước
# cặp từ hay bị pyvi bỏ sót khi tách từ ghép -> không bao giờ ngắt giữa
PAIRS = {"mọi người", "có lợi", "về nhà", "lúc khó", "lúc thuận", "lúc may", "tận gốc", "câu hỏi", "trực tuyến", "danh bạ", "bề mặt", "số đông", "quy mô", "khổng lồ", "cạnh tranh", "tham vọng", "chăm chỉ", "làm việc", "công việc", "bản thân", "gia tài", "kiếm sống", "năm tháng", "tự học", "dòng tiền", "lời hứa", "lời mời", "lời nhắc", "giữ lại", "ghi lại", "vừa phải",
         "tầm nhìn", "vỗ tay", "đặt cược", "sự thật", "đời thường", "ngày mai", "hôm nay", "thế giới", "tiếng vỗ",
         "chính mình", "khó tin", "ai cũng", "đem lại", "mang lại", "có thể", "trở thành", "trở nên", "tỷ phú", "khởi nghiệp", "thấp kém", "bảng báo",
         "thiêu chết", "đứng dậy", "phượng hoàng", "trọng trách", "thật lòng"}
BIND_BACK = {"của", "hơn", "nhất", "lắm", "quá", "nữa", "thôi", "lại", "ra", "được", "đó", "này", "ấy", "kia", "rồi",
             "xong", "hết", "mất", "nào", "thêm"}


def bare(w):
    return re.sub(r"[^\w\-]", "", w.lower())


def fr(t):
    return int(round(t * FPS))


# ---------------------------------------------------------------- tách từ ghép
def compound_links(words):
    """links[i] = True nếu KHÔNG được ngắt giữa words[i] và words[i+1] (cùng từ ghép / tên riêng)."""
    n = len(words)
    links = [False] * max(0, n - 1)
    try:
        from pyvi import ViTokenizer
        plain = [re.sub(r"[^\w\-]", "", w) or "x" for w in words]
        tok = ViTokenizer.tokenize(" ".join(plain)).split()
        i = 0
        for t in tok:
            parts = t.split("_")
            for k in range(len(parts) - 1):
                if i + k < len(links):
                    links[i + k] = True
            i += len(parts)
    except Exception as e:  # pyvi không có -> chỉ bảo vệ tên riêng
        print("cảnh báo: không dùng được pyvi:", e)
    # tên riêng: chuỗi từ viết hoa chữ cái đầu liên tiếp (vd Robert Kiyosaki, Lee Kun-hee)
    for i in range(n - 1):
        a, b = words[i], words[i + 1]
        if a[:1].isupper() and b[:1].isupper() and not SENT_END.search(a) and not COMMA_END.search(a):
            links[i] = True
    # không ngắt sau từ có dấu câu -> luôn cho phép ngắt
    for i in range(n - 1):
        if bare(words[i]) + " " + bare(words[i + 1]) in PAIRS:
            links[i] = True
    for i in range(n - 1):
        if SENT_END.search(words[i]) or COMMA_END.search(words[i]):
            links[i] = False
    return links


def pos_tags(words):
    """Từ loại (pyvi) cho từng từ: N danh, V động, A tính, E giới, C liên, R phụ, M số, L định lượng, P đại."""
    try:
        from pyvi import ViTokenizer, ViPosTagger
        plain = [re.sub(r"[^\w\-]", "", w) or "x" for w in words]
        toks, tags = ViPosTagger.postagging(ViTokenizer.tokenize(" ".join(plain)))
        out = []
        for t, g in zip(toks, tags):
            out += [g] * len(t.split("_"))
        return out[:len(words)] + ["X"] * max(0, len(words) - len(out))
    except Exception:
        return ["X"] * len(words)


def grammar_cost(a, b):
    """Phạt khi ngắt giữa từ loại a (cuối cụm) và b (đầu cụm sau)."""
    c = 0
    if a == "V" and b in ("N", "Np", "M", "L", "P", "Nc"):
        c += 8          # động từ | tân ngữ: "GIẢI QUYẾT / VẤN ĐỀ"
    if a == "V" and b == "V":
        c += 6          # "VỨT / BỎ"
    if a in ("L", "M", "Nc") and b in ("N", "Np", "A"):
        c += 9          # "MỌI / CƯỢC", "MỘT / SẢN PHẨM"
    if a in ("N", "Np") and b == "A":
        c += 6          # "CƯỢC / LỚN"
    if a in ("N", "Np") and b in ("N", "Np"):
        c += 3
    if a == "R":
        c += 5          # phụ từ kéo về sau: "ĐỀU / ĐÚNG", "CHƯA / CÓ"
    if a == "E":
        c += 8          # giới từ đứng cuối: "RÈN QUA / GIAN KHÓ"
    if b == "C":
        c -= 2
    return c


# ---------------------------------------------------------------- chia cụm phụ đề
_sub_font = None


def sub_width(text):
    global _sub_font
    if _sub_font is None:
        _sub_font = ImageFont.truetype(FONT_BOLD, SPEC["sub_font_size_px"])
    return _sub_font.getlength(vn_upper(text))


def chunk_sentence(ws):
    """ws: list từ (dict w,s,e) của MỘT câu. Trả về list (i, j) chỉ số cụm."""
    words = [x["w"] for x in ws]
    n = len(words)
    links = compound_links(words)
    tags = pos_tags(words)
    INF = 1e18

    def cost(i, j):
        m = j - i + 1
        text = " ".join(words[i:j + 1])
        if m > SPEC["sub_max_words"] + 1 or sub_width(text) > SPEC["sub_max_w"]:
            return INF
        c = 0.6 * (m - SPEC["sub_target_words"]) ** 2
        if m == SPEC["sub_max_words"] + 1:
            c += 3
        if m == 1 and n > 1:
            c += 10
        if m == 2 and n > 3:
            c += 3
        d = ws[j]["e"] - ws[i]["s"]
        if d > 1.6:
            c += (d - 1.6) * 12
        if d < 0.55 and n > m:
            c += 4
        last = bare(words[j])
        if j < n - 1:
            nxt = bare(words[j + 1])
            if COMMA_END.search(words[j]):
                c -= 4
            else:
                if last in BIND_FWD:
                    c += 9
                if nxt in BIND_BACK:
                    c += 9
                if nxt in BREAK_BEFORE:
                    c -= 1.5
                c += grammar_cost(tags[j], tags[j + 1])
        return c

    best = [INF] * (n + 1)
    prev = [-1] * (n + 1)
    best[0] = 0
    for j in range(1, n + 1):
        for i in range(max(0, j - SPEC["sub_max_words"] - 1), j):
            if i > 0 and links[i - 1]:
                continue  # không ngắt giữa từ ghép / tên riêng
            c = best[i] + cost(i, j - 1)
            if c < best[j]:
                best[j], prev[j] = c, i
    if best[n] >= INF:  # bất khả -> cắt tham lam theo số chữ
        return [(i, min(i + SPEC["sub_max_words"], n) - 1) for i in range(0, n, SPEC["sub_max_words"])]
    out, j = [], n
    while j > 0:
        i = prev[j]
        out.append((i, j - 1))
        j = i
    return out[::-1]


# ---------------------------------------------------------------- xếp dòng câu trích dẫn hook
HARD = 1e5      # cắt ngang từ ghép / tên riêng / cặp PAIRS: chỉ chấp nhận khi không còn cách nào
PRONOUNS = {"bạn", "nó", "ta", "mình", "họ", "tôi", "người"}
CAUSATIVE = {"giúp", "khiến", "cho", "để", "bắt", "làm", "bảo", "mời", "nhờ", "chúc", "cho phép", "buộc"}


def wrap_headline(text, size, max_w, lines_n, src=None):
    """Chia câu trích dẫn thành đúng lines_n dòng, ưu tiên ngắt theo cụm nghĩa.

    text: câu đã IN HOA để đo; src: cùng câu ở chữ thường gốc (để tách từ ghép / tên riêng đúng).
    Tách từ trên chữ IN HOA là sai: luật tên riêng thấy mọi chữ viết hoa nên coi cả câu là tên,
    chặn hết mọi chỗ ngắt như nhau -> luật chống cắt từ ghép mất tác dụng ("CHĂM / CHỈ").

    Chi phí: chỗ ngắt sai ngữ pháp (động từ | tân ngữ, danh từ | tính từ, hư từ cuối dòng…) nặng hơn
    việc dòng hơi hụt chữ; ngắt sau dấu phẩy hoặc trước liên từ được thưởng; dòng cuối được phép
    ngắn (như chữ tự xuống dòng) nhưng không để 1 chữ mồ côi. Ghi số chỗ cắt từ ghép vào last_bad."""
    font = ImageFont.truetype(FONT_XBOLD, size)
    words = text.split()
    n = len(words)
    base = (src or text).split()
    if len(base) != n:
        base = [w.lower() for w in words]
    base = [w.strip("“”\"") for w in base]
    links = compound_links(base)
    tags = pos_tags([w.lower() for w in base])
    W = lambda i, j: font.getlength(" ".join(words[i:j + 1]))

    def brk(j):                       # chi phí ngắt giữa words[j-1] | words[j]
        c, hard = 0.0, 0
        a, b = bare(words[j - 1]), bare(words[j])
        if links[j - 1] or a + " " + b in PAIRS:
            c, hard = c + HARD, 1
        if COMMA_END.search(words[j - 1]):
            c -= 400
        else:
            # đại từ cuối dòng chỉ xấu khi nó là chủ ngữ của vế sau ("BIẾT MÌNH / SẼ CHẾT");
            # làm tân ngữ sau giới từ thì được ("PHẠM VÀO NÓ / CHẲNG SƯỚNG").
            # Tiểu từ đứng sau động từ (lại, ra, được, hơn…) kết dòng là tự nhiên ("ĐEM LẠI / LÀ").
            # đại từ mở một vế mới (chủ ngữ của động từ ngay sau) -> ngắt TRƯỚC nó là ranh giới vế câu:
            # "MUỐN BIẾT / MÌNH SẼ CHẾT Ở ĐÂU", "KHÓ TIN / NGƯỜI LUÔN SỢ…"
            # Chỉ áp cho động từ nhận thức/nói (biết, tin, thấy…); động từ sai khiến thì đại từ là
            # tân ngữ, không ngắt được ("GIÚP / BẠN BẮT ĐẦU", "CHÚC CÁC / BẠN").
            subj_next = (b in PRONOUNS and j + 1 < n and tags[j + 1] in ("R", "V", "A")
                         and tags[j - 1] == "V" and a not in CAUSATIVE)
            if a in PRONOUNS:
                if tags[j] in ("R", "V", "A") and not (j >= 2 and tags[j - 2] == "E"):
                    c += 300
            elif a == "là":
                c += 60               # "BẬN RỘN CŨNG LÀ / MỘT KIỂU…" đọc vẫn trôi, chỉ kém ngắt trước "là"
            elif a in BIND_FWD and (a not in BIND_BACK or a == "của") and not subj_next:
                c += 300
            if subj_next:
                c -= 40
            elif a != "là" and b != "là" and b not in BREAK_BEFORE:
                # "là" nối chủ ngữ với vị ngữ: ngắt quanh nó vẫn tự nhiên. Trước liên từ/giới từ cũng
                # vậy, kể cả khi pyvi gán nhầm từ loại (nó hay gán "khi" là danh từ).
                # Tiểu từ sau động từ (lại, ra, thêm…) thì xét theo động từ đứng trước nó:
                # "RÈN RA / TÍNH CÁCH" vẫn là động từ | tân ngữ.
                ta = tags[j - 2] if a in BIND_BACK and a != "của" and j >= 2 else tags[j - 1]
                c += 40 * max(0, grammar_cost(ta, tags[j]))
            if tags[j - 1] == "R" and a not in BIND_BACK:
                c += 120              # phụ từ (cũng, đã, chẳng, chỉ…) treo cuối dòng rất khó đọc;
                                      # tiểu từ sau động từ (lại, ra, thêm, hơn…) thì kết dòng được
            if b in BREAK_BEFORE or b == "là":
                c -= 60
        if not COMMA_END.search(words[j - 1]) and (
                b in BIND_BACK or (b == "thật" and (j + 1 >= n or bare(words[j + 1]) != "sự"))):
            c += 400                  # sau dấu phẩy thì "rồi", "còn"… là liên từ mở vế mới
        return c, hard

    INF = 1e18
    dp = [[INF] * (n + 1) for _ in range(lines_n + 1)]
    bk = [[-1] * (n + 1) for _ in range(lines_n + 1)]
    hb = [[0] * (n + 1) for _ in range(lines_n + 1)]
    dp[0][0] = 0
    for k in range(1, lines_n + 1):
        for j in range(1, n + 1):
            for i in range(0, j):
                if dp[k - 1][i] >= INF:
                    continue
                w = W(i, j - 1)
                if w > max_w:
                    continue
                h = 0
                if j < n:
                    c = ((max_w - w) / 40.0) ** 2
                    bc, h = brk(j)
                    c += bc
                else:
                    c = 400.0 if j - i == 1 and n > 1 else (100.0 if j - i == 2 and n >= 6 else 0.0)
                if dp[k - 1][i] + c < dp[k][j]:
                    dp[k][j], bk[k][j], hb[k][j] = dp[k - 1][i] + c, i, hb[k - 1][i] + h
    if dp[lines_n][n] >= INF:
        return None
    res, j = [], n
    for k in range(lines_n, 0, -1):
        i = bk[k][j]
        res.append(" ".join(words[i:j]))
        j = i
    wrap_headline.last_cost = dp[lines_n][n]
    wrap_headline.last_bad = hb[lines_n][n]
    return res[::-1]


def make_headline(text):
    t = text.strip()
    t = re.sub(r"[.!…]+$", "", t)                 # bỏ dấu chấm cuối (không để dấu chấm trước ngoặc kép đóng)
    src = t
    t = "“" + vn_upper(t) + "”"
    # Xuống dòng TỰ NHIÊN như chữ tự xuống dòng (người dùng 02-10: "đừng cố làm 3 dòng, được mấy
    # dòng thì mấy"; 03-10: "đang bị xuống dòng dù ở trên chưa hết chỗ"):
    # lấp đầy từng dòng tới 944 px ở cỡ 50 px; chỉ xuống dòng khi chữ kế tiếp không vừa nữa.
    # Ngoại lệ duy nhất: không tách đôi từ ghép / tên riêng / cặp PAIRS — cả cụm cùng xuống dòng.
    # (wrap_headline theo cụm nghĩa vẫn giữ lại để tham khảo, nhưng KHÔNG dùng: nó cố ý để dòng
    # trên hụt chữ, đúng cái người dùng chê.)
    size = SPEC["head_size"]
    font = ImageFont.truetype(FONT_XBOLD, size)
    words = t.split()
    base = src.split()
    if len(base) != len(words):
        base = [w.lower() for w in words]
    base = [w.strip("“”\"") for w in base]
    links = compound_links(base)
    # Không để dòng kết thúc bằng liên từ treo ("TRỪ VỢ VÀ / CON," -> "TRỪ VỢ / VÀ CON,"):
    # liên từ đi xuống cùng chữ sau nó. 19-10: thêm giới từ ở/tại/của/với ("THẮNG Ở / VẠCH XUẤT PHÁT"). Thử trên 40 hook bộ 05-10: chỉ đổi 4 hook, cả 4 ngắt đúng dấu phẩy.
    for i in range(len(links)):
        if bare(base[i]) in {"và", "hay", "hoặc", "nhưng", "mà", "ở", "tại", "của", "với"} and not COMMA_END.search(base[i]) \
                and not SENT_END.search(base[i]):
            links[i] = True
    units, cur = [], [words[0]]
    for i in range(1, len(words)):
        if links[i - 1] or bare(words[i - 1]) + " " + bare(words[i]) in PAIRS:
            cur.append(words[i])
        else:
            units.append(" ".join(cur))
            cur = [words[i]]
    units.append(" ".join(cur))
    # Dấu câu cuối dòng (” , . : ; ! ?) được "treo" ra lề phải: chữ đo tới 960 px, cả dấu tới 990 px
    # (vẫn cách mép khung >= 22 px). Người dùng 09-10 chê "LÀM SAO ĐỂ / MUA ĐƯỢC”" là xuống dòng vô
    # duyên khi trên còn chỗ: "MUA ĐƯỢC”" rộng 979 px, chỉ lố 960 vì dấu ngoặc đóng.
    # Thử trên 40 hook bộ 05-10: chỉ đổi 4 hook (07, 13, 29, 32), cả 4 hết chữ mồ côi ở dòng cuối.
    # (Bản 09-10 sáng kéo chữ trước xuống cùng chữ mồ côi -> lại để dòng trên hụt: đã bỏ.)
    def fits(s):
        return font.getlength(re.sub(r"[”,.:;!?]+$", "", s)) <= SPEC["head_max_w"] \
            and font.getlength(s) <= SPEC["head_max_w"] + 30
    lines = []
    for u in units:
        if lines and fits(lines[-1] + " " + u):
            lines[-1] += " " + u
        else:
            lines.append(u)
    return {"lines": lines, "size": size}


# ---------------------------------------------------------------- main
def main(words_p, cfg_p, out_p):
    wd = load_json(words_p)
    cfg = load_json(cfg_p)
    words = wd["words"]
    audio = cfg.get("audio") or wd["audio"]
    dur = probe_duration(audio)
    lead, tail = SPEC["sub_lead"], SPEC["sub_tail"]

    # ---- câu
    sents, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if SENT_END.search(w["w"]):
            sents.append(cur); cur = []
    if cur:
        sents.append(cur)
    hook_n = int(cfg.get("hook_sentences", 1))
    hook_idx = [i for s in sents[:hook_n] for i in s]
    body_sents = sents[hook_n:]
    if not body_sents:
        raise SystemExit("MP3 chỉ có một câu -> không có phần thân.")
    hook_end = words[body_sents[0][0]]["s"] - lead
    n_total = math.ceil(dur * FPS)

    # ---- phụ đề (chỉ phần thân)
    chunks = []
    manual = cfg.get("sub_chunks")
    if manual:
        # cụm do người/Claude chốt tay: phải khớp đúng thứ tự từ của lời thoại
        flat = [(si, i) for si, s in enumerate(body_sents) for i in s]
        p = 0
        for line in manual:
            toks = line.split()
            got = flat[p:p + len(toks)]
            if len(got) < len(toks) or [bare(words[i]["w"]) for _, i in got] != [bare(t) for t in toks]:
                have = " ".join(words[i]["w"] for _, i in flat[p:p + len(toks) + 2])
                raise SystemExit(f"sub_chunks lệch lời thoại ở cụm {line!r}; lời thoại tại đó: {have!r}")
            if len({si for si, _ in got}) > 1:
                raise SystemExit(f"cụm {line!r} vắt qua hai câu - tách ở dấu chấm.")
            chunks.append({"sent": got[0][0], "idx": [i for _, i in got]})
            p += len(toks)
        if p != len(flat):
            raise SystemExit("sub_chunks thiếu từ ở cuối: " + " ".join(words[i]["w"] for _, i in flat[p:]))
    else:
        for si, s in enumerate(body_sents):
            ws = [words[i] for i in s]
            for (a, b) in chunk_sentence(ws):
                chunks.append({"sent": si, "idx": s[a:b + 1]})
    for k, c in enumerate(chunks):
        ws = [words[i] for i in c["idx"]]
        # libass chỉ hiện chữ ở frame có thời điểm >= t_in -> làm tròn t_in về frame GẦN NHẤT (lệch ±17 ms)
        # thay vì để luôn trễ tới 33 ms; cụm đầu tiên hiện ngay frame đầu sau hook
        t_in = max(ws[0]["s"] - lead, hook_end)
        hook_cut = round(hook_end * FPS) / FPS
        t_in = max(round(t_in * FPS) / FPS, hook_cut) - 0.001
        c["t_in"] = round(max(t_in, hook_cut - 0.001), 3)
        c["text"] = " ".join(w["w"] for w in ws)
        c["words"] = [{"w": vn_upper(w["w"]), "s": round(w["s"] - lead, 3), "e": round(w["e"], 3)} for w in ws]
    for k, c in enumerate(chunks):
        nxt = chunks[k + 1] if k + 1 < len(chunks) else None
        end_last = c["words"][-1]["e"]
        if nxt is not None and nxt["sent"] == c["sent"]:
            c["t_out"] = nxt["t_in"]
        else:
            t_out = end_last + tail
            if nxt is not None:
                t_out = min(t_out, nxt["t_in"])
            c["t_out"] = round(min(t_out, dur), 3)
        c["width"] = round(sub_width(c["text"]))
        c["n_words"] = len(c["words"])
        del c["idx"]

    # ---- shot: mỗi câu một ảnh, gộp câu ngắn, tách câu dài
    starts = [max(words[s[0]]["s"] - lead, hook_end) for s in body_sents]
    starts[0] = hook_end
    segs = []
    for k, t0 in enumerate(starts):
        t1 = starts[k + 1] if k + 1 < len(starts) else n_total / FPS
        segs.append([t0, t1, [k]])
    merged = []
    for sg in segs:
        if merged and (sg[1] - sg[0] < SPEC["shot_min"] or merged[-1][1] - merged[-1][0] < SPEC["shot_min"]):
            merged[-1][1] = sg[1]; merged[-1][2] += sg[2]
        else:
            merged.append(sg)
    shots = []
    for t0, t1, ss in merged:
        d = t1 - t0
        m = max(1, math.ceil(d / SPEC["shot_max"] - 1e-6))
        after_comma = {c["t_in"] for k, c in enumerate(chunks)
                       if k > 0 and COMMA_END.search(chunks[k - 1]["text"]) and chunks[k - 1]["sent"] == c["sent"]}
        # dung sai 0,05 s: điểm cắt cách đầu shot đúng 1,90 s từng bị loại vì sai số dấu phẩy động,
        # để lại shot 5,4 s không chia được (Bill Gates 07-10)
        cands = sorted({c["t_in"] for c in chunks
                        if t0 + SPEC["shot_min"] - 0.05 <= c["t_in"] <= t1 - SPEC["shot_min"] + 0.05})
        cuts = []
        for q in range(1, m):
            ideal = t0 + d * q / m
            if cands:
                # ưu tiên cắt ảnh ngay sau dấu phẩy (chỗ ngắt ý), miễn không lệch quá 1 s khỏi điểm chia đều
                best = min(cands, key=lambda x: abs(x - ideal) - (1.0 if x in after_comma else 0))
                if all(abs(best - c0) >= SPEC["shot_min"] for c0 in cuts):
                    cuts.append(best)
        bounds = [t0] + sorted(cuts) + [t1]
        for a, b in zip(bounds[:-1], bounds[1:]):
            shots.append({"t0": a, "t1": b})
    # cắt đúng frame
    for s in shots:
        s["n0"], s["n1"] = fr(s["t0"]), fr(s["t1"])
    shots[-1]["n1"] = n_total
    for s in shots:
        s["t0"], s["t1"] = round(s["n0"] / FPS, 3), round(s["n1"] / FPS, 3)
        spoken = [c["text"] for c in chunks if s["t0"] - 0.05 <= c["t_in"] < s["t1"] - 0.05]
        s["spoken"] = " ".join(spoken)

    # ---- ảnh + chuyển động
    imgs = cfg.get("images") or []
    base = os.path.dirname(os.path.abspath(cfg_p))
    def ar_of(p):
        try:
            with Image.open(p if os.path.isabs(p) else os.path.join(base, p)) as im:
                return im.width / im.height
        except Exception:
            return None
    pan_dir, zoom_dir = "left", "in"
    want_pan = True
    ks = SPEC["zoom_k"]
    for i, s in enumerate(shots):
        img = imgs[i] if i < len(imgs) else None
        s["image"] = img
        ar = ar_of(img) if img else None
        s["ar"] = round(ar, 3) if ar else None
        override = (cfg.get("motions") or {}).get(str(i))
        last = i == len(shots) - 1
        if override:
            mo = override
        elif last:
            mo = "zoom_in"
        elif want_pan and (ar is None or ar >= 1.05):
            mo = "pan_" + pan_dir
            pan_dir = "right" if pan_dir == "left" else "left"
        else:
            mo = "zoom_" + zoom_dir
            zoom_dir = "out" if zoom_dir == "in" else "in"
        if i > 0 and mo == shots[i - 1]["motion"] and mo.startswith("zoom") and not last:
            mo = "zoom_out" if mo == "zoom_in" else "zoom_in"
            zoom_dir = "out" if mo == "zoom_in" else "in"
        # xen kẽ theo loại chuyển động THỰC TẾ: lượt pan bị ảnh dọc chặn thì giữ cho ảnh ngang kế tiếp
        # (trước đây đảo theo số thứ tự -> video toàn ảnh dọc/ngang xen nhau ra 100% zoom)
        want_pan = not mo.startswith("pan")
        s["motion"] = mo
        if mo.startswith("zoom"):
            n_zoom = sum(1 for x in shots[:i] if x.get("motion", "").startswith("zoom"))
            s["k"] = ks[n_zoom % 2]   # zoom 1.10 / 1.11 luân phiên như bản gốc
        else:
            s["k"] = None
        if last:
            s["k"] = ks[1]
    # shot cuối luôn zoom in -> shot áp chót mà cũng zoom in thì đổi thành zoom out cho khỏi lặp
    if len(shots) >= 2 and shots[-2]["motion"] == "zoom_in" and shots[-1]["motion"] == "zoom_in" \
            and not (cfg.get("motions") or {}).get(str(len(shots) - 2)):
        shots[-2]["motion"] = "zoom_out"

    # ---- hook
    head_src = cfg.get("headline") or " ".join(words[i]["w"] for i in hook_idx)
    if cfg.get("headline_lines"):
        head = {"lines": [vn_upper(x) for x in cfg["headline_lines"]], "size": cfg.get("headline_size", SPEC["head_size"])}
    else:
        head = make_headline(head_src)
    label = cfg.get("label") or ("BÀI HỌC TỪ " + vn_upper(cfg["person"]) + ":")
    plan = {
        "audio": audio, "duration": round(dur, 3), "n_frames": n_total, "fps": FPS,
        "hook": {"t0": 0.0, "t1": round(fr(hook_end) / FPS, 3), "n1": fr(hook_end),
                 "image": cfg.get("hook_image"), "face_y": cfg.get("hook_face_y", 0.33),
                 "label": vn_upper(label), "headline": head},
        "shots": shots, "subs": chunks,
    }
    plan["shots"][0]["n0"] = plan["hook"]["n1"]
    plan["shots"][0]["t0"] = plan["hook"]["t1"]
    save_json(plan, out_p)

    # ---- báo cáo
    print(f"Âm thanh {dur:.2f}s -> {n_total} frame. Hook 0.00-{plan['hook']['t1']:.2f}s")
    print("  Nhãn :", plan["hook"]["label"])
    print("  Câu trích dẫn (%dpx):" % head["size"])
    for l in head["lines"]:
        print("     ", l)
    print(f"\nCẦN {len(shots)} ẢNH THÂN + 1 ảnh hook. Danh sách shot:")
    for i, s in enumerate(shots):
        print(f"  [{i:02d}] {s['t0']:6.2f}-{s['t1']:6.2f} ({s['t1']-s['t0']:.2f}s) {s['motion']:9s} {s['k'] or '':<5} "
              f"ảnh={s['image'] or '-'} ar={s['ar'] or '-'}\n        \"{s['spoken']}\"")
    print(f"\nPhụ đề: {len(chunks)} cụm")
    for c in chunks:
        warn = []
        if c["width"] > SPEC["sub_max_w"]:
            warn.append("QUÁ RỘNG")
        if c["t_out"] - c["t_in"] < 0.35:
            warn.append("QUÁ NGẮN")
        print(f"  {c['t_in']:6.2f}-{c['t_out']:6.2f} ({c['t_out']-c['t_in']:.2f}s, {c['n_words']} chữ, {c['width']}px) "
              f"{vn_upper(c['text'])} {' '.join(warn)}")


if __name__ == "__main__":
    main(*sys.argv[1:4])

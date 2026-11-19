---
name: sansan-video-bai-hoc
description: Dựng video dọc 9:16 series "Bài học từ …" của SanSan Academy từ MỘT file MP3 giọng đọc — clone đúng phong cách 4 video mẫu (Lee Kun-hee, Akio Morita, Charlie Munger, Naval Ravikant) - hook nền đỏ ribbon TƯ DUY/SANSAN ACADEMY + câu trích dẫn, ảnh giữa trên nền mờ, pan/zoom tuyến tính, phụ đề karaoke IN HOA trắng→vàng khớp từng từ. Tự bóc lời, sửa tên riêng, căn chỉnh từng từ, tìm ảnh, lập kế hoạch cắt, render MP4 và tự nghiệm thu. Dùng khi người dùng gửi MP3 và nói "edit video", "dựng video", "làm video như mẫu", "làm tương tự", "video bài học từ …", "video Sansan Academy", "làm sub karaoke", hoặc gửi MP3 kèm tên nhân vật. Kể cả khi chỉ đưa file MP3 mà không nói gì thêm, vẫn dùng skill này.
---

# SanSan Academy — video "Bài học từ …"

Người dùng chỉ đưa **MP3 giọng đọc**. Mọi việc còn lại (bóc lời, sửa tên riêng, phụ đề, tìm
ảnh, chuyển động, render, kiểm tra) là của Claude. Mục tiêu: ra video **y hệt phong cách mẫu**,
và phụ đề **khớp giọng từng từ, không nhanh không chậm**.

Thông số đầy đủ, kèm cách đo và khác biệt giữa các phiên bản: `references/thong-so-thiet-ke.md`.
Cách tìm ảnh: `references/chon-anh.md`. Mọi con số dùng trong code nằm ở `scripts/common.py` (`SPEC`).

## Thương hiệu (17-10-2026)
Kênh SanSan Academy bị gậy, video từ nay đăng kênh **SEE THE LIGHT**. Ribbon hook đã đổi chữ trong
`assets/hook_template_stl.png` (dựng bằng `scripts/make_brand_template.py`, font Be Vietnam Pro SemiBold,
đo lại chữ cũ để khớp màu, chiều cao, độ giãn). Tên file xuất: `See_The_Light_<Nhan_Vat>_<Chu_De>.mp4`.
Khuôn cũ: `assets/hook_template_sansan.png`.

## Môi trường (máy Windows của người dùng)

- Python: `C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe` (gọi trong Bash là
  `~/AppData/Local/Programs/Python/Python312/python.exe`). Luôn đặt `PYTHONIOENCODING=utf-8`.
- Gói: `numpy opencv-python-headless pillow faster-whisper torch(cpu) transformers pyvi`.
  Thiếu thì cài: `pip install ...` (torch: `--index-url https://download.pytorch.org/whl/cpu`).
- ffmpeg: `winget install Gyan.FFmpeg`. Script tự tìm trong WinGet nếu PATH chưa có.
- Đường dẫn scratchpad quá dài với Python (giới hạn 260 ký tự). Làm việc trong thư mục ngắn,
  ví dụ `D:\ssan\<ten-video>\` hoặc thư mục người dùng chọn.
  **KHÔNG làm việc trong `%TEMP%`.** Ngày 21-10-2026 Windows tự dọn mất `%TEMP%\ssan\kb1210`,
  `%TEMP%\claude\vbee` và cả ffmpeg trong WinGet. Các file bị xoá thẳng, không qua Thùng rác.
  Khi gặp lỗi "Không tìm thấy ffmpeg" mà winget vẫn báo đã cài, chạy
  `winget install --id Gyan.FFmpeg -e --force`.
- RAM máy ít (~8 GB). Không chạy hai tác vụ nặng (Whisper, render) cùng lúc.
- Kiểm nhanh mọi thứ: `python scripts/check_env.py` → phải in "SẴN SÀNG".
- Người dùng gửi video mẫu mới và muốn cập nhật phong cách: đo bằng `scripts/do_mau.py`, rồi
  sửa `SPEC` trong `common.py` và bảng trong `references/thong-so-thiet-ke.md`.

## Quy trình (làm đủ, đúng thứ tự)

Đặt `S=~/.claude/skills/sansan-video-bai-hoc/scripts`, thư mục làm việc `work/` chứa `voice.mp3`.

### 1. Bóc lời thô
`python $S/transcribe.py work/voice.mp3 work/asr.json` → `work/script_draft.txt`.
Mốc thời gian của Whisper **không dùng** cho phụ đề: đầu câu và tên riêng có thể lệch tới 0,4 s.
Whisper có lúc **bỏ sót nguyên đoạn vài giây**. Script tự dò chỗ có tiếng mà không có chữ, bóc lại
và in dòng `!! ĐOẠN BỊ SÓT …`. Thấy dòng này thì ghép đoạn đó vào `script.txt`. Bước align sau đó
sẽ xác nhận: bản mô hình tự nghe phải khớp cả đoạn đó.

### 2. Sửa lời thoại → `work/script.txt`
- **Có kịch bản gốc thì lấy làm chuẩn.** MP3 trong `Downloads\40-kich-ban-new\` (tên dạng
  `NN - Tiêu đề.mp3`) được tạo từ Vbee. Từ 05/10/2026, thư mục này chứa bộ 40 doanh nhân quen
  với người Việt. Chữ gốc nằm ở `%TEMP%\claude\vbee\nhom-a-moi-0510.json`: phần tử có `n` = số NN,
  `tieu_de` khớp tên file, `tts` là lời đọc (bỏ thẻ `<break …/>`), `tac_gia` là nhân vật. Nếu thư
  mục tạm đã mất thì lấy JSON trong `<script id="data">` của
  `Downloads\40-kich-ban-doanh-nhan-noi-tieng-05-10.html`. Bộ cũ (`nhom-a.json`, file
  `120-kich-ban-viet-lai-tu-hook-ban-loc-02-10.html`) chỉ khớp các video dựng trước 05/10.
  **Bộ 2 (12/10/2026):** MP3 trong `Downloads\40-kich-ban-moi-12-10\`, chữ gốc ở
  `D:\ssan\kb1210\bo40_1210.json` (trường `body`, `tts`, `note`). Bản này khôi phục ngày 21-10
  từ `<script id="data">` của `Downloads\40-kich-ban-moi-12-10.html`, vì bản trong %TEMP% đã mất.
  **Bộ 3 (23/10/2026, 27 bài):** MP3 trong `Downloads\27-kich-ban-moi-23-10\`, chữ gốc ở
  `D:\ssan\kb2310\bo27_2310.json` (trường `h`, `body`, `tts`, `nguon`, `url`, `doi`). Số trong `body`
  viết bằng chữ: khi làm `script.txt` thì đổi sang dạng `1999{một_nghìn_chín_trăm_chín_mươi_chín}`.
  Lấy đúng bộ theo thư mục chứa MP3: cùng số NN nhưng các bộ là các kịch bản khác nhau.
  Tên riêng trong `tts` viết theo phiên âm Vbee ("Tim Phe rít"): đổi về tên gốc và dùng phiên âm
  làm phần đọc, vd `Ferriss{phe_rít}`. Vẫn chạy align: kết quả nghe phải khớp, vì giọng đọc mới là
  thứ phụ đề bám theo.
- Soát **từng tên riêng**. Whisper phiên âm bừa tên nước ngoài (vd "Zobuki Iosaki" thực ra là
  "Robert Kiyosaki"). Đối chiếu với tên file MP3, câu trích dẫn nổi tiếng của nhân vật và ngữ cảnh.
  Viết tên đúng chính tả gốc (Lee Kun-hee, Akio Morita, Robert Kiyosaki), không viết theo phiên âm.
- Sửa từ nhận sai theo ngữ cảnh ("nợ tư dùng" → "nợ tiêu dùng", "tăng đến nó" → "tăng đến đó").
- **Không** thêm, bớt, đổi từ người đọc thực sự nói. Không lấy lại kịch bản cũ.
- Mỗi câu một dòng, giữ dấu câu (dấu chấm quyết định chỗ đổi ảnh và ẩn phụ đề).
- Số đọc thành chữ: viết `5{năm}`, `1990{một_nghìn_chín_trăm_chín_mươi},`. Phụ đề hiện "5",
  còn căn chỉnh theo âm đọc thật (gạch dưới = cách chữ). Riêng liệt kê "một, hai, ba…" thì để chữ
  y như lời đọc.

### 3. Căn chỉnh từng từ + kiểm chéo
`python $S/align.py work/voice.mp3 work/script.txt work/words.json`

Script này chạy wav2vec2 tiếng Việt, cho ra mốc thật của từng từ (sai số ~20–40 ms), rồi in:
- **Từ khớp yếu**: điểm < −1,5.
- **Khác biệt** giữa lời thoại và bản mô hình tự nghe.

Soát từng dòng. Tên nước ngoài sẽ hiện dạng phiên âm, ví dụ "dô bợt ki y ô xa ki" = Robert Kiyosaki,
đó là bình thường. Lẫn phụ âm gi/d/r cũng bình thường ("dàu" = giàu). Mọi khác biệt còn lại là
dấu hiệu chữ sai: sửa `script.txt` rồi chạy lại cho tới khi chỉ còn khác biệt giải thích được.

Khi Whisper và wav2vec2 nghe khác nhau (vd "chịu được" / "chịu đựn"), chạy align với từng
phương án rồi so điểm `score` của từ đó trong `words.json`. Điểm gần 0 là đúng: "đựng" −0,28,
"được" −2,41, nên chọn "đựng". Whisper hay "sửa" thành từ quen hơn, nên đừng tin mặc định.

### 4. Lập kế hoạch (lần 1, chưa có ảnh)
Tạo `work/config.json` theo `examples/config.example.json`. Tối thiểu cần `audio`, `person`,
`hook_image`. Để `images: []`, **bỏ `sub_chunks`**, rồi chạy:
`python $S/plan.py work/words.json work/config.json work/plan.json`.
Kết quả in ra câu trích dẫn đã xếp dòng, danh sách shot kèm lời đọc trong từng shot, và các
cụm phụ đề tự chia. Đổi `sub_chunks` có thể làm dời mốc shot và đổi số shot: chạy lại `plan.py`
rồi mới đếm số ảnh (thiếu ảnh thì render báo lỗi `join() argument … NoneType`).

**Câu trích dẫn hook xuống dòng tự nhiên, như chữ tự xuống dòng.** Người dùng đã dặn hai lần:
- 02-10: "đừng cố làm 3 dòng, được mấy dòng thì mấy";
- 03-10: "đang bị xuống dòng dù ở trên chưa hết chỗ".

Cách xếp: lấp đầy mỗi dòng tới hết khung (960 px ở cỡ 50 px), chữ kế tiếp không vừa nữa mới
xuống dòng. Số dòng tuỳ câu. Chữ luôn 50 px, không thu nhỏ. Ngoại lệ duy nhất là không tách đôi
từ ghép hay tên riêng ("THÀNH / CÔNG"): cả cụm cùng xuống dòng. **Không** ngắt sớm theo cụm nghĩa
khi lấp đầy đã đẹp. Ngắt sớm để trống chỗ ở dòng trên, đúng lỗi người dùng đã chê.

**Khi lấp đầy ra xấu** (cắt đôi một cụm như "VỀ / NHÀ", hoặc để chữ mồ côi như "TIN NHẤT”" một
mình ở dòng cuối) thì mới tự đặt `headline_lines`. Chọn cách xếp gần lấp đầy nhất mà các dòng dài
gần bằng nhau. **Không bao giờ để một dòng chỉ 2–3 chữ** trong khi dòng khác gần đầy: 23-10 người
dùng hỏi ngay "sao lại xuống dòng như thế này?" khi dòng 1 chỉ có "ĐỂ MỌI NGƯỜI".
`python $S/do_tieu_de.py "<câu hook>"` in bản lấp đầy, báo dòng cụt, rồi liệt kê các phương án
3–4 dòng đã đo bề rộng và chấm điểm (dòng đều, không ngắt "KHỎE / NHẤT", "TÔI / NGHĨ"). Công cụ chỉ
đề xuất: đọc lại bằng mắt rồi mới chọn. `--do "dòng 1" "dòng 2"` đo các dòng tự viết.
Khi tự đặt `headline_lines`, ngoặc kép không tự thêm. Các video bộ 3 đều để không ngoặc.
Luôn xem frame hook trong preview trước khi render.

### 5. Rà phụ đề bằng mắt → chốt `sub_chunks`
Bộ chia tự động (pyvi tách từ + gán từ loại + luật hư từ) chỉ là bản nháp. Lỗi nó hay mắc:
tách động từ khỏi tân ngữ ("DÙNG / DỮ LIỆU") và tách danh từ khỏi tính từ ("CƯỢC / LỚN").
Đọc từng cụm và sửa theo luật:
- 1 dòng, thường 4–6 chữ (tối đa 7), ~0,8–1,3 s mỗi cụm. Không có cụm nào vắt qua dấu chấm.
- **Không cắt ngang** từ ghép (thành công, quy trình, tự học, dòng tiền…), tên riêng, số + đơn vị.
- Không kết thúc cụm bằng hư từ hoặc loại từ (của, và, với, những, một, lời, dòng, chiếc…).
  Không mở đầu cụm bằng từ dính ngược (hơn, nhất, lại, ra, được, của…).
- Ưu tiên ngắt ở dấu phẩy và trước liên từ hoặc giới từ (và, nhưng, mà, cho, trên, trước khi…).
- Tránh cụm < 0,5 s nhấp nháy, trừ cụm chốt câu ngắn.

Ghi danh sách cụm đã chốt vào `config.sub_chunks`, chữ thường theo đúng `script.txt`. Script tự
kiểm cụm có khớp đủ từ, đúng thứ tự và không vắt câu. Chỉ đặt `headline_lines` khi máy tách đôi
một từ ghép mà pyvi không nhận ra. Khi đó vẫn lấp đầy dòng, mỗi dòng ≤ 960 px ở 50 px, và tự ghi
ngoặc kép cong “ ” vào dòng đầu và dòng cuối. Không đặt `headline_size`.

### 6. Ảnh
Theo `references/chon-anh.md`: 1 ảnh hook + đúng số shot. **≥ 80% shot thân phải là chính nhân
vật** (còn lại là công ty hoặc sản phẩm của họ). Ảnh khái niệm chung chung tối đa 1–2 tấm.
Khi giao agent tìm ảnh, ghi rõ tỉ lệ này trong yêu cầu.

Công cụ tìm và soát ảnh:
1. `python $S/tim_anh_bing.py <work> tim "<từ khoá>" … --bo-qua <work video cũ cùng nhân vật> …`
   dựng bảng `_bing_*.jpg` có đánh số. Nhân vật châu Á thì tìm bằng tên gốc (张一鸣 演讲, 李嘉诚 采访…).
   Xem bảng, chọn số, rồi `… chon 1,10,13` ra `_chon.json`.
   Bing gọi từ Python có ngày trả kết quả rác (cá lóc, tiền Hà Lan…). Khi đó tìm trong trình duyệt
   của app rồi dựng bảng bằng `python $S/mk_sheet.py <work>`: cách làm ở mục "Tìm Bing trong trình
   duyệt" của `references/chon-anh.md`.
2. `python $S/tai_anh_web.py <work> <work>/_chon.json` tải ảnh gốc vào `<work>/web/`.
3. `python $S/loc_trung_anh.py <work>/web <work video cũ> …` so aHash/md5 với ảnh đã dùng.
   **Nhân vật làm nhiều video thì không được lặp ảnh giữa các video**, kể cả ảnh cùng buổi chụp
   khác khung (cùng bức tường, cùng áo): aHash không bắt được loại này nên phải xem bằng mắt.
4. Loại ảnh có watermark (kể cả chữ nhỏ ở góc như "知乎 @…"), chữ chèn, ảnh ghép, ảnh chụp màn hình
   TV/video có thanh đen hoặc ô che mờ (cắt bỏ được thì cắt), ảnh minh hoạ vẽ, ảnh người khác trùng tên.
   Ảnh nhỏ (< 800 px) upscale bị mềm: chỉ dùng khi không còn ảnh tốt hơn.
5. Ghi `images/manifest.json` (file, key, size, url, page, source, license).

Điền `images` theo thứ tự shot và chạy lại `plan.py`. Motion tự gán: ảnh dọc tự chuyển sang zoom. Muốn ép motion cho shot nào thì dùng
`motions: {"3": "zoom_out"}`. Nếu ảnh hook bị cắt mất mặt, chỉnh `hook_face_y` (vị trí mắt theo
tỉ lệ chiều cao ảnh, mặc định 0,3).
Ảnh hook phủ vùng 1274×1160, neo mép TRÁI rồi trượt sang trái 194 px. Với ảnh ngang thì chỉ phần
bên trái hiện ra, nên mặt nằm giữa/phải sẽ bị cắt. Cách sửa là cắt trước ảnh hook theo tỉ lệ
1274:1160 sao cho mặt nằm khoảng 40% bề ngang tính từ trái, rồi lưu thành `images/00_hook.jpg`.
Ảnh hook thấp hơn ~600 px bị phóng to gần 2 lần và mờ thấy rõ.

### 7. Xem trước rồi render
- Xem trước:
  `python $S/render.py work/plan.json work/prev --preview --frames=0,100,<đầu mỗi shot>`,
  rồi xem PNG để soát hook, bố cục và chỗ phụ đề đè lên mặt.
- Render: `python $S/render.py work/plan.json work/<Ten_Video>.mp4`, mất ~2–3 phút cho 35–40 s.
  Chạy render rồi `qa.py` ngay trong cùng một lệnh foreground (timeout 600000). **Không kết thúc
  lượt bằng câu "đang render…"**: 22-10 người dùng bực "tự qa đi còn chờ gì nữa".

### 8. Nghiệm thu bắt buộc
`python $S/qa.py work/plan.json work/<Ten_Video>.mp4`

Phải ra **ĐẠT**:
- đúng thông số và độ lớn âm thanh;
- **lệch karaoke ≤ 2 frame ở mọi từ**, đo trên chính video;
- không có phụ đề trong hook, có phụ đề ở mọi từ đang đọc.

Mở contact sheet `_qa_sheet.jpg` xem bằng mắt. CHƯA ĐẠT thì sửa rồi dựng lại, không bàn giao.

### 9. Bàn giao
Gửi file (SendUserFile). Báo ngắn bằng tiếng Việt:
- đường dẫn file;
- các tên riêng và từ đã sửa so với bản bóc;
- kết quả QA (lệch karaoke lớn nhất, LUFS);
- danh sách ảnh kèm tác giả và giấy phép (CC BY/BY-SA bắt buộc ghi công);
- điểm nào còn phân vân.

## Không bao giờ

- Tự thêm nhạc nền, SFX, CTA, logo, lời không có trong MP3.
- Dùng mốc Whisper cho karaoke hoặc chia đều thời gian câu cho các từ.
- Để phụ đề chạy trước hoặc sau giọng, hay biến mất khi đang có tiếng.
- Cắt cụm máy móc theo số chữ (lỗi của bản gốc: "HOÀN / TOÀN", "THÀNH / CÔNG").
- Dùng phụ đề chữ thường, đổi màu vàng, thêm hộp nền, xuống 2 dòng.
- Dùng ảnh có watermark hoặc chữ chèn, hoặc lặp một ảnh hai lần.
- Lấp shot bằng ảnh khái niệm chung chung (đường, la bàn, người lạ…) khi còn tìm được ảnh nhân vật.
- Tự ghi "X TỪNG NÓI" khi chưa có nguồn chắc chắn. Nhãn chuẩn là "BÀI HỌC TỪ X:".

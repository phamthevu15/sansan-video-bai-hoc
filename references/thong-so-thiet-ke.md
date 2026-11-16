# Thông số thiết kế — series "Bài học từ …" SanSan Academy

Mọi con số dưới đây **đo trực tiếp** trên 4 video mẫu (ngày 24–25/09/2026), bằng cách
bám điểm ORB từng frame, dò mép ảnh, khớp mô hình nền mờ và so font từng pixel. Bản chuẩn
là 2 video mới nhất: *Lee Kun-hee — Dám thay đổi* và *Akio Morita — REEDIT*. Cột "bản cũ"
ghi khác biệt của *Charlie Munger* và *Naval Ravikant* để biết đừng làm theo.

## 1. Khung hình và xuất file

| Mục | Giá trị |
|---|---|
| Kích thước | 1080 × 1920, 30 fps, H.264 High, yuv420p |
| Âm thanh | AAC mono 48 kHz ~180–190 kb/s, loudnorm **−16 LUFS, true peak −1,5 dBTP** (2 lượt, linear) |
| Độ dài | đúng bằng độ dài MP3 (làm tròn lên frame), giữ khung cuối tới hết tiếng |
| Nhạc nền / SFX | **không có** |
| Chuyển cảnh | **cắt thẳng** (hard cut) 100%, không hoà tan, không trượt |

## 2. Cấu trúc thời gian

| Đoạn | Quy tắc đo được |
|---|---|
| Hook | từ 0 tới lúc câu thứ 2 bắt đầu nói (3,5–3,9 s). Giọng đọc chính là câu trích dẫn trên màn hình |
| Thân | mỗi câu = 1 ảnh, cắt **đúng lúc câu mới bắt đầu** (cuối khoảng lặng). Câu dài hơn ~4,5 s thì cắt thêm 1 lần giữa câu |
| Độ dài shot | 1,9–4,5 s, trung bình ~2,9 s; 10–12 ảnh thân cho video ~35–39 s |
| Shot cuối | kéo tới hết video, thường là chân dung nhân vật, zoom in |

## 3. Hook (màn mở đầu)

| Thành phần | Thông số |
|---|---|
| Nền đỏ + ribbon "TƯ DUY / SANSAN ACADEMY" + gạch trắng | ảnh template cố định `assets/hook_template.png` (tách từ video, giống hệt nhau ở cả 4 video, sai số 0,12/255) |
| Vùng mờ dần ảnh → đỏ | alpha = smoothstep từ y=880 (0) tới y=1160 (1) — đã kiểm 5 điểm, sai < 0,03 |
| Ảnh chân dung | phủ kín vùng rộng 1080+194 × cao 1160; **trượt sang trái 194 px (18% × 1080), tuyến tính**, suốt hook, không zoom. Biên độ cố định, không phụ thuộc hook dài bao lâu |
| Nhãn | "BÀI HỌC TỪ {TÊN}:" — Inter **Bold 34 px** (chữ hoa cao 25 px), trắng, viền 2 px đen 58%, lề trái x=68, chân chữ y=1227 |
| Câu trích dẫn | Inter **ExtraBold 50 px** (chữ hoa cao 37 px), trắng, IN HOA, trong ngoặc kép cong “ ”, căn trái x=68, dòng đầu chân chữ y = 1311, mỗi dòng sau +75 px (1386, 1461, 1536…), rộng tối đa 960 px (lề phải 52 px; 944 px lề đối xứng hay để trống cả mảng dòng trên), viền 3 px đen 58% (thành đỏ sẫm ~#5A0508 trên nền đỏ). 4 video mẫu đều đúng 3 dòng. Từ 02-10 người dùng yêu cầu **xuống dòng tự nhiên, được mấy dòng thì mấy**; từ 03-10 thêm yêu cầu **lấp đầy dòng**: chỉ xuống dòng khi chữ kế tiếp không vừa 960 px, không ngắt sớm, không tách đôi từ ghép; từ 08-10 liên từ (và, hay, hoặc, nhưng, mà) không treo cuối dòng mà xuống cùng chữ sau; từ 09-10 dấu câu cuối dòng (” , . : ; ! ?) được treo ra lề: chữ ≤ 960 px, cả dấu ≤ 990 px. Giữ cỡ 50 px |
| Bỏ dấu chấm | không để dấu chấm trước ngoặc kép đóng |
| Phụ đề trong hook | **không có** |

Bản cũ (Munger/Naval): gạch trắng ở y=1133 thay vì 1145; chữ cao hơn 9 px; Naval dùng cỡ chữ nhỏ hơn (chữ hoa 33 px).

## 4. Thân video — ảnh chính

| Mục | Thông số |
|---|---|
| Bố cục | ảnh đặt giữa, tâm (540, 960), **rộng 926 px ở scale 1,0** (lề 77 px mỗi bên), cao theo tỉ lệ ảnh — ảnh dọc vẫn rộng 926 |
| Viền | không viền, không bo góc. (Viền giấy cũ ở 3 ảnh của video Lee Kun-hee là **viền có sẵn trong ảnh tư liệu**, không phải hiệu ứng — không tự thêm) |
| Bóng đổ | đen, độ đậm 60%, Gauss σ = 25 px, không lệch |
| Zoom in | scale 1,00 → **1,10 hoặc 1,11** (926 → ~1022 px), tâm (540, 960) |
| Zoom out | scale 1,10/1,11 → 1,00 |
| Pan | ảnh rộng cố định **1026 px (0,95 W)**; tâm đi từ 540+44,5 → 540−44,5 (pan trái) hoặc ngược lại — **tổng 89 px**, mép ảnh trượt ra ngoài khung một chút |
| Tốc độ | **tuyến tính**, không easing; biên độ cố định, shot ngắn thì chạy nhanh hơn (pan 89 px/2 s = 44 px/s; /4 s = 22 px/s) |
| Thứ tự | xen kẽ pan ↔ zoom: pan trái → zoom in → pan phải → zoom out … Pan chỉ dùng cho ảnh ngang; ảnh dọc luôn zoom. Shot cuối zoom in |

Quy đổi sang % để so với thói quen cũ "pan/zoom 12–20%":
hook pan = **18%** bề ngang khung; zoom thân = **10–11%**; pan thân = 89 px = **8,7%** bề ngang ảnh (8,2% khung).

Bản cũ: Munger pan 85,5 px, ảnh gốc 923 px; Naval ảnh gốc **1032 px** (gần tràn khung), pan **115 px**, zoom shot cuối 1,12. Bản mới đã thu ảnh lại 926 px cho thoáng.

## 5. Thân video — nền

| Mục | Thông số |
|---|---|
| Nguồn | chính ảnh của shot, phóng **phủ kín** 1080×1920 |
| Chuyển động nền | **đi cùng ảnh chính**: cùng scale (×1,00→×1,11 khi zoom) và cùng độ dịch ngang khi pan |
| Mờ | Gauss σ = 25 px (ở 1080p) |
| Độ sáng | × 0,385 |
| Gradient đáy | phủ đen tuyến tính từ y=1080 (0%) tới y=1920 (55%) — chỉ phủ nền, không phủ ảnh chính và phụ đề |

## 6. Phụ đề karaoke

| Mục | Thông số |
|---|---|
| Font | **Inter Bold**, libass Fontsize 46 = chữ hoa cao 26 px (~37 px em) |
| Chữ | **IN HOA** (bản cũ Munger/Naval viết thường — không dùng nữa), giữ dấu câu |
| Màu | chưa đọc trắng `#FFFFFF`, đã đọc vàng `#FFD400` (ASS `&H0000D4FF`) |
| Hiệu ứng | `\kf` — vệt vàng **quét liên tục qua từng ký tự** (có frame chữ "C" nửa vàng nửa trắng) |
| Viền / bóng | viền đen 4 px + bóng đen lệch (2, 2) px, không hộp nền |
| Vị trí | căn giữa x = 540, chân chữ y ≈ 1451 (chữ hoa y 1426–1451), **cố định**, đè lên ảnh dọc nếu ảnh dài xuống |
| Dòng | luôn **1 dòng**, rộng tối đa ~930 px |
| Nhịp | mỗi cụm ~1,0 s (0,8–1,3 s), 4–6 chữ; cụm cuối câu có thể ngắn 0,4–0,7 s |
| Chuyển cụm | trong cùng câu: cụm sau thay ngay khi từ đầu của nó bắt đầu. Hết câu: ẩn ngay sau từ cuối, hiện lại khi câu mới bắt đầu |

### Điểm bản gốc làm SAI — bản clone sửa lại
1. **Cắt cụm máy móc tối đa 6 chữ**, nên cắt đôi cả từ ghép: "HOÀN / TOÀN", "THÀNH / CÔNG",
   "PHƯƠNG / PHÁP", "QUY / TRÌNH". Bản clone chia theo nghĩa: không cắt từ ghép hay tên riêng,
   không kết thúc cụm bằng hư từ (của, và, những, một…), ưu tiên ngắt trước liên từ/giới từ.
2. **Mốc thời gian lấy thẳng từ Whisper** nên có lúc lệch: video Lee Kun-hee có ~0,5 s đang đọc
   "LEE KUN-HEE…" mà **không có phụ đề** (5,07–5,46 s). Bản clone căn chỉnh cưỡng bức (wav2vec2),
   sai số ≤ 1 frame, và QA đo lại trên chính video.

## 7. Thứ tự lớp

Hook: ảnh chân dung (pan) → template đỏ (alpha) → nhãn → câu trích dẫn.
Thân: nền mờ (đi theo ảnh) → phủ gradient đáy → bóng đổ → ảnh chính → phụ đề ASS.

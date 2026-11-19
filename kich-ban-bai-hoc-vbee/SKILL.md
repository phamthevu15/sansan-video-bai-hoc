---
name: kich-ban-bai-hoc-vbee
description: Viết bộ kịch bản video dọc 35–40 giây series "Bài học từ <nhân vật>" (kênh SEE THE LIGHT / SanSan Academy) rồi tạo MP3 giọng Vbee hàng loạt — gom câu hook có nguồn kiểm chứng của doanh nhân người Việt biết tên, lọc theo gu chủ kênh (châm ngôn sống, có cú lật, đọc một lần là hiểu), đưa duyệt danh sách hook, viết thân bài một mạch 176–188 tiếng, sinh bản đọc Vbee (phiên âm tên riêng, số thành chữ, nhịp nghỉ), dựng trang HTML duyệt, tạo MP3 Ngọc Huyền 1.1x qua Vbee Studio và tải về. Dùng khi người dùng nói "viết kịch bản mới", "nạp thêm kịch bản", "kịch bản đã xài hết", "bộ kịch bản tiếp theo", "kịch bản vbee", "tạo mp3", "tạo mp3 đi", "làm thêm 30 kịch bản", hoặc đưa tên doanh nhân/câu nói và muốn có kịch bản video bài học. Đầu ra của skill này là đầu vào của skill sansan-video-bai-hoc.
---

# Kịch bản "Bài học từ …" + MP3 Vbee

Một bài = **1 câu hook** (đọc ở đầu video, hiện to trên nền đỏ) + **thân bài một mạch**. Tổng cộng
176–188 tiếng, tương đương 36–39 giây ở giọng Ngọc Huyền 1.1x (đo trên 27 MP3 bộ 3: 4,91 tiếng/giây).
Sau đó skill `sansan-video-bai-hoc` dựng MP3 thành video.

Chủ kênh duyệt rất khắt khe. Hai bộ trước bị loại 35/40 rồi 21/24 câu, vì hook sai gu chứ không phải
vì nhân vật kém nổi. Mọi luật dưới đây đều rút ra từ những lần bị loại đó. Đọc kỹ trước khi viết:
- `references/gu-hook.md`: hook được giữ và bị loại, kèm phép thử "đọc một lần là hiểu".
- `references/nhan-vat.md`: ai được dùng, ai bị loại, các câu nổi tiếng nhưng gán tên sai.
- `references/viet-hoa-cau-noi.md`: cách chuyển câu nói gốc (Anh/Trung/Nhật/Hàn) thành câu tiếng Việt rõ nghĩa,
  10 cách đổi lời kèm 27 ví dụ đã duyệt, và cách ghi trường `doi`.
- `references/than-bai.md`: khuôn thân bài một mạch, kèm 3 bài mẫu đã duyệt.
- `references/vbee.md`: thiết lập giọng, cách tạo MP3 hàng loạt, các bẫy.
- `references/brief-gom-hook.md`: brief mẫu để giao agent đi gom ứng viên hook.

Đặt `K=~/.claude/skills/kich-ban-bai-hoc-vbee`. Python 3.12, luôn đặt `PYTHONIOENCODING=utf-8`.
Thư mục làm việc phải ngắn và nằm ngoài `%TEMP%` (Windows tự dọn), ví dụ `D:\ssan\kb<ddmm>\`.

## Quy trình (đúng thứ tự, có 2 điểm dừng chờ chủ kênh)

### 1. Chuẩn bị
- Hỏi (hoặc tự chọn nếu đã được dặn) số bài, thường 27–40.
- Đọc `data/loai_tru.txt`: đây là mọi hook đã dùng ở các bộ trước. Không viết câu trùng chữ hay trùng ý.
- Chép `references/brief-gom-hook.md` vào thư mục làm việc rồi điền số lượng và ngày.

### 2. Gom ứng viên hook có nguồn (gấp khoảng 2 lần số bài cần)
- Có thể chạy 2–3 agent song song theo vùng (Trung Quốc; Nhật–Hàn; Mỹ–Âu; Việt Nam). Mỗi agent nhận
  nguyên brief, tự tra nguồn và nộp JSON theo mẫu trong brief.
  - Báo trước cho chủ kênh là bước này mất khoảng 20–30 phút. Mỗi agent xong thì báo tiến độ.
    Agent chạy nền lâu mà im lặng, chủ kênh sẽ tưởng máy treo và huỷ.
- **Không bịa, không gán tên.** Mỗi câu phải có sự kiện, ngày và URL mở được. Câu chỉ thấy trên trang
  trích dẫn (BrainyQuote, Goodreads, ảnh quote) thì bỏ.

### 3. Tự lọc rồi đưa chủ kênh duyệt DANH SÁCH HOOK (điểm dừng 1)
- Việt hoá từng câu theo `references/viet-hoa-cau-noi.md` (giữ ý, đổi lời, ghi rõ chỗ đổi vào `doi`).
- Tự đọc từng câu theo `references/gu-hook.md`, nhất là phép thử: đọc to MỘT lần cho người Việt
  45–50 tuổi không biết nhân vật. Agent hay sai đúng điểm này, nên đừng tin agent đã tự chấm.
- Tối đa 2 bài/người. Chủ đề cha mẹ/gia đình dưới 1/3 bộ. Không để hai bài cùng ý.
- Ghi `bo.json` (mẫu: `examples/bo_mau.json`, mới có hook thì để `body` rỗng), rồi chạy
  `python $K/scripts/dung_bo.py <thư_mục> <tên-bộ> --chi-hook`. Lệnh này ra trang `Downloads/<tên-bộ>.html`
  gồm danh sách hook, nguồn, nguyên văn và chỗ đã Việt hoá. Có kèm 5–8 câu dự phòng.
- **Dừng, chờ chủ kênh duyệt.** Chưa viết thân bài, chưa tạo MP3 (để đỡ tốn công và điểm Vbee).
  Câu nào chủ kênh đã khen thì giữ nguyên chữ, không tự nối thêm vế.

### 4. Viết thân bài một mạch cho các hook đã duyệt
- Theo `references/than-bai.md` (khuôn 6 bước, một lập luận, một cảnh đời thường Việt kể trọn).
- Số viết bằng chữ ("năm một nghìn chín trăm chín mươi chín"), tên riêng viết đúng chính tả gốc.
- Chạy `python $K/scripts/dung_bo.py <thư_mục> <tên-bộ>`. Lệnh này:
  - đếm tiếng: hook phải 15–20 tiếng, tổng phải 176–188 tiếng;
  - báo số viết bằng chữ số, người quá 2 bài, tên bị loại, câu gần trùng `loai_tru.txt`;
  - sinh `tts` (thay tên nước ngoài bằng phiên âm Vbee theo `data/phien_am.json`, chèn nhịp nghỉ);
  - xuất `<tên-bộ>.json`, `vbee_<tên-bộ>.json` và trang `Downloads/<tên-bộ>.html`.

  Sửa tới khi không còn dòng `<<<`. Tên mới chưa có phiên âm thì thêm vào `data/phien_am.json`
  (Vbee đọc tên nước ngoài rất sai).
- Tự kiểm mạch từng bài: che một câu bất kỳ, câu sau phải mất nghĩa. Nếu không mất nghĩa thì bài
  đang liệt kê, phải viết lại.

### 5. Đưa chủ kênh đọc bản đầy đủ (điểm dừng 2), chờ lệnh "tạo mp3 đi"

### 6. Tạo MP3 Vbee
Làm theo `references/vbee.md`:
- dùng Claude in Chrome trên tab studio.vbee.vn đã đăng nhập sẵn;
- dán `scripts/vbee_tao_mp3.js`;
- nạp `vbee_<tên-bộ>.json`;
- tạo thử bài đầu tiên và nghe kiểm, rồi mới tạo cả loạt;
- lấy link, tải bằng `scripts/tai_mp3.py` vào `Downloads/<tên-bộ>/NN - Tiêu đề.mp3`.

Mỗi file phải dài 34–40 giây.

### 7. Chốt bộ
- `python $K/scripts/dung_bo.py <thư_mục> <tên-bộ> --ghi-loai-tru` cộng các hook đã dùng vào
  `data/loai_tru.txt`, để bộ sau không lặp lại.
- Báo ngắn bằng tiếng Việt:
  - đường dẫn HTML và thư mục MP3;
  - số bài;
  - thời lượng ngắn nhất và dài nhất;
  - số điểm Vbee đã dùng;
  - các câu đã Việt hoá mạnh so với nguyên văn.
- Khi dựng video, skill `sansan-video-bai-hoc` lấy chữ gốc từ `<tên-bộ>.json`: trường `body` là
  lời thoại. Đổi số trong `body` sang dạng `1999{một_nghìn_chín_trăm_chín_mươi_chín}`.

## Không bao giờ
- Bịa câu nói, gán tên, hoặc dùng câu đã biết là gán sai (danh sách trong `references/nhan-vat.md`).
- Tạo MP3 khi chủ kênh chưa duyệt. Tự đăng bài hay tự xuất bản bất cứ thứ gì.
- Dịch thẳng thành ngữ, ẩn dụ nước ngoài ("con chó chết", "ván ép", "xiềng xích thói quen").
- Viết hook dưới 15 tiếng, hook kiểu mẹo, khẩu hiệu, poster, LinkedIn.
- Viết thân bài theo khuôn ô rời ("Câu này không bảo bạn…", "Tối nay hãy…").
- Dùng nhân vật dính án hay bê bối lớn (Bill Gates từ 2-2026), hoặc tên người Việt 50 tuổi không biết.

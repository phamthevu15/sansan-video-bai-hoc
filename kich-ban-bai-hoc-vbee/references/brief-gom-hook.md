# Brief: gom ứng viên HOOK cho bộ kịch bản "Bài học từ …" (bộ ___, ngày ___)

Giao nguyên văn file này cho mỗi agent gom hook. Điền số lượng, vùng phụ trách và đường dẫn trước khi giao.

Kênh: video dọc 35–40 giây "BÀI HỌC TỪ <NHÂN VẬT>: <câu hook>" (kênh SEE THE LIGHT, khán giả Việt Nam, nhiều
người trung niên và lớn tuổi).

Việc ở bước này: CHỈ gom ứng viên hook có nguồn kiểm chứng. KHÔNG viết thân bài. Chủ kênh sẽ duyệt danh sách
hook trước.

Vùng phụ trách của bạn: ___ (ví dụ Trung Quốc–Hồng Kông / Nhật–Hàn / Mỹ–Âu / Việt Nam). Nộp khoảng ___ câu.

## 1. Đọc trước khi bắt đầu (các file nằm trong thư mục skill `~/.claude/skills/kich-ban-bai-hoc-vbee/`)
- `references/gu-hook.md`: gu hook, phép thử đọc một lần là hiểu, các loại câu bị loại.
- `references/nhan-vat.md`: người được dùng, người bị loại, các câu đã biết là gán tên sai.
- `data/loai_tru.txt`: mọi hook đã dùng. KHÔNG nộp câu trùng hoặc cùng ý. Đọc hết file.

## 2. Nguồn (bắt buộc)
- KHÔNG bịa, không gán tên. Mỗi ứng viên phải có nguồn gốc kiểm chứng được, như bài phỏng vấn, bài phát
  biểu, thư cổ đông, sách do chính người đó viết, video có thời điểm.
- Ghi rõ sự kiện, ngày và ít nhất 1 URL đã mở xem được. Có nguyên văn bằng ngôn ngữ gốc (Trung/Nhật/Hàn/Anh)
  càng tốt.
- Hook tiếng Việt được phép rút gọn hoặc Việt hoá, nhưng phải giữ đúng ý gốc. Ghi rõ chỗ đã đổi.
  Hình ảnh gốc xa lạ thì bỏ hình ảnh, nói thẳng ý.
- Câu chỉ thấy trên trang trích dẫn (BrainyQuote, Goodreads, ảnh quote) mà không lần ra nguồn gốc thì BỎ.

## 3. Đầu ra
Ghi JSON UTF-8 là một mảng, mỗi phần tử có dạng:
```json
{"id": "A01", "who": "Lý Gia Thành", "hook": "…câu hook tiếng Việt 15–20 tiếng…", "so_tieng": 18,
 "goc": "nguyên văn ngôn ngữ gốc", "nguon": "sự kiện, nơi, ngày", "url": ["https://…"],
 "doi_so_voi_goc": "đã rút gọn/Việt hoá chỗ nào", "chu_de": "sĩ diện", "hinh_anh": "hình ảnh đời thường trong câu",
 "chi_tiet_than_bai": "1–2 chi tiết đời thật của nhân vật quanh câu nói (có nguồn) để sau này viết thân bài",
 "rui_ro": "điểm yếu nếu có (nguồn mỏng, dễ bị mỉa, trùng ý…)"}
```

## 4. Tự chấm trước khi nộp
Từng câu phải qua đủ 6 điểm sau:
1. 15–20 tiếng.
2. Có cú lật.
3. Có hình ảnh đời thường mà người Việt nào cũng gặp.
4. Đọc to MỘT lần cho người Việt 45–50 tuổi không biết nhân vật: họ hiểu ngay và gật đầu "đúng thật".
5. Có nguồn và URL.
6. Không trùng ý với `loai_tru.txt`.

Thà nộp ít mà chắc còn hơn nộp nhiều câu nhạt.

# Bộ kỹ năng video "Bài học từ …" (kênh SEE THE LIGHT / SanSan Academy)

Hai skill cho Claude Code, nối thành một dây chuyền:

```
kich-ban-bai-hoc-vbee            →  MP3 giọng Vbee  →  sansan-video-bai-hoc (thư mục gốc repo)
gom hook có nguồn, chọn nhân vật,     Ngọc Huyền 1.1x      bóc lời, phụ đề karaoke, tìm ảnh,
Việt hoá câu nói, viết thân bài                            dựng video 9:16, tự nghiệm thu
```

| Skill | Thư mục | Làm gì |
|---|---|---|
| `sansan-video-bai-hoc` | gốc repo | Từ một file MP3: bóc lời, sửa tên riêng, căn từng từ, chia cụm phụ đề, xếp câu hook, tìm ảnh nhân vật, render MP4 và chạy QA (lệch karaoke ≤ 2 frame). |
| `kich-ban-bai-hoc-vbee` | `kich-ban-bai-hoc-vbee/` | Gom câu nói có nguồn kiểm chứng, chọn nhân vật người Việt biết tên, lọc theo gu chủ kênh, chuyển câu gốc sang tiếng Việt rõ nghĩa, viết thân bài một mạch, sinh bản đọc Vbee và tạo MP3 hàng loạt. |

## Quy cách chọn lựa và viết (đọc trước khi làm)

| Việc | File |
|---|---|
| Chọn nhân vật: ai được dùng, ai bị loại, câu nổi tiếng nhưng gán tên sai | `kich-ban-bai-hoc-vbee/references/nhan-vat.md` |
| Chọn câu hook: gu chủ kênh, phép thử "đọc một lần là hiểu", câu được giữ và bị loại | `kich-ban-bai-hoc-vbee/references/gu-hook.md` |
| Tìm nội dung có nguồn: brief giao agent đi gom ứng viên | `kich-ban-bai-hoc-vbee/references/brief-gom-hook.md` |
| Chuyển câu gốc (Anh/Trung/Nhật/Hàn) thành câu tiếng Việt rõ nghĩa: 10 cách đổi lời, 27 ví dụ đã duyệt | `kich-ban-bai-hoc-vbee/references/viet-hoa-cau-noi.md` |
| Viết thân bài một mạch 176–188 tiếng, kèm bài mẫu | `kich-ban-bai-hoc-vbee/references/than-bai.md` |
| Bản đọc Vbee: giọng, phiên âm tên riêng, số thành chữ, nhịp nghỉ, tạo MP3 hàng loạt | `kich-ban-bai-hoc-vbee/references/vbee.md`, `data/phien_am.json` |
| Hook đã dùng (không lặp lại) | `kich-ban-bai-hoc-vbee/data/loai_tru.txt` |
| Một bộ 27 bài đã duyệt hoàn chỉnh (nguyên văn, hook, chỗ đã đổi, nguồn, thân bài, bản đọc) | `kich-ban-bai-hoc-vbee/examples/bo-27-da-duyet-23-10.json` |
| Sửa lời thoại, chia cụm phụ đề, xếp dòng câu hook | `SKILL.md` (bước 2, 4, 5) |
| Chọn ảnh: ≥ 80% là nhân vật, nguồn, tìm Bing qua trình duyệt, các bẫy nhận nhầm người | `references/chon-anh.md` |
| Thông số thiết kế đo từ video mẫu | `references/thong-so-thiet-ke.md` |

## Cài đặt

Chép hai thư mục vào `~/.claude/skills/`:

```bash
git clone https://github.com/phamthevu15/sansan-video-bai-hoc.git ~/.claude/skills/sansan-video-bai-hoc
cp -r ~/.claude/skills/sansan-video-bai-hoc/kich-ban-bai-hoc-vbee ~/.claude/skills/
```

Thư mục gốc repo chính là skill video (có `SKILL.md`). Skill kịch bản nằm lồng bên trong nên phải chép ra
cạnh nó thì Claude Code mới nhận.

Yêu cầu:
- Python 3.12 với `numpy opencv-python-headless pillow faster-whisper torch transformers pyvi`, và ffmpeg.
  Kiểm bằng `python scripts/check_env.py`, phải in "SẴN SÀNG".
- Tạo MP3 cần tài khoản Vbee Studio đã đăng nhập sẵn trong Chrome (skill không bao giờ nhập mật khẩu,
  token chỉ đọc trong trang lúc chạy).
- Tìm ảnh cần trình duyệt (Claude in Chrome hoặc trình duyệt của app) khi Bing chặn truy vấn từ Python.

## Cách gọi

- "viết kịch bản mới", "làm thêm 30 kịch bản", "tạo mp3 đi" → skill kịch bản.
- Gửi MP3 rồi nói "edit video", "dựng video", "tạo video tiếp theo" → skill video.

Đường dẫn trong tài liệu (`D:\ssan\…`, `C:\Users\ADMIN\…`) là của máy chủ kênh, đổi theo máy mình.

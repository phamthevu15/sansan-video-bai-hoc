# Tạo MP3 trên Vbee Studio

## Thiết lập chuẩn (chủ kênh chốt 08-10 sau khi nghe thử 3 giọng)

| Mục | Giá trị |
|---|---|
| Giọng | HN – Ngọc Huyền, `hn_female_ngochuyen_full_48k-fhg` |
| Tốc độ | 1.1x (trang tự trả về 1x mỗi lần tải lại; gửi qua API thì luôn đúng 1.1) |
| Định dạng | mp3, 128 kbps, không nhạc nền |
| Ngắt nghỉ | dấu chấm 0,2 s · dấu phẩy 0,1 s · chấm phẩy 0,15 s · xuống dòng 0,25 s. Gửi kèm `clientPause` trong body. Trên giao diện, chỉnh ở nút "99" → Thiết lập ngắt nghỉ (cài theo tài khoản). |
| Nhịp nghỉ trong chữ | `dung_bo.py` tự chèn `<break time=…s/>`: sau hook 0,08; giữa các câu 0,05 / 0,1 / 0,08 xoay vòng; trước câu cuối 0,12 |
| Tốc độ đọc thực đo | 4,91 tiếng/giây, tức 176–188 tiếng ra 36,1–38,7 giây (bộ 3) |
| Điểm | Vbee tính theo ký tự chữ, không tính thẻ `<break/>`. 27 bài tốn khoảng 22.400 điểm. |

Tài khoản này còn dùng cho việc khác, ví dụ giọng nam đọc tin, tốc độ 1x. Đừng lấy thiết lập của lần
tạo gần nhất làm chuẩn: luôn dùng `__vb.CFG`.

## Cách chạy (Claude in Chrome, tab studio.vbee.vn đã đăng nhập sẵn)

Không bao giờ nhập mật khẩu. Chưa đăng nhập thì nhờ chủ kênh tự đăng nhập.

1. Mở tab mới vào `https://studio.vbee.vn/studio/text-to-speech`.
2. Dán toàn bộ `scripts/vbee_tao_mp3.js` qua `javascript_tool`. Lệnh này chỉ khai báo `window.__vb`.
3. `await __vb.timToken()`: phải ra `tok: true`. Xem 8 request gần nhất để biết chủ kênh vừa làm gì.
4. Chép `vbee_<bộ>.json` vào thư mục scratchpad của phiên, vì `file_upload` chỉ nhận file ở đó.
   Sau đó gọi `__vb.moONap()`, dùng `file_upload` đưa file vào ô `#__vbin`, rồi `__vb.daNap()` để kiểm số bài.
5. `await __vb.taoThu()` tạo bài đầu tiên. Gọi `await __vb.trangThai()` vài lần tới khi SUCCESS.
   Lấy link bằng `__vb.links(1,1)`, tải về và **nghe thử**: tên riêng đọc đúng chưa, có đúng giọng Ngọc
   Huyền 1.1x không.
6. `__vb.taoLoat()`: Web Worker gửi các bài còn lại, mỗi bài cách nhau 1,5 giây. Worker chạy được cả khi
   tab bị ẩn. Theo dõi bằng `__vb.tienDo()`.
7. Chờ 1–2 phút (Vbee xếp hàng), rồi gọi `await __vb.trangThai()` tới khi `st.SUCCESS` bằng số bài và `bad` rỗng.
8. `__vb.goc()` lấy đầu link S3. `__vb.links(1,9)`, `__vb.links(10,18)`, … lấy tên file theo lô 9 bài,
   vì kết quả trả về dài quá khoảng 1000 ký tự sẽ bị cắt. Ghi các dòng `NN|…` vào `links.txt`.
9. Chạy `python scripts/tai_mp3.py vbee_<bộ>.json links.txt ~/Downloads/<bộ>`. Mỗi file phải dài 34–40 giây.

## Bẫy đã gặp

- **Link S3 hết hạn sau vài ngày** (link ngày 23-10 trả 403 vào 29-10). Phải tải ngay sau khi tạo.
- **Mã request nằm ở `result.request_id`.** Dò bằng regex `"id"` sẽ bắt nhầm id lồng bên trong và làm
  vòng chờ treo.
- **Không `await` quá khoảng 15 giây trong một lệnh `javascript_tool`.** Máy ít RAM từng treo renderer hơn 5 phút vì
  await 40 giây. Muốn chờ thì gọi lệnh ngắn nhiều lần.
- **Biến `const` không còn ở lần gọi sau.** Mọi thứ phải gắn vào `window`; `__vb` đã làm sẵn việc này.
- **Redux store:** phải duyệt cây fiber từ `#root` qua child và sibling. Cách đi `child||return` không ra.
- **Token chỉ dùng trong trang.** Không in token ra, không chép ra ngoài.
- **Không fetch từ trang Vbee về `127.0.0.1`**: Chrome sẽ đòi quyền "mạng cục bộ".
- **Tab bị ẩn** khi chủ kênh dùng tab khác: bấm phím và hẹn giờ trong trang bị hãm, chỉ Worker còn chạy đều.
- **PowerShell 5.1 đọc file .ps1 không BOM sẽ làm hỏng chữ Việt.** Dùng Python để tải, tên file tiếng Việt
  vẫn đúng. `curl` trong Git Bash làm hỏng tên file tiếng Việt.
- **Thay MP3 của một bài:** chuyển bản cũ vào Thùng rác trước (không xoá thẳng), rồi tạo lại đúng bài đó.
  Video đã dựng từ bản cũ thì phải dựng lại.

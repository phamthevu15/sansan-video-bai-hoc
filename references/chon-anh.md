# Tìm và chọn ảnh

Người dùng chỉ đưa MP3. Ảnh là việc của Claude. Số ảnh = 1 ảnh hook + số shot mà
`plan.py` in ra (thường 10–12).

## Nguồn (theo thứ tự ưu tiên)

1. **Wikimedia Commons API**: không cần khoá, giấy phép rõ ràng.
   `https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch=<từ khoá>&gsrlimit=30&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=2000&format=json`
   Nhớ gửi `User-Agent` mô tả (curl `-A "SansanVideoBot/1.0"`), không có là bị chặn. Ảnh chân dung
   người nổi tiếng thường có bộ của Gage Skidmore (CC BY-SA), chất lượng cao.
2. Ảnh báo chí hoặc ảnh chính thức của doanh nghiệp/nhân vật, chỉ khi Commons không có.
   Ghi lại nguồn.
3. Openverse chỉ trả ảnh xem trước ~1024 px, dưới chuẩn. Chỉ dùng để tìm ra trang gốc.

Có thể giao một agent chạy nền đi tìm, nhưng phải đưa đủ các yêu cầu dưới đây và bắt nó ghi
`images/manifest.json` (file, kích thước, trang nguồn, tác giả, giấy phép).

## Yêu cầu bắt buộc

- Không watermark, không chữ chèn sẵn, không logo báo hay kho ảnh, không ảnh ghép, không ảnh chụp màn hình.
- Cạnh dài ≥ 1200 px. Riêng ảnh hook cao ≥ 1400 px.
- Đúng nhân vật. Ảnh hook ưu tiên giai đoạn dễ nhận ra, mặt nằm ở nửa trên, đầu-vai hoặc nửa người,
  dọc hoặc vuông (hook phủ vùng 1274×1160 nên ảnh dọc cao sẽ bị cắt bớt phía dưới).
- Ảnh thân chủ yếu ngang (pan cần ảnh ngang). Ảnh dọc vẫn dùng được: tự chuyển sang zoom,
  rộng 926 px, phụ đề đè lên phần dưới ảnh như bản gốc.
- Ảnh tư liệu cũ, đen trắng dùng bình thường (bản gốc dùng nhiều).

## Phân bổ: 80–90% ảnh là NHÂN VẬT (luật cứng, người dùng đã nhắc)

Đếm trên 4 video mẫu:
- Lee Kun-hee: 12/12 ảnh là Lee hoặc Samsung (nhà máy, điện thoại, wafer).
- Akio Morita: 11/11 là Morita hoặc Sony.
- Munger: 9/12 là Munger.
- Naval: 7/10 là Naval.

Vì vậy:

- **≥ 80% shot thân là chính nhân vật** (chân dung, đang phát biểu, làm việc, gặp gỡ người khác,
  ảnh tư liệu thời trẻ). Ảnh có người khác cùng khung vẫn tính, miễn nhân vật rõ mặt.
- Phần còn lại ưu tiên ảnh **gắn trực tiếp với nhân vật**: công ty, trụ sở, sản phẩm, nhà máy, thương
  vụ, sự kiện của họ (vd Son → SoftBank, robot Pepper, Alibaba, ARM, WeWork; Kiyosaki → sách
  Rich Dad Poor Dad).
- Ảnh khái niệm chung chung (con đường, la bàn, người lạ học bài, thành phố, biểu đồ, heo đất…)
  **tối đa 1–2 tấm mỗi video**. Câu nói về "đời thường" hay "bạn" vẫn dùng ảnh nhân vật, giống bản
  gốc Munger ("Bạn không cần thắng mọi ván" đặt trên ảnh Munger).
- Shot đầu phần thân và **shot cuối** bắt buộc là nhân vật.
- Kho ảnh tự do về nhân vật ít thì mở rộng nguồn trước khi lùi về ảnh khái niệm:
  - `Category:<Tên nhân vật>` trên Commons;
  - ảnh chính phủ có giấy phép mở: Kremlin.ru CC BY 4.0, Nhà Trắng public domain, văn phòng Thủ
    tướng Nhật/Ấn, Korea.net CC BY-SA, Phủ Tổng thống Mexico/Đài Loan;
  - Flickr CC của sự kiện (Web Summit, TechCrunch, World Economic Forum);
  - ảnh tư liệu cũ.

  Chấp nhận ảnh nhỏ hơn chuẩn một chút (≥ 1000 px) nếu là ảnh nhân vật, và ghi rõ trong báo cáo.
- **Ảnh giấy phép mở vẫn không đủ 80%** (vd Jim Rohn chỉ có 3 ảnh, 2 ảnh CC BY-NC-ND): người dùng
  đã chốt ngày 27/09/2026 là **dùng ảnh báo chí/ảnh chính thức**. Nguồn gồm web chính thức của nhân
  vật/đối tác, bài báo, tạp chí, Flickr giữ bản quyền. Rủi ro bản quyền do người dùng chịu.
  - Vẫn cấm ảnh có watermark (ảnh xem trước Getty/Alamy/Shutterstock), ảnh có chữ chèn, ảnh AI giả,
    người đóng giả.
  - Manifest ghi `license: "all rights reserved – used with user's acceptance"` kèm `source_page_url`.
  - Không cần hỏi lại mỗi lần. Báo trong phần bàn giao là có dùng ảnh giữ bản quyền.
- Ảnh scan có lề trắng thì cắt lề trước khi dựng (cắt dư 4–5 px, đo trung bình từng cột/hàng ở mép).
- Không lặp lại cùng một ảnh trong một video (bản gốc Munger lặp 3 ảnh, đừng theo).
- Trước khi dựng, đếm lại: số shot là nhân vật / tổng shot phải ≥ 0,8. Chưa đủ thì tìm tiếp.

## Giấy phép

Ảnh CC BY / CC BY-SA bắt buộc ghi tác giả + giấy phép. Khi bàn giao, liệt kê trong báo cáo
để người dùng dán vào phần mô tả bài đăng.

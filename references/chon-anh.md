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

## Tìm Bing trong trình duyệt (khi Python bị Bing chặn)

Có những ngày Bing trả kết quả rác cho mọi từ khoá gọi từ Python (`tim_anh_bing.py` ra ảnh cá lóc, tiền
Hà Lan, sơ đồ phanh). Trong trình duyệt của app (tab đang mở bing.com) thì `fetch` vẫn ra đúng, kể cả
từ khoá chữ Nhật/Trung/Hàn.

1. Mở tab `https://www.bing.com/images/search?q=<tên nhân vật>`. Mỗi lần điều hướng phải nạp lại hàm:
   ```js
   window.__g = async (q) => { const out=[]; for (const ep of ['async','search']) { for (const first of [0,35]) {
     const r = await fetch(`https://www.bing.com/images/${ep}?q=`+encodeURIComponent(q)+`&first=${first}&count=35&qft=+filterui:imagesize-large&mmasync=1&form=IRFLTR`);
     const d = new DOMParser().parseFromString(await r.text(),'text/html');
     for (const a of d.querySelectorAll('a.iusc')) { try { const m=JSON.parse(a.getAttribute('m')); out.push([m.murl,m.purl,m.turl]); } catch(e){} } }
     if (out.length) break; } return out; };
   window.__ids = (rows)=>rows.map(r=>{const u=r[3]||''; const m=u.match(/[?&]id=([^&]+)/);
     return (m?m[1]:u).replace(/^OIP\./,'')+'@'+(u.match(/\/\/(ts\d)\./)||['','ts1'])[1];}).join(' ');
   window.__search = async (qs, skip=[]) => { const seen=new Set(skip); const rows=[];
     for (const q of qs) for (const [m,p,t] of await window.__g(q)) if(!seen.has(m)){seen.add(m); rows.push([q,m,p,t]);}
     return rows; };
   window.__R = window.__R || {};
   ```
2. Tìm nhiều từ khoá theo đúng nội dung từng shot (vd "Warren Buffett Salomon 1991 testimony", "Henry Ford
   Thomas Edison"), lọc bỏ kho ảnh có watermark, lưu vào `window.__R[<số bài>]`:
   ```js
   const bad=/getty|alamy|shutterstock|istock|dreamstime|depositphotos|123rf|ftcdn|ytimg|youtube|quote|meme|freepik|pngtree|cartoon|tiktok|bridgeman/i;
   window.__R[22] = (await window.__search([...])).filter(r=>!bad.test(r[1]+r[2]));
   window.__ids(window.__R[22])
   ```
3. Trình duyệt không gửi được dữ liệu về `127.0.0.1` (bị chặn mạng nội bộ). Chép chuỗi mã trả về vào
   `<work>/_th_ids.txt`, rồi `python $S/mk_sheet.py <work>` dựng `_br_0.jpg`, `_br_1.jpg`… (64 ảnh/bảng,
   có số vàng). Quá 250 mã thì nên bớt từ khoá, chép tay dài dễ sai.
4. Xem bảng, chọn số, hỏi lại URL gốc chỉ cho các số đã chọn:
   `JSON.stringify([3,17,40].map(i=>['k'+i, window.__R[22][i][1], window.__R[22][i][2]]))`.
   Ghi `<work>/_chon.json` dạng `[key, url_anh, trang_nguon, ten_nguon]`, rồi chạy `tai_anh_web.py`
   và `loc_trung_anh.py` như bình thường.

## Bẫy đã gặp khi chọn ảnh (bộ 3, 11-2026)

- **Nhận nhầm người.** Ảnh ghi "Carnegie at desk" trên Pinterest là Andrew Carnegie chứ không phải Dale.
  Ảnh "Henry Ford" cười đội mũ trên alchetron là con trai ông, Edsel Ford. Ảnh "Buffett năm 1991" đứng
  cạnh xe buýt hoá ra là người khác. Trước khi chốt, đọc `purl` và chú thích ảnh. Trang gallery của báo
  (vd CNN "life in pictures") có chú thích từng ảnh, đọc được bằng Python.
- **Ảnh AI.** Đường dẫn có `ai-images`, `contentshake`, chân dung "studio portrait of a distinguished…",
  tranh minh hoạ, ảnh tô màu kiểu tranh: loại.
- **Một ảnh gốc, nhiều bản cắt.** `loc_trung_anh.py` không bắt được bản cắt chặt từ cùng một ảnh
  (Carnegie: ảnh hook và ảnh shot 9 là cùng một bức chân dung, chỉ khác khung). Soát bằng mắt ảnh hook so
  với các shot, và so với ảnh video cũ cùng nhân vật.
- **Ảnh cùng buổi chụp** (cùng áo, cùng ghế, cùng bức tường) đặt cạnh nhau trông như lặp. Mỗi buổi chụp
  dùng tối đa một tấm, nếu dùng hai thì để cách xa nhau.
- **Viền và huy hiệu.** Ảnh kho lưu trữ (Collections, The Henry Ford…) hay có viền đen và một huy hiệu đỏ
  nhỏ ở góc trên trái. Cắt viền theo độ sáng trung bình từng hàng/cột, rồi dò điểm đỏ trong ô 200 px ở
  góc để cắt tiếp. Chữ ghi nguồn dưới ảnh ("Seth Poppel Yearbook Library") thì cắt bỏ phần đó.
- **Hook cụt đỉnh đầu.** Đặt `hook_face_y` 0,18–0,22 để thấy thêm phía trên. Ảnh gốc đã cắt sát đầu thì
  không cứu được, đổi ảnh khác (ưu tiên ảnh dọc độ phân giải cao còn khoảng trống trên đầu).
- **Ảnh theo đúng chuyện trong lời đọc.** Câu nói ra đời ở sự kiện nào thì tìm ảnh đúng sự kiện đó
  (Buffett điều trần vụ Salomon 1991, Zuckerberg nhận bằng Harvard 2017, Munger cùng Buffett). Câu nhắc
  vợ con, cha mẹ thì tìm ảnh gia đình thật của nhân vật. Câu chung chung vẫn dùng chân dung nhân vật.
- **Trang chặn tải** (403/402 từ people.com, telegraph, Ford Media…): bỏ qua, tìm bản khác của cùng ảnh
  trên trang khác. Không vượt chặn.

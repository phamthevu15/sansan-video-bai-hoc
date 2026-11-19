"""Tải MP3 Vbee (link S3 công khai) về thư mục bộ, đặt tên "NN - Tiêu đề.mp3", đo thời lượng.

Chạy: python tai_mp3.py <vbee_<bộ>.json> <links.txt> <thư_mục_ra> [--goc <đầu link S3>]
      ví dụ: python tai_mp3.py D:/ssan/kb0511/vbee_30-kich-ban-moi-05-11.json D:/ssan/kb0511/links.txt ~/Downloads/30-kich-ban-moi-05-11
links.txt: mỗi dòng "NN|YYYY/MM/DD/ten_file.mp3" (đúng như __vb.links() in ra), hoặc một link đầy đủ https://….mp3
           (NN lấy từ đầu tên file, vì Vbee đặt tên file theo tiêu đề "NN - …").
Mặc định --goc là https://vbee-studio2-3.s3.ap-southeast-1.amazonaws.com/synthesis/ (xem __vb.goc()).
File đã có thì bỏ qua. Bản cũ cần thay thì chuyển vào Thùng rác trước, không xoá thẳng.
Link S3 của Vbee HẾT HẠN sau vài ngày (link 23-10 trả 403 vào 29-10): tải ngay sau khi tạo. Hết hạn thì mở
Lịch sử trên studio.vbee.vn lấy link mới (__vb.trangThai() với id cũ), không cần tạo lại.
Thời lượng chuẩn 34–40 s; ngoài khoảng đó in "<<<".
"""
import sys, os, re, json, glob, subprocess, urllib.request

GOC = "https://vbee-studio2-3.s3.ap-southeast-1.amazonaws.com/synthesis/"


def ffprobe():
    for p in glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages",
                                    "Gyan.FFmpeg*", "*", "bin", "ffprobe.exe")):
        return p
    return "ffprobe"


def giay(fn, fp):
    try:
        return float(subprocess.run([fp, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", fn],
                                    capture_output=True, text=True).stdout.strip())
    except Exception:
        return None


def ten_sach(s):
    return re.sub(r'[<>:"/\\|?*]', "", s).strip()


def main():
    a = sys.argv[1:]
    goc = GOC
    if "--goc" in a:
        k = a.index("--goc")
        goc = a[k + 1].rstrip("/") + "/"
        a = a[:k] + a[k + 2:]
    if len(a) < 3:
        sys.exit(__doc__)
    V = {x["n"]: x for x in json.load(open(a[0], encoding="utf-8"))}
    out = os.path.expanduser(a[2])
    os.makedirs(out, exist_ok=True)
    link = {}
    for l in open(a[1], encoding="utf-8"):
        l = l.strip()
        if not l:
            continue
        if "|" in l:
            n, p = l.split("|", 1)
            u = p if p.startswith("http") else goc + p
        else:
            u = l
        m = re.match(r"(\d+)", n) if "|" in l else re.match(r"(\d+)", u.rsplit("/", 1)[-1])
        if not m:
            print("không đọc được số bài:", l)
            continue
        link[int(m.group(1))] = u
    fp = ffprobe()
    thieu = [n for n in V if n not in link]
    for n in sorted(link):
        if n not in V:
            print(f"{n:02d} có link nhưng không có trong {os.path.basename(a[0])}")
            continue
        fn = os.path.join(out, ten_sach(V[n]["title"]) + ".mp3")
        if not os.path.exists(fn):
            try:
                d = urllib.request.urlopen(link[n], timeout=60).read()
            except Exception as e:
                print(f"{n:02d} LỖI TẢI ({e}): link hết hạn thì lấy link mới  <<<")
                continue
            if len(d) < 50000:
                print(f"{n:02d} tải về chỉ {len(d)} byte, không phải MP3  <<<")
                continue
            open(fn, "wb").write(d)
        s = giay(fn, fp)
        canh = "" if s and 34 <= s <= 40 else "  <<<"
        print(f"{n:02d} {s or 0:5.1f} s  {os.path.basename(fn)}{canh}")
    if thieu:
        print("CHƯA CÓ LINK:", ", ".join(f"{n:02d}" for n in sorted(thieu)))
    print("thư mục:", out)


if __name__ == "__main__":
    main()

"""CÔNG CỤ ĐO VIDEO MẪU — dùng khi người dùng gửi mẫu mới và muốn cập nhật phong cách.

    python do_mau.py mau.mp4 out/motion.json

Mỗi shot (giữa hai điểm cắt): frame đầu làm tham chiếu, bắt điểm ORB trên vùng sắc nét,
khớp sang từng frame sau, ước lượng phép đồng dạng -> scale(t), tx(t), ty(t).
In ra từng shot: thời điểm, scale cuối (zoom 1.10 = zoom in 10%), tx (pan px). Đọc kiểu
stream để tiết kiệm RAM. Kích thước ảnh gốc thì đo tay bằng profile điểm ảnh ở frame đầu shot.
"""
import subprocess, sys, json, os
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ffmpeg_bin

FF = ffmpeg_bin()
W, H = 1080, 1920

def stream(path):
    p = subprocess.Popen([FF, "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         stdout=subprocess.PIPE, bufsize=W * H * 4)
    n = W * H
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W)

orb = cv2.ORB_create(nfeatures=4000, fastThreshold=12)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

def sharp_mask(g):
    lap = np.abs(cv2.Laplacian(g.astype(np.float32), cv2.CV_32F, ksize=3))
    d = cv2.GaussianBlur((lap > 12).astype(np.float32), (0, 0), 12)
    m = ((d > 0.06) * 255).astype(np.uint8)
    m[1370:1520, :] = 0  # dải phụ đề
    return m

def small(g):
    return cv2.resize(g, (135, 240), interpolation=cv2.INTER_AREA).astype(np.float32)

if __name__ == "__main__":
    path, outp = sys.argv[1], sys.argv[2]
    thr = float(sys.argv[3]) if len(sys.argv) > 3 else 18.0
    shots, cur, prev_s = [], None, None
    kp0 = d0 = None
    for i, g in enumerate(stream(path)):
        s = small(g)
        is_cut = prev_s is None or np.abs(s - prev_s).mean() > thr
        prev_s = s
        if is_cut:
            cur = {"a": i, "fg": []}
            shots.append(cur)
            kp0, d0 = orb.detectAndCompute(g, sharp_mask(g))
            # lưu frame đầu shot để đo khung ảnh sau
            cv2.imwrite(outp.replace(".json", f"_shot{len(shots)-1:02d}_first.png"), g)
        kp1, d1 = orb.detectAndCompute(g, None)
        rec = None
        if d0 is not None and d1 is not None:
            ms = bf.match(d0, d1)
            if len(ms) >= 8:
                p0 = np.float32([kp0[x.queryIdx].pt for x in ms])
                p1 = np.float32([kp1[x.trainIdx].pt for x in ms])
                M, inl = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=2.0,
                                                     maxIters=4000, confidence=0.999)
                if M is not None:
                    rec = {"i": i, "s": float(np.hypot(M[0, 0], M[1, 0])), "tx": float(M[0, 2]),
                           "ty": float(M[1, 2]), "n": int(inl.sum())}
        cur["fg"].append(rec)
        cur["b"] = i + 1
        if cur["b"] - cur["a"] > 1 and i % 1 == 0:
            pass
        last_g = g
    cv2.imwrite(outp.replace(".json", f"_shot{len(shots)-1:02d}_last.png"), last_g)
    for k, sh in enumerate(shots):
        v = [r for r in sh["fg"] if r]
        e = v[-1] if v else None
        print(f"shot {k:2d}: {sh['a']/30:6.2f}-{sh['b']/30:6.2f}s ({sh['b']-sh['a']:3d}f)",
              "end s=%.4f tx=%.1f ty=%.1f n=%d" % (e["s"], e["tx"], e["ty"], e["n"]) if e else "-")
    json.dump({"shots": shots}, open(outp, "w"))

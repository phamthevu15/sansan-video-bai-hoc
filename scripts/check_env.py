"""Kiểm tra môi trường trước khi dựng: ffmpeg (có libass), các gói Python, font, template.

    python check_env.py
"""
import sys, os, subprocess, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ffmpeg_bin, FONT_BOLD, FONT_XBOLD, HOOK_TEMPLATE

ok = True
try:
    ff = ffmpeg_bin()
    v = subprocess.run([ff, "-version"], capture_output=True, text=True).stdout
    print("ffmpeg :", v.splitlines()[0])
    if "--enable-libass" not in v:
        ok = False; print("  LỖI: ffmpeg không có libass (cần bản Gyan full build)")
except SystemExit as e:
    ok = False; print(e)
for mod, pipname in [("numpy", "numpy"), ("cv2", "opencv-python-headless"), ("PIL", "pillow"),
                     ("faster_whisper", "faster-whisper"), ("torch", "torch --index-url https://download.pytorch.org/whl/cpu"),
                     ("transformers", "transformers"), ("pyvi", "pyvi")]:
    try:
        importlib.import_module(mod)
        print(f"{mod:15s}: có")
    except Exception:
        ok = False
        print(f"{mod:15s}: THIẾU -> pip install {pipname}")
for p in (FONT_BOLD, FONT_XBOLD, HOOK_TEMPLATE):
    print(("có   " if os.path.exists(p) else "THIẾU"), p)
    ok &= os.path.exists(p)
print("SẴN SÀNG" if ok else "CHƯA SẴN SÀNG")

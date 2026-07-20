# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH)
datas = [(str(root / "assets"), "assets")]
binaries = []
for name in ("yt-dlp.exe", "ffmpeg.exe", "ffprobe.exe"):
    source = root / "bin" / name
    if source.exists(): binaries.append((str(source), "bin"))

a = Analysis(["app/main.py"], pathex=[str(root)], binaries=binaries, datas=datas, hiddenimports=[], hookspath=[])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="MediaGrab", debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, name="MediaGrab")


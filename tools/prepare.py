"""Prepare the work folder from your own copy of the game.

    python tools/prepare.py <Shadow the Hedgehog (Japan).rvz|.iso> [path/to/DolphinTool.exe]

  work/original.iso   the disc as a plain ISO (DolphinTool convert), checked against its SHA-1
  work/disc/          its files (DolphinTool extract)
  text/ja/            the Japanese source text (tools/extract.py)
"""
import hashlib, os, shutil, subprocess, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
WORK = os.path.join(ROOT, "work")
SHA1 = "1d4d1a069d87bdcc6985ffd16d1d19328bb3ae69"     # Shadow the Hedgehog (Japan), GUPJ8P


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while b := f.read(1 << 24):
            h.update(b)
    return h.hexdigest()


def main():
    src = sys.argv[1]
    tool = sys.argv[2] if len(sys.argv) > 2 else (shutil.which("DolphinTool") or "DolphinTool.exe")
    os.makedirs(WORK, exist_ok=True)
    iso = os.path.join(WORK, "original.iso")
    subprocess.run([tool, "convert", "-i", src, "-o", iso, "-f", "iso"], check=True)
    if sha1(iso) != SHA1:
        sys.exit(f"{iso}: SHA-1 differs from the Japanese release ({SHA1}); use an unmodified GUPJ8P disc")
    disc = os.path.join(WORK, "disc")
    if os.path.exists(disc):
        shutil.rmtree(disc)
    subprocess.run([tool, "extract", "-i", iso, "-o", disc, "-q"], check=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "extract.py")], check=True)
    print("ready: python tools/build.py")


if __name__ == "__main__":
    main()

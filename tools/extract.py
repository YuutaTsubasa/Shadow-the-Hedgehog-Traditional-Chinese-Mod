"""Extract every Japanese .fnt message table into translation units.

    python tools/extract.py        -> text/ja/<FILE>.json  (FILE = Movie, Save, Advertise, stg0100 ...)

Unit: {id (message id), ja, lines, max_units, frames, speaker?}. Empty strings are skipped
(the build keeps them empty). Speakers come from the voice file name in PRS_VOICE_J.afs.
"""
import glob, json, os, struct, sys

sys.path.insert(0, os.path.dirname(__file__))
import fnt

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DISC = os.path.join(ROOT, "work", "disc", "files")
SPEAKERS = {
    "am": "艾咪", "bd": "黑暗末日", "ch": "查米", "cm": "GUN指揮官", "co": "巧歐", "cr": "克琳姆",
    "eg": "蛋頭博士", "es": "艾斯皮歐", "gr": "傑拉德", "kn": "納克魯斯", "mr": "瑪莉亞",
    "mr2": "瑪莉亞", "om": "Omega", "pr": "總統", "rg": "露姬", "sc": "祕書", "sd": "夏特",
    "sl": "GUN士兵", "sn": "索尼克", "tl": "塔爾斯", "vc": "貝庫特",
}


def voice_names():
    with open(os.path.join(DISC, "PRS_VOICE_J.afs"), "rb") as f:
        f.seek(4); n = struct.unpack("<I", f.read(4))[0]
        f.seek(8 + 8 * n); off, _ = struct.unpack("<II", f.read(8))
        f.seek(off); t = f.read(48 * n)
    return [t[48 * i:48 * i + 32].rstrip(b"\0").decode() for i in range(n)]


def units(line):
    return sum(1 if ord(c) < 0x80 or 0xff61 <= ord(c) <= 0xff9f else 2 for c in line)


def main():
    voices = voice_names()
    os.makedirs(os.path.join(ROOT, "text", "ja"), exist_ok=True)
    for p in sorted(glob.glob(os.path.join(DISC, "fonts", "*", "*_JP.fnt"))):
        name = os.path.basename(p)[:-7]
        entries, _ = fnt.parse(open(p, "rb").read())
        rows = []
        for e in entries:
            if not e["text"]:
                continue
            r = {"id": str(e["id"]), "ja": e["text"], "lines": e["text"].count("\n") + 1,
                 "max_units": max(units(l) for l in e["text"].split("\n")), "frames": e["frames"]}
            if e["audio"] >= 0:
                r["voice"] = voices[e["audio"]]
                sp = voices[e["audio"]].rsplit("_", 1)[1][:-4]
                if sp in SPEAKERS:
                    r["speaker"] = SPEAKERS[sp]
            rows.append(r)
        with open(os.path.join(ROOT, "text", "ja", name + ".json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print(f"{name:10} {len(rows)}")


if __name__ == "__main__":
    main()

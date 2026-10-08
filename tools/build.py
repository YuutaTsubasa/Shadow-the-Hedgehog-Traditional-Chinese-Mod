"""Build the patched disc: text/zh -> .fnt + per-file fonts -> out/<name>.iso

    python tools/build.py [--only FILE,...] [--test] [--no-patch]

For each Japanese message table the text is zh (text/zh/<FILE>.json), else the TM, else the
original Japanese. Every .fnt gets a font holding exactly its characters; .met files beyond the
original count are added to the disc; main.dol is patched so the game sees
them (tools/dolpatch.py). Texture text (stage titles, title logo) comes from tools/tex.py. --test also writes work/build/ for inspection.
"""
import glob, hashlib, json, os, shutil, subprocess, sys, time

sys.path.insert(0, os.path.dirname(__file__))
import dolpatch, fnt, font, gcm, tex

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DISC = os.path.join(ROOT, "work", "disc", "files")
ISO = os.path.join(ROOT, "work", "original.iso")
OUT = os.path.join(ROOT, "out", "Shadow the Hedgehog (zh-TW).iso")
PATCH = os.path.join(ROOT, "out", "Shadow.the.Hedgehog.Japan.zh-TW.xdelta")
README = os.path.join(ROOT, "out", "README.txt")
# xdelta3 3.1.0 (github.com/jmacd/xdelta-gpl); override with the XDELTA3 environment variable
XDELTA = os.environ.get("XDELTA3") or os.path.join(ROOT, "work", "bin", "xdelta3.exe")


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while b := f.read(1 << 24):
            h.update(b)
    return h.hexdigest()


def make_patch():
    """original.iso -> OUT as an xdelta3 patch, verified by applying it, plus out/README.txt."""
    if not os.path.exists(XDELTA) and not shutil.which(XDELTA):
        print(f"xdelta3 not found ({XDELTA}); patch skipped")
        return
    t = time.time()
    if os.path.exists(PATCH):
        os.remove(PATCH)
    subprocess.run([XDELTA, "-e", "-9", "-S", "djw", "-B", str(512 << 20), "-s", ISO, OUT, PATCH], check=True)
    check = os.path.join(ROOT, "work", "patch_check.iso")
    subprocess.run([XDELTA, "-d", "-f", "-s", ISO, PATCH, check], check=True)
    out_sha1 = sha1(OUT)
    ok = sha1(check) == out_sha1
    os.remove(check)
    if not ok:
        raise RuntimeError("the patch does not reproduce the built ISO")
    tpl = open(os.path.join(ROOT, "tools", "patch_readme.txt"), encoding="utf-8").read()
    open(README, "w", encoding="utf-8").write(tpl.replace("{out_sha1}", out_sha1))
    print(f"wrote {PATCH} ({os.path.getsize(PATCH) / 1e6:.1f} MB, verified, sha1 {out_sha1}, {time.time() - t:.0f}s)")


def load(p, d):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else d


def main():
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    tm = load(os.path.join(ROOT, "text", "tm.json"), {})
    repl, report = {}, {}
    for p in sorted(glob.glob(os.path.join(DISC, "fonts", "*", "*_JP.fnt"))):
        name = os.path.basename(p)[:-7]
        if only and name not in only:
            continue
        zh = load(os.path.join(ROOT, "text", "zh", name + ".json"), {})
        entries, tail = fnt.parse(open(p, "rb").read())
        n = 0
        for e in entries:
            if e["text"]:
                t = zh.get(str(e["id"])) or tm.get(e["text"])
                if t:
                    e["text"] = t; n += 1
        rep = {}
        tx, mets = font.build(name, [e["text"] for e in entries], rep)
        base = f"fonts/{name}/{name}_JP"
        repl[base + ".fnt"] = fnt.build(entries, tail)
        repl[base + ".txd"] = tx
        for mn, mb in mets.items():
            repl[f"fonts/{name}/{mn}"] = mb
        rep["translated"] = n
        report[name] = rep
        print(f"{name:10} zh={n:4} chars={rep['chars']:4} drawn={rep['new']:4} pages={rep['pages']}")
    if not only:
        repl["sys/main.dol"] = dolpatch.patch(open(os.path.join(ROOT, "work", "disc", "sys", "main.dol"), "rb").read())
        textures = tex.build()
        repl.update(textures)
        print(f"textures: {len(textures)} files")
    if "--test" in sys.argv:
        for k, v in repl.items():
            q = os.path.join(ROOT, "work", "build", k); os.makedirs(os.path.dirname(q), exist_ok=True)
            open(q, "wb").write(v)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    t = time.time()
    gcm.patch(ISO, OUT, repl)
    json.dump(report, open(os.path.join(ROOT, "work", "build_report.json"), "w"), indent=1)
    print(f"wrote {OUT} ({time.time() - t:.0f}s)")
    if not only and "--no-patch" not in sys.argv:
        make_patch()


if __name__ == "__main__":
    main()

"""Per-file fonts: fonts/<F>/<F>_JP.txd (256x256 C4 pages) + <F>_JPnn.met metrics.

Each .fnt has its own font holding exactly the characters its strings use. The game looks up
a UTF-16 code in the .met files ("code x0 y0 x1 y1 #", inclusive, 24 px rows) and draws that
rectangle of the page with the same index. Pages use palette indices 0/7/8/15 as 4 grey levels.

build(name, strings) -> (txd bytes, {met file name: bytes}):
  characters in the original font keep their original glyph cells; every other character is
  drawn with Noto Sans TC. Glyphs are shelf-packed in order of first use.

    python tools/font.py preview <FILE> <text> [out.png]   draw text with the rebuilt font
"""
import os, re, struct, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import txd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FONTS = os.path.join(ROOT, "work", "disc", "files", "fonts")
NOTO = r"C:/Windows/Fonts/NotoSansTC-VF.ttf"
WEIGHT = 400
SIZE = 23
SS = 4
CELL = 24
PAGE = 256
LEVELS = [(0, 0), (7, 132), (8, 198), (15, 255)]   # palette index, brightness
# every CJK ideograph is redrawn so Chinese text has one look (the Japanese kanji are a
# different design); kana, ASCII and symbols keep their original glyphs
REDRAW = re.compile(r"[㐀-鿿豈-﫿，；：]")
# Taiwanese style: these sit in the middle of the cell, not bottom-left
CENTRED_PUNCT = "，。、；：！？"


def read_original(name):
    """{char: (page image, (x0, y0, x1, y1))}, met header value, raw txd bytes."""
    d = open(os.path.join(FONTS, name, name + "_JP.txd"), "rb").read()
    glyphs = {}
    for t in txd.parse(d):
        px = txd.c4_decode(t.data, t.w, t.h)
        met = open(os.path.join(FONTS, name, t.name + ".met"), encoding="ascii").read().split("\n")
        assert met[0] == "METRICS1"
        for line in met[3:]:
            m = re.match(r"\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", line)
            if m:
                c, x0, y0, x1, y1 = map(int, m.groups())
                cell = bytearray()
                for y in range(y0, y1 + 1):
                    cell += px[y * t.w + x0:y * t.w + x1 + 1]
                glyphs.setdefault(chr(c), (x1 - x0 + 1, y1 - y0 + 1, bytes(cell)))
    return glyphs, d


_fonts = {}
MAX_PAGES = 10          # the game's font object has 10 page slots
# per-file weight: movie subtitles sit on bright CG with no outline, so they get a heavier face
WEIGHTS = {"Movie": 700}


def noto(weight=None):
    weight = weight or WEIGHT
    if weight not in _fonts:
        f = ImageFont.truetype(NOTO, SIZE * SS)
        f.set_variation_by_axes([weight])
        _fonts[weight] = f
    return _fonts[weight]


def quant(v):
    best = min(LEVELS, key=lambda l: abs(l[1] - v))
    return best[0]


def render(ch, weight=None):
    """24x24 cell of palette indices for a full-width character."""
    S = CELL * SS
    im = Image.new("L", (S, S), 0)
    dr = ImageDraw.Draw(im)
    f = noto(weight)
    x0, y0, x1, y1 = dr.textbbox((0, 0), ch, font=f, anchor="ls")
    w = x1 - x0
    asc, desc = f.getmetrics()
    base = (S - (asc + desc)) // 2 + asc - SS          # optical centre of a CJK em box
    if ch in CENTRED_PUNCT:
        h = y1 - y0
        dr.text(((S - w) // 2 - x0, (S - h) // 2 - y0), ch, font=f, fill=255, anchor="ls")
    else:
        dr.text(((S - w) // 2 - x0, base), ch, font=f, fill=255, anchor="ls")
    im = im.resize((CELL, CELL), Image.BOX)
    if ord(ch) < 0x80:   # half-width: keep the advance width, centred
        w = max(4, round(f.getlength(ch) / SS))
        im = im.crop(((CELL - w) // 2, 0, (CELL - w) // 2 + w, CELL))
        return w, CELL, bytes(quant(v) for v in im.tobytes())
    return CELL, CELL, bytes(quant(v) for v in im.tobytes())


def chars_of(strings):
    seen = {}
    for s in strings:
        for ch in s:
            if ch != "\n":
                seen.setdefault(ch, None)
    return list(seen)


def build(name, strings, report=None):
    orig, d = read_original(name)
    tex0 = txd.parse(d)[0]
    glyphs = []
    chars = chars_of(strings)
    pad = int(os.environ.get("FONT_TEST_PAD", 0))   # test only: push real glyphs onto later pages
    if pad:
        chars = [chr(0x4E00 + i) for i in range(pad) if chr(0x4E00 + i) not in chars] + chars
    for ch in chars:
        if ch in orig and not REDRAW.match(ch):
            glyphs.append((ch,) + orig[ch])
        else:
            glyphs.append((ch,) + render(ch, WEIGHTS.get(name)))
    # shelf pack; pages grow taller (256x512, 256x1024) when 10 square pages aren't enough
    for ph in (PAGE, 2 * PAGE, 4 * PAGE):
        pages, x, y = [[]], 0, 0
        for ch, w, h, cell in glyphs:
            if x + w > PAGE:
                x, y = 0, y + CELL
            if y + CELL > ph:
                pages.append([]); x, y = 0, 0
            pages[-1].append((ch, x, y, w, h, cell))
            x += w
        if len(pages) <= MAX_PAGES:
            break
    else:
        raise RuntimeError(f"{name}: {len(glyphs)} glyphs don't fit in {MAX_PAGES} pages")
    mets, datas, names, dims = {}, [], [], {}
    for i, pg in enumerate(pages):
        pname = f"{name}_JP{i:02d}"
        px = bytearray(PAGE * ph)
        lines = ["METRICS1", pname, "5"]
        for ch, x, y, w, h, cell in pg:
            for r in range(h):
                px[(y + r) * PAGE + x:(y + r) * PAGE + x + w] = cell[r * w:(r + 1) * w]
            lines.append(f"{ord(ch):5d} {x:3d} {y:3d} {x + w - 1:3d} {y + h - 1:3d} #")
        mets[pname + ".met"] = ("\n".join(lines) + "\n\n").encode("ascii")
        datas.append(txd.c4_encode(px, PAGE, ph))
        names.append(pname)
        if ph != PAGE:
            dims[pname] = (PAGE, ph)
    if report is not None:
        report.update(chars=len(glyphs), new=sum(1 for g in glyphs if g[0] not in orig or REDRAW.match(g[0])), pages=len(pages), page_h=ph)
    return txd.build_like(d, names, datas, dims), mets


def preview(name, text, out):
    data, mets = build(name, [text])
    pages = {}
    for t in txd.parse(data):
        pages[t.name] = txd.c4_decode(t.data, t.w, t.h)
    rects = {}
    for mn, m in mets.items():
        for line in m.decode().split("\n")[3:]:
            mm = re.match(r"\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", line)
            if mm:
                c, x0, y0, x1, y1 = map(int, mm.groups())
                rects[chr(c)] = (mn[:-4], x0, y0, x1, y1)
    lines = text.split("\n")
    W = max(sum(rects[c][3] - rects[c][1] + 1 for c in l) for l in lines) + 8
    im = Image.new("L", (W, CELL * len(lines) + 8), 40)
    for li, l in enumerate(lines):
        x = 4
        for c in l:
            pn, x0, y0, x1, y1 = rects[c]
            pg = pages[pn]
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    v = pg[yy * PAGE + xx]  # pages are always 256 wide
                    if v:
                        im.putpixel((x + xx - x0, 4 + li * CELL + yy - y0), dict(LEVELS)[v])
            x += x1 - x0 + 1
    im = im.resize((im.width * 3, im.height * 3), Image.NEAREST)
    im.save(out)


if __name__ == "__main__":
    if sys.argv[1] == "preview":
        preview(sys.argv[2], open(sys.argv[3], encoding="utf-8").read().rstrip("\n"),sys.argv[4] if len(sys.argv) > 4 else "work/preview.png")

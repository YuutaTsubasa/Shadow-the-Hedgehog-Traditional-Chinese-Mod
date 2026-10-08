"""Japanese/English text drawn in textures -> Chinese.

Each spec erases the text area of one texture and draws the Chinese with Noto Sans TC, then
maps every pixel back onto the texture's own palette (the palette never changes).

    python tools/tex.py preview      -> work/tex/preview_*.png
build() returns {fst path: bytes} for tools/build.py.
"""
import glob, json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import txd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FILES = os.path.join(ROOT, "work", "disc", "files")
NOTO = r"C:/Windows/Fonts/NotoSansTC-VF.ttf"
SS = 4

STAGES = {
    "0100": "WESTOPOLIS", "0200": "DIGITAL CIRCUIT", "0201": "GLYPHIC CANYON", "0202": "LETHAL HIGHWAY",
    "0300": "CRYPTIC CASTLE", "0301": "PRISON ISLAND", "0302": "CIRCUS PARK", "0400": "CENTRAL CITY",
    "0401": "THE DOOM", "0402": "SKY TROOPS", "0403": "MAD MATRIX", "0404": "DEATH RUINS",
    "0500": "THE ARK", "0501": "AIR FLEET", "0502": "IRON JUNGLE", "0503": "SPACE GADGET",
    "0504": "LOST IMPACT", "0600": "GUN FORTRESS", "0601": "BLACK COMET", "0602": "LAVA SHELTER",
    "0603": "COSMIC FALL", "0604": "FINAL HAUNT", "0700": "THE LAST WAY",
}


def font(px, weight):
    f = ImageFont.truetype(NOTO, px * SS)
    f.set_variation_by_axes([weight])
    return f


def title_text(text, w, h, px=24, weight=900, outline=2, x0=3, track=3):
    """White-to-grey gradient letters with a black outline, left-aligned like the original."""
    W, H = w * SS, h * SS
    f = font(px, weight)
    # draw onto a wide strip char by char (tracking), then squeeze to fit if needed
    strip = Image.new("L", (W * 3, H), 0)
    d = ImageDraw.Draw(strip)
    asc, desc = f.getmetrics()
    x = 0
    for ch in text:
        d.text((x, (H - (asc + desc)) // 2 + asc // 10), ch, font=f, fill=255)
        x += int(f.getlength(ch)) + track * SS
    tw = x - track * SS
    avail = W - 2 * (x0 + outline) * SS
    strip = strip.crop((0, 0, max(tw, 1), H))
    if tw > avail:
        strip = strip.resize((avail, H), Image.LANCZOS)
    mask = Image.new("L", (W, H), 0)
    mask.paste(strip, ((x0 + outline) * SS, 0))
    edge = mask.filter(ImageFilter.MaxFilter(2 * outline * SS + 1))
    grad = Image.new("L", (W, H))
    grad.putdata([255 - int(75 * (y / H)) for y in range(H) for _ in range(W)])
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste((0, 0, 0, 255), (0, 0), edge)
    fill = Image.merge("RGBA", (grad, grad, grad, mask))
    out.alpha_composite(fill)
    return out.resize((w, h), Image.LANCZOS)


def nearest(pal, rgba, trans):
    r, g, b, a = rgba
    if a < 128:
        return trans
    best, bd = 0, 1e9
    for i, (pr, pg, pb, pa) in enumerate(pal):
        if pa < 255:
            continue
        dd = (pr - r) ** 2 + (pg - g) ** 2 + (pb - b) ** 2
        if dd < bd:
            best, bd = i, dd
    return best


def stage_titles(glossary):
    out = {}
    for num, en in STAGES.items():
        path = f"csdFiles/stageTitle/StageTitle{num}_JP.txd"
        d = open(os.path.join(FILES, path), "rb").read()
        new = []
        for t in txd.parse(d):
            if t.name != "stagetitle":
                new.append(None); continue
            pal = txd.palette_rgba(t)
            trans = next(i for i, c in enumerate(pal) if c[3] == 0)
            idx = txd.c4_decode(t.data, t.w, t.h)
            Y0 = 105
            for i in range(Y0 * t.w, t.w * t.h):
                idx[i] = trans
            layer = title_text(glossary[en]["zh"], t.w, t.h - Y0)
            for y in range(layer.height):
                for x in range(layer.width):
                    px = layer.getpixel((x, y))
                    if px[3] >= 128:
                        idx[(Y0 + y) * t.w + x] = nearest(pal, px, trans)
            new.append(txd.c4_encode(idx, t.w, t.h))
        out[path] = txd.replace_data(d, new)
    return out


def build():
    g = json.load(open(os.path.join(ROOT, "text", "glossary.json"), encoding="utf-8"))
    out = stage_titles(g)
    out.update(title_logo())
    out.update(menus(out))
    return out


def preview():
    os.makedirs(os.path.join(ROOT, "work", "tex"), exist_ok=True)
    res = build()
    sheet = Image.new("RGBA", (512, 40 * ((len(res) + 1) // 2)), (40, 40, 90, 255))
    for i, (p, d) in enumerate(sorted(res.items())):
        for t in txd.parse(d):
            if t.name == "stagetitle":
                im = txd.to_image(t).crop((0, 88, 256, 128))
                sheet.alpha_composite(im, ((i % 2) * 256, (i // 2) * 40))
    sheet.save(os.path.join(ROOT, "work", "tex", "preview_stagetitles.png"))


if __name__ == "__main__":
    preview()


def title_logo():
    """「シャドウ・ザ・ヘッジホッグ」 under the logo -> 「刺蝟夏特」 on the same black brush stroke."""
    path = "csdFiles/honban_JP.txd"
    d = open(os.path.join(FILES, path), "rb").read()
    new = []
    for t in txd.parse(d):
        if t.name != "TitleParts":
            new.append(None); continue
        im = txd.to_image(t)
        px = im.load()
        X0, X1, Y0, Y1 = 236, 404, 67, 79
        for y in range(Y0 + 1, Y1):              # repaint the band (katakana and its outline) in the stroke colour
            for x in range(X0, X1 + 1):
                r, g, b, a = px[x, y]
                if a > 0:
                    px[x, y] = (20, 20, 20, a)
        W, H = (X1 - X0) * SS, (Y1 - Y0 + 1) * SS
        f = font(12, 900)
        lay = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(lay)
        text, track = "刺蝟夏特", 4 * SS
        tw = sum(int(f.getlength(c)) for c in text) + track * (len(text) - 1)
        x = (W - tw) // 2
        asc, desc = f.getmetrics()
        for c in text:
            dr.text((x, (H - (asc + desc)) // 2 + SS), c, font=f, fill=255)
            x += int(f.getlength(c)) + track
        lay = lay.resize((X1 - X0, Y1 - Y0 + 1), Image.LANCZOS)
        white = Image.new("RGBA", lay.size, (255, 255, 255, 255))
        base = im.crop((X0, Y0, X1, Y1 + 1))
        base.paste(white, (0, 0), lay)
        im.paste(base, (X0, Y0))
        new.append(txd.rgb5a3_encode(list(im.getdata()), t.w, t.h))
    return {path: txd.replace_data(d, new)}


# ---------------------------------------------------------------- menu labels (paletted textures)
def label(text, w, h, px=None, weight=700, outline=2, align="center"):
    """White text with a black outline, fitted into w x h (squeezed horizontally if too long)."""
    px = px or h - 3
    f = font(px, weight)
    W, H = w * SS, h * SS
    asc, desc = f.getmetrics()
    tw = int(f.getlength(text))
    strip = Image.new("L", (tw + 2 * outline * SS + 8, H), 0)
    ImageDraw.Draw(strip).text((outline * SS + 4, (H - (asc + desc)) // 2 + SS), text, font=f, fill=255)
    if strip.width > W:
        strip = strip.resize((W, H), Image.LANCZOS)
    mask = Image.new("L", (W, H), 0)
    x = {"center": (W - strip.width) // 2, "left": 0, "right": W - strip.width}[align]
    mask.paste(strip, (x, 0))
    edge = mask.filter(ImageFilter.MaxFilter(2 * outline * SS + 1))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste((0, 0, 0, 255), (0, 0), edge)
    out.paste((255, 255, 255, 255), (0, 0), mask)
    return out.resize((w, h), Image.LANCZOS)


def nearest_rgba(pal, c, cache):
    if c in cache:
        return cache[c]
    r, g, b, a = c
    best = min(range(len(pal)), key=lambda i: (pal[i][0] - r) ** 2 + (pal[i][1] - g) ** 2
               + (pal[i][2] - b) ** 2 + 2 * (pal[i][3] - a) ** 2)
    cache[c] = best
    return best


def relabel(d, texname, items):
    """d: txd bytes. items: [((x0, y0, x1, y1), text, align)]; each box (inclusive) is cleared
    and the text drawn in it."""
    new = []
    for t in txd.parse(d):
        if t.name != texname:
            new.append(None); continue
        dec, enc = {8: (txd.c4_decode, txd.c4_encode), 9: (txd.c8_decode, txd.c8_encode)}[t.gx]
        pal = txd.palette_rgba(t)
        idx = dec(t.data, t.w, t.h)
        trans = min(range(len(pal)), key=lambda i: pal[i][3])
        cache = {}
        for (x0, y0, x1, y1), text, align in items:
            w, h = x1 - x0 + 1, y1 - y0 + 1
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    idx[y * t.w + x] = trans
            lay = label(text, w, h, align=align)
            for y in range(h):
                for x in range(w):
                    c = lay.getpixel((x, y))
                    if c[3] >= 40:
                        idx[(y0 + y) * t.w + x0 + x] = nearest_rgba(pal, c, cache)
        new.append(enc(idx, t.w, t.h))
    return txd.replace_data(d, new)


GAMEMENU = [  # the menu-word sheet shared by several screens
    ((60, 0, 196, 19), "1P遊戲", "center"), ((60, 21, 196, 40), "2P遊戲", "center"),
    ((60, 42, 196, 62), "選項", "center"), ((58, 63, 197, 83), "故事模式", "center"),
    ((60, 85, 196, 105), "選擇模式", "center"), ((60, 106, 196, 126), "困難模式", "center"),
    ((60, 128, 196, 147), "從頭開始", "center"), ((60, 149, 196, 169), "從上次繼續", "center"),
    ((0, 210, 40, 229), "確定", "left"), ((0, 231, 40, 253), "返回", "left"),
]
PAUSE_MAIN = [
    ((118, 18, 240, 35), "故事路線", "left"), ((2, 73, 40, 91), "返回", "left"),
    ((8, 103, 100, 123), "從頭開始", "left"), ((24, 130, 90, 151), "結束", "left"),
    ((115, 130, 190, 150), "繼續", "left"),
]
SELECTMODE = [((383, 473, 421, 493), "確定", "left"), ((383, 494, 421, 511), "返回", "left")]
BATTLEMODE = [((172, 72, 267, 97), "三局兩勝", "center"), ((174, 100, 268, 125), "一局決勝", "center")]
GAMEOVER = [((19, 110, 110, 144), "否", "center"), ((161, 110, 223, 145), "是", "center")]
LIBRARY = [  # story mode menu
    ((343, 1, 433, 20), "從頭開始", "center"), ((344, 21, 433, 40), "繼續遊戲", "center"),
    ((335, 41, 442, 61), "資料庫", "center"), ((318, 61, 459, 81), "最終篇", "center"),
    ((264, 156, 301, 175), "確定", "left"), ((264, 176, 301, 195), "返回", "left"),
]
SYNOPSIS = [((0, 0, 81, 17), "開始遊戲", "left")]
SHEETS = (("gamemenu", GAMEMENU), ("pause_main", PAUSE_MAIN), ("selectmode", SELECTMODE),
          ("battlemode", BATTLEMODE), ("gameover", GAMEOVER), ("library", LIBRARY), ("Synopsis", SYNOPSIS))


def menus(base):
    """Relabel every JP texture dictionary holding one of the menu sheets, on top of `base`."""
    out = {}
    for p in sorted(glob.glob(os.path.join(FILES, "csdFiles", "**", "*_JP.txd"), recursive=True)):
        path = os.path.relpath(p, FILES).replace(os.sep, "/")
        d = base.get(path) or open(p, "rb").read()
        names = [t.name for t in txd.parse(d)]
        hit = False
        for tex, items in SHEETS:
            if tex in names:
                d = relabel(d, tex, items); hit = True
        if hit:
            out[path] = d
    return out

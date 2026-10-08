"""RenderWare TXD (GameCube native textures, platform 6) as used by Shadow the Hedgehog fonts.

Chunk tree: 0x16 TexDictionary { 0x01 struct(u16 count, u16 dev), 0x15 TextureNative { 0x01 struct, 0x03 ext } ..., 0x03 ext }.
Chunk headers are little-endian; the native struct body is big-endian:
  u32 platform(6), u32 filter/addressing, 4 x u32 unknown, char name[32], char mask[32],
  u32 raster_format, u16 w, u16 h, u8 depth, u8 levels, u8 gx_format, u8 tlut_format, u32 unknown,
  [palette 2*(1<<depth) bytes when paletted], u32 data_size, pixel data (GX tiled).
Font pages are 256x256 C4 (gx 8) with an RGB565 palette.
"""
import struct


def chunks(d, o, end):
    while o < end:
        t, s, v = struct.unpack_from('<III', d, o)
        yield t, o, s, v
        o += 12 + s


class Tex:
    def __init__(self, d, o):  # o = start of the 0x01 struct body
        self.platform, self.filter = struct.unpack_from('>II', d, o)
        self.unk = d[o + 8:o + 24]
        self.name = d[o + 24:o + 56].rstrip(b'\0').decode()
        self.mask = d[o + 56:o + 88]
        self.rfmt, self.w, self.h, self.depth, self.levels, self.gx, self.tlut, self.unk2 = \
            struct.unpack_from('>IHHBBBBI', d, o + 88)
        p = o + 104
        self.palette = b''
        if self.gx in (8, 9):
            n = 2 * (1 << self.depth)
            self.palette = d[p:p + n]
            p += n
        self.size = struct.unpack_from('>I', d, p)[0]
        self.data = d[p + 4:p + 4 + self.size]
        self.after = None


def parse(d):
    """Return (textures, raw) with each texture's location so it can be rewritten in place."""
    texs = []
    t, o, s, v = next(chunks(d, 0, len(d)))
    assert t == 0x16
    for t2, o2, s2, v2 in chunks(d, o + 12, o + 12 + s):
        if t2 == 0x15:
            t3, o3, s3, v3 = next(chunks(d, o2 + 12, o2 + 12 + s2))
            x = Tex(d, o3 + 12)
            x.data_off = o3 + 12 + (s3 - x.size)
            texs.append(x)
    return texs


def c4_decode(data, w, h):
    px = bytearray(w * h)
    i = 0
    for by in range(0, h, 8):
        for bx in range(0, w, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    b = data[i]; i += 1
                    px[(by + y) * w + bx + x] = b >> 4
                    px[(by + y) * w + bx + x + 1] = b & 15
    return px


def c4_encode(px, w, h):
    out = bytearray()
    for by in range(0, h, 8):
        for bx in range(0, w, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(px[(by + y) * w + bx + x] << 4 | px[(by + y) * w + bx + x + 1])
    return bytes(out)


def replace_data(d, texs_new):
    """d with each texture's pixel data replaced (same size); texs_new = list of bytes or None."""
    b = bytearray(d)
    for x, nd in zip(parse(d), texs_new):
        if nd is not None:
            assert len(nd) == x.size
            b[x.data_off:x.data_off + x.size] = nd
    return bytes(b)


def build_like(d, names, datas, dims=None):
    """A texture dictionary shaped like d (same chunk versions, header fields and palette as its
    first texture) holding one texture per (name, pixel data)."""
    t, o, s, ver = next(chunks(d, 0, len(d)))
    kids = list(chunks(d, o + 12, o + 12 + s))
    st = next(k for k in kids if k[0] == 0x01)
    tn = next(k for k in kids if k[0] == 0x15)
    ext = [k for k in kids if k[0] == 0x03][-1]
    tn_raw = d[tn[1]:tn[1] + 12 + tn[2]]
    t3, o3, s3, v3 = next(chunks(tn_raw, 12, len(tn_raw)))
    body0 = tn_raw[o3 + 12:o3 + 12 + s3]
    rest = tn_raw[o3 + 12 + s3:]                     # the texture's extension chunk
    x = Tex(d, tn[1] + 12 + 12)
    data_at = s3 - x.size
    out = bytearray()
    for name, data in zip(names, datas):
        hdr = bytearray(body0[56:data_at])
        if dims and name in dims:                   # (w, h): a smaller page, same format
            w, h = dims[name]
            struct.pack_into(">HH", hdr, 88 + 4 - 56, w, h)
            struct.pack_into(">I", hdr, len(hdr) - 4, len(data))
        else:
            assert len(data) == x.size
        nb = name.encode().ljust(32, b"\0")
        body = body0[:24] + nb + bytes(hdr) + data
        inner = struct.pack("<III", 0x01, len(body), v3) + body + rest
        out += struct.pack("<III", 0x15, len(inner), tn[3]) + inner
    stb = bytearray(d[st[1] + 12:st[1] + 12 + st[2]])
    struct.pack_into("<H", stb, 0, len(names))
    head = struct.pack("<III", 0x01, len(stb), st[3]) + stb
    tail = d[ext[1]:ext[1] + 12 + ext[2]]
    inner = head + bytes(out) + tail
    return struct.pack("<III", 0x16, len(inner), ver) + inner


# ---------------------------------------------------------------- colour textures
def _rgb565(v):
    return ((v >> 11) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31, 255)


def _rgb5a3(v):
    if v & 0x8000:
        return (((v >> 10) & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, (v & 31) * 255 // 31, 255)
    return (((v >> 8) & 15) * 17, ((v >> 4) & 15) * 17, (v & 15) * 17, ((v >> 12) & 7) * 255 // 7)


def _ia8(v):
    return (v & 255, v & 255, v & 255, v >> 8)


TLUT = {0: _ia8, 1: _rgb565, 2: _rgb5a3}


def palette_rgba(t):
    f = TLUT[t.tlut]
    n = len(t.palette) // 2
    return [f(struct.unpack_from(">H", t.palette, 2 * i)[0]) for i in range(n)]


def c8_decode(data, w, h):
    px = bytearray(w * h); i = 0
    for by in range(0, h, 4):
        for bx in range(0, w, 8):
            for y in range(4):
                for x in range(8):
                    if by + y < h and bx + x < w:
                        px[(by + y) * w + bx + x] = data[i]
                    i += 1
    return px


def c8_encode(px, w, h):
    out = bytearray()
    for by in range(0, h, 4):
        for bx in range(0, w, 8):
            for y in range(4):
                for x in range(8):
                    out.append(px[(by + y) * w + bx + x])
    return bytes(out)


def rgb5a3_decode(data, w, h):
    px = [None] * (w * h); i = 0
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            for y in range(4):
                for x in range(4):
                    px[(by + y) * w + bx + x] = _rgb5a3(struct.unpack_from(">H", data, i)[0]); i += 2
    return px


def to_image(t):
    """PIL RGBA image of the first mip level."""
    from PIL import Image
    w, h = t.w, t.h
    if t.gx == 8:
        pal = palette_rgba(t); idx = c4_decode(t.data, w, h); px = [pal[i] for i in idx]
    elif t.gx == 9:
        pal = palette_rgba(t); idx = c8_decode(t.data, w, h); px = [pal[i] for i in idx]
    elif t.gx == 5:
        px = rgb5a3_decode(t.data, w, h)
    else:
        raise ValueError(f"gx format {t.gx}")
    im = Image.new("RGBA", (w, h)); im.putdata(px)
    return im


def _rgb5a3_enc(r, g, b, a):
    if a >= 0xE0:
        return 0x8000 | (r >> 3) << 10 | (g >> 3) << 5 | (b >> 3)
    return (a >> 5) << 12 | (r >> 4) << 8 | (g >> 4) << 4 | (b >> 4)


def rgb5a3_encode(px, w, h):
    """px: list of (r, g, b, a) in raster order."""
    out = bytearray()
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            for y in range(4):
                for x in range(4):
                    out += struct.pack(">H", _rgb5a3_enc(*px[(by + y) * w + bx + x]))
    return bytes(out)

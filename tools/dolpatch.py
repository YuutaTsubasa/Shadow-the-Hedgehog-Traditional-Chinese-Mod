"""main.dol patch: let the game see files that its built-in file list doesn't name.

Before opening a file the game checks a hard-coded list of the disc's file names
(0x8053ebb8, bucketed by first letter, at 0x801e2a??). Files this mod adds (extra font
pages fonts/<F>/<F>_JPnn.met) are not in it, so the game stopped at the original page count.
The patch makes a failed lookup fall back to the real FST: DVDConvertPathToEntrynum(path) >= 0.
The few instructions live in zero padding of text section 0.
"""
import struct

DVD_PATH_TO_ENTRY = 0x80379f98
NOT_FOUND = (0x801e2b00, 0x801e2b48)      # "li r3, 0" before the common epilogue
EPILOGUE = 0x801e2b4c
CAVE = 0x80003e40


def sections(d):
    offs = struct.unpack_from(">18I", d, 0)
    addr = struct.unpack_from(">18I", d, 0x48)
    size = struct.unpack_from(">18I", d, 0x90)
    return offs, addr, size


def a2o(d, a):
    offs, addr, size = sections(d)
    for i in range(18):
        if size[i] and addr[i] <= a < addr[i] + size[i]:
            return offs[i] + a - addr[i]
    raise ValueError(hex(a))


def b(frm, to, link=False):
    return 0x48000000 | ((to - frm) & 0x3FFFFFC) | int(link)


def patch(d):
    d = bytearray(d)
    code = [
        0x38610008,                                  # addi r3, r1, 8   (upper-cased path)
        b(CAVE + 4, DVD_PATH_TO_ENTRY, True),        # bl DVDConvertPathToEntrynum
        0x7C6318F8,                                  # not r3, r3
        0x54630FFE,                                  # srwi r3, r3, 31  -> 1 if entry >= 0
        b(CAVE + 16, EPILOGUE),                      # b epilogue
    ]
    o = a2o(d, CAVE)
    assert d[o:o + 4 * len(code)] == bytes(4 * len(code)), "cave not empty"
    for i, w in enumerate(code):
        struct.pack_into(">I", d, o + 4 * i, w)
    for a in NOT_FOUND:
        o = a2o(d, a)
        assert struct.unpack_from(">I", d, o)[0] == 0x38600000, hex(a)   # li r3, 0
        struct.pack_into(">I", d, o, b(a, CAVE))
    return patch_strings(bytes(d))


# Japanese strings the game draws with the console's Shift-JIS ROM font (memory-card comment,
# disc errors, progressive-scan prompt). Traditional Chinese is used only where the character
# exists in Shift-JIS (碟/說/閱/嗎 don't: 遊戲片, 使用手冊, 是否…？ instead).
STRINGS = {
    0x4f8fcc: "刺蝟夏特",            # memory card comment line 1
    0x4f8fe8: "遊戲資料",            # memory card comment line 2
    0x50bda3: "\x02主機上蓋是開著的。\n若要繼續遊戲，\n請蓋上主機上蓋。",
    0x50be18: "請放入「刺蝟夏特」\n的遊戲片。",
    0x50be8c: "無法讀取遊戲片。\n詳情請參考主機的使用手冊。",
    0x50bef4: "發生錯誤。\n請按下主機的電源按鈕關閉電源，\n並依照主機使用手冊的指示處理。",
    0x50cfc0: "是否以逐行掃描模式顯示？",
    0x50d014: "畫面顯示模式\n已設定為逐行掃描模式。",
    0x50d078: "畫面顯示模式\n已設定為交錯掃描模式。",
    0x55ef60: "B\n\n請按下主機的電源按鈕關閉電源，\n並依照主機使用手冊的指示處理。",
    0x57f6fc: "是",
    0x57f710: "否",
}


def patch_strings(d):
    d = bytearray(d)
    for off, text in STRINGS.items():
        end = d.index(b"\0", off)
        slot = end
        while d[slot] == 0:
            slot += 1
        b = text.encode("cp932")                     # raises if a character isn't in Shift-JIS
        assert len(b) < slot - off, (hex(off), len(b), slot - off)
        d[off:slot] = b + bytes(slot - off - len(b))
    return bytes(d)

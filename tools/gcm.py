"""GameCube disc image (GCM/ISO): parse/rebuild the FST and patch files into a copy of the image.

A replacement that fits in its file's slot (up to the next file's start) is written in place;
a larger one, or a new file, goes into free space after the last file. The FST is rebuilt
(new files inserted in name order) and must fit before the first file; boot.bin's FST size
fields are updated. With no changes the FST rebuilds byte-identically (`python gcm.py check`).
"""
import shutil, struct

ALIGN = 0x8000
DISC_SIZE = 1459978240


class Node:
    def __init__(self, name, is_dir, off=0, size=0):
        self.name, self.is_dir, self.off, self.size = name, is_dir, off, size
        self.kids = []


def parse_fst(fst):
    n = struct.unpack_from(">I", fst, 8)[0]
    strtab = 12 * n

    def name(i):
        o = strtab + (struct.unpack_from(">I", fst, 12 * i)[0] & 0xFFFFFF)
        return fst[o:fst.index(b"\0", o)].decode("cp932")

    def walk(node, start, end):
        i = start
        while i < end:
            w0, a, b = struct.unpack_from(">III", fst, 12 * i)
            if w0 >> 24:
                d = Node(name(i), True); node.kids.append(d)
                walk(d, i + 1, b); i = b
            else:
                node.kids.append(Node(name(i), False, a, b)); i += 1

    root = Node("", True)
    walk(root, 1, n)
    return root


def build_fst(root):
    ents, names = [], bytearray()

    def walk(node, parent):
        for k in node.kids:
            idx = len(ents)
            no = len(names); names.extend(k.name.encode("cp932") + b"\0")
            if k.is_dir:
                ents.append([1, no, parent, 0])
                walk(k, idx)
                ents[idx][3] = len(ents)
            else:
                ents.append([0, no, k.off, k.size])

    ents.append([1, 0, 0, 0])
    walk(root, 0)
    ents[0][3] = len(ents)
    out = bytearray()
    for t, no, a, b in ents:
        out += struct.pack(">III", t << 24 | no, a, b)
    return bytes(out + names)


def files_of(root, prefix=""):
    for k in root.kids:
        if k.is_dir:
            yield from files_of(k, prefix + k.name + "/")
        else:
            yield prefix + k.name, k


def read(f):
    f.seek(0x424)
    fst_off, fst_size = struct.unpack(">II", f.read(8))
    f.seek(fst_off)
    fst = f.read(fst_size)
    return fst_off, fst, parse_fst(fst)


def lookup(root, path, create=False):
    node = root
    parts = path.split("/")
    for i, p in enumerate(parts):
        k = next((k for k in node.kids if k.name.lower() == p.lower()), None)
        if k is None:
            if not create:
                raise KeyError(path)
            k = Node(p, i < len(parts) - 1)
            node.kids.append(k)
            node.kids.sort(key=lambda x: x.name.lower())
        node = k
    return node


def patch(src, dst, repl):
    """repl: {fst path: bytes}. Copies src to dst and patches (adds files that don't exist)."""
    shutil.copyfile(src, dst)
    with open(dst, "r+b") as f:
        fst_off, fst, root = read(f)
        allf = dict(files_of(root))
        starts = sorted(n.off for n in allf.values())
        first = starts[0]
        free = max(n.off + n.size for n in allf.values())
        free = (free + ALIGN - 1) // ALIGN * ALIGN
        for path, data in repl.items():
            if path == "sys/main.dol":              # boot DOL, patched in place (same size)
                f.seek(0x420); dol_off = struct.unpack(">I", f.read(4))[0]
                f.seek(dol_off); assert len(f.read(len(data))) == len(data)
                f.seek(dol_off); f.write(data)
                continue
            node = lookup(root, path, create=True)
            off, size = node.off, node.size
            nxt = next((s for s in starts if s > off), DISC_SIZE) if off else 0
            if off and len(data) <= nxt - off:
                at = off
            else:
                at = free
                free = (free + len(data) + ALIGN - 1) // ALIGN * ALIGN
                if free > DISC_SIZE:
                    raise RuntimeError("disc full")
            f.seek(at); f.write(data)
            if at == off and len(data) < size:
                f.write(b"\0" * (size - len(data)))
            node.off, node.size = at, len(data)
        nf = build_fst(root)
        if fst_off + len(nf) > first:
            raise RuntimeError("FST does not fit before the first file")
        f.seek(fst_off); f.write(nf)
        if len(nf) < len(fst):
            f.write(b"\0" * (len(fst) - len(nf)))
        f.seek(0x428); f.write(struct.pack(">II", len(nf), len(nf)))


if __name__ == "__main__":
    import sys
    with open(sys.argv[2] if len(sys.argv) > 2 else sys.argv[1], "rb") as f:
        fst_off, fst, root = read(f)
    allf = dict(files_of(root))
    end = max(n.off + n.size for n in allf.values())
    print(len(allf), "files; free", DISC_SIZE - end, "; FST round trip", build_fst(root) == fst)

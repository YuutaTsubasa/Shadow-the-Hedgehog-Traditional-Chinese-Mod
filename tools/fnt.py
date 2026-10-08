"""Shadow the Hedgehog (GameCube, GUPJ8P) .fnt message tables.

Little-endian: u32 count, then count x 20-byte entries
  (u32 text_off, u32 msg_id, u32 kind, i32 frames, i32 audio_id),
then the UTF-16LE NUL-terminated strings. Anything after the last string (the JP files
carry leftover data from the English build) is kept verbatim as `tail`.
"""
import struct


def parse(data: bytes):
    n = struct.unpack_from('<I', data, 0)[0]
    entries = []
    end = 4 + 20 * n
    for i in range(n):
        off, mid, kind, frames, audio = struct.unpack_from('<IIIii', data, 4 + 20 * i)
        e = off
        while data[e:e + 2] != b'\0\0':
            e += 2
        entries.append({'off': off, 'id': mid, 'kind': kind, 'frames': frames, 'audio': audio,
                        'text': data[off:e].decode('utf-16-le')})
        end = max(end, e + 2)
    return entries, data[end:]


def build(entries, tail=b''):
    n = len(entries)
    head = bytearray(struct.pack('<I', n))
    body = bytearray()
    base = 4 + 20 * n
    for e in entries:
        head += struct.pack('<IIIii', base + len(body), e['id'], e['kind'], e['frames'], e['audio'])
        body += e['text'].encode('utf-16-le') + b'\0\0'
    return bytes(head + body + tail)

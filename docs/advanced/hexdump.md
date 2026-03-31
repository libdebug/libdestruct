# Hex Dump

Every libdestruct object has a `hexdump()` method that returns a classic hex dump of its serialized bytes.

## Basic Usage

```python
from libdestruct import c_int, inflater

memory = bytearray(b"Hello, World!\x00\x00\x00")
lib = inflater(memory)
x = lib.inflate(c_int, 0)
print(x.hexdump())
```

Output format:

```
00000000  48 65 6c 6c                                       |Hell|
```

Each line shows: offset, hex bytes (up to 16 per line), and ASCII representation (non-printable bytes shown as `.`).

## Struct Hex Dump

When called on a struct, `hexdump()` annotates each line with the field names that start on that line:

```python
from libdestruct import struct, c_int, c_long

class player_t(struct):
    health: c_int
    score: c_long

memory = bytearray(12)
memory[0:4] = (100).to_bytes(4, "little")
memory[4:12] = (9999).to_bytes(8, "little")

player = player_t.from_bytes(memory)
print(player.hexdump())
```

Output:

```
00000000  64 00 00 00 0f 27 00 00 00 00 00 00               |d....'......|  health, score
```

## Standalone Utility

The underlying `format_hexdump` function can be used directly:

```python
from libdestruct.common.hexdump import format_hexdump

print(format_hexdump(b"\xde\xad\xbe\xef", base_address=0x1000))
```

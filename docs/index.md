# libdestruct

**Native structs made Pythonic.**

libdestruct lets you define C-like data structures in Python and inflate them directly from raw memory. It is designed for reverse engineering, binary analysis, and debugger scripting — anywhere you need to make sense of packed binary data without writing boilerplate.

## Quick Start

### Installation

```bash
pip install libdestruct
```

Or build from source:

```bash
git clone https://github.com/mrindeciso/libdestruct.git
cd libdestruct
pip install .
```

### Your First Struct

Define a C struct in Python, then inflate it from raw bytes:

```python
from libdestruct import struct, c_int, c_long, inflater

class player_t(struct):
    health: c_int
    score: c_long

# Some memory (e.g., from a debugger, a binary file, a network packet)
memory = bytearray(b"\x64\x00\x00\x00\x39\x05\x00\x00\x00\x00\x00\x00")

lib = inflater(memory)
player = lib.inflate(player_t, 0)

print(player.health.value)  # 100
print(player.score.value)   # 1337
```

### From Raw Bytes

If you just have a `bytes` object and want to quickly inspect it:

```python
player = player_t.from_bytes(memory)
print(player.health.value)  # 100
```

### Parse a C Definition

You can skip the Python definition entirely and parse a C struct directly:

```python
from libdestruct.c.struct_parser import definition_to_type

player_t = definition_to_type("""
    struct player_t {
        int health;
        long score;
    };
""")

player = player_t.from_bytes(memory)
print(player.health.value)  # 100
```

## Features

- **Pythonic API** — define structs with type annotations, access fields as attributes
- **C type system** — `c_int`, `c_uint`, `c_long`, `c_ulong`, `c_char`, `c_str`
- **Pointers** — typed pointers with `ptr`, automatic dereferencing with `unwrap()`
- **Arrays** — fixed-size arrays with `array_of()`
- **Enums** — map integer values to Python `Enum` types
- **Nested structs** — compose structs within structs
- **Self-referential types** — forward references via `ptr["TypeName"]`
- **C struct parser** — parse C struct definitions directly with `definition_to_type()`
- **Freeze & diff** — snapshot values and track changes
- **Mutable memory** — write values back to `bytearray`-backed memory

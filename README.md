# libdestruct

**Native structs made Pythonic.**

libdestruct is a Python library for defining C-like data structures and inflating them directly from raw memory. It is designed for reverse engineering, binary analysis, and debugger scripting — anywhere you need to make sense of packed binary data without writing boilerplate.

With libdestruct you can:
- Define C structs using Python type annotations
- Read and write typed values from raw memory buffers
- Follow pointers, including self-referential types (linked lists, trees)
- Work with arrays, enums, and nested structs
- Parse C struct definitions directly from source
- Snapshot values and track changes with freeze/diff/reset

## Installation

```bash
pip install git+https://github.com/mrindeciso/libdestruct.git
```

## Your first script

```python
from libdestruct import struct, c_int, c_long, inflater

class player_t(struct):
    health: c_int
    score: c_long

memory = bytearray(b"\x64\x00\x00\x00\x39\x05\x00\x00\x00\x00\x00\x00")

lib = inflater(memory)
player = lib.inflate(player_t, 0)

print(player.health.value)  # 100
print(player.score.value)   # 1337

# Write a new value back to memory
player.health.value = 200
print(player.health.value)  # 200
```

You can also skip the Python definition and parse C directly:

```python
from libdestruct.c.struct_parser import definition_to_type

player_t = definition_to_type("""
    struct player_t {
        int health;
        long score;
    };
""")

player = player_t.from_bytes(b"\x64\x00\x00\x00\x39\x05\x00\x00\x00\x00\x00\x00")
print(player.health.value)  # 100
```

## Project Links

Documentation: [docs/](docs/)

## License

libdestruct is licensed under the [MIT License](LICENSE).

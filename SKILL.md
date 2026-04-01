# libdestruct Skills

libdestruct is a Python library for destructuring binary data into typed objects. It maps raw bytes to C-like types (integers, floats, strings, structs, pointers, arrays, enums, bitfields) with read/write support.

## Installation

```bash
pip install git+https://github.com/mrindeciso/libdestruct.git
```

## Core Concepts

All types inherit from `obj`. Every `obj` has:
- `.value` property to read/write the underlying data
- `.address` property for the memory offset
- `.to_bytes()` to serialize back to bytes
- `.freeze()` / `.diff()` / `.reset()` for snapshotting
- `.hexdump()` for a hex dump of the object's bytes
- `.from_bytes(data)` class method to create a read-only instance from raw bytes

Memory is accessed through an `inflater`, which wraps a `bytes` or `bytearray` buffer. Use `bytearray` for read/write access.

## Quick Reference

### Imports

```python
from typing import Annotated
from libdestruct import (
    inflater,          # memory wrapper
    struct,            # struct base class
    c_int, c_uint,     # 32-bit integers (signed/unsigned)
    c_long, c_ulong,   # 64-bit integers (signed/unsigned)
    c_float, c_double, # IEEE 754 floats (32/64-bit)
    c_str,             # null-terminated C string
    ptr,               # 8-byte pointer
    ptr_to,            # typed pointer field descriptor (legacy)
    ptr_to_self,       # self-referential pointer field descriptor (legacy)
    array, array_of,   # array type + field descriptor
    enum, enum_of,     # enum type + field descriptor
    bitfield_of,       # bitfield descriptor
    union,             # union annotation type
    union_of,          # plain union field descriptor
    tagged_union,      # tagged union field descriptor
    offset,            # explicit field offset
    size_of,           # get size in bytes of any type/instance/field
    alignment_of,      # get natural alignment of any type/instance
)
```

### Type Sizes

| Type | Size (bytes) |
|---|---|
| `c_int` / `c_uint` | 4 |
| `c_long` / `c_ulong` | 8 |
| `c_float` | 4 |
| `c_double` | 8 |
| `ptr` | 8 |
| `c_str` | variable (reads until null) |

### Reading Primitives from a Buffer

```python
memory = bytearray(b"\x2a\x00\x00\x00\x00\x00\x00\x00")
lib = inflater(memory)

x = lib.inflate(c_int, 0)    # inflate c_int at offset 0
print(x.value)                # 42

y = lib.inflate(c_long, 0)   # inflate c_long at offset 0
print(y.value)
```

### Reading Primitives from Raw Bytes

```python
x = c_int.from_bytes(b"\x2a\x00\x00\x00")
print(x.value)  # 42
# Note: from_bytes returns a frozen (read-only) object
```

### Writing Primitives

```python
memory = bytearray(4)
lib = inflater(memory)
x = lib.inflate(c_int, 0)
x.value = -1
print(memory)  # bytearray(b'\xff\xff\xff\xff')
```

### Defining Structs

```python
class player_t(struct):
    health: c_int
    score: c_uint
    position_x: c_float
    position_y: c_float
```

Struct fields are laid out sequentially. Access members as attributes; each returns a typed `obj` (use `.value` to get the Python value).

### Inflating Structs

```python
import struct as pystruct

memory = bytearray(16)
memory[0:4] = pystruct.pack("<i", 100)
memory[4:8] = pystruct.pack("<I", 5000)
memory[8:12] = pystruct.pack("<f", 1.5)
memory[12:16] = pystruct.pack("<f", -3.0)

lib = inflater(memory)
player = lib.inflate(player_t, 0)

print(player.health.value)      # 100
print(player.score.value)       # 5000
print(player.position_x.value)  # 1.5
```

Or from raw bytes (read-only):

```python
player = player_t.from_bytes(memory)
```

### Pointers

```python
class node_t(struct):
    value: c_int
    next: ptr["node_t"]       # pointer to own type (forward ref)

# Typed pointer to another type:
class container_t(struct):
    data: c_int
    ref: ptr[c_long]          # subscript syntax (preferred)
```

Legacy syntax with `ptr_to()` and `ptr_to_self()` is still supported:

```python
class node_t(struct):
    value: c_int
    next: ptr = ptr_to_self()

class container_t(struct):
    data: c_int
    ref: ptr = ptr_to(c_long)
```

Dereference with `.unwrap()` or safe `.try_unwrap()` (returns `None` if invalid):

```python
node = lib.inflate(node_t, 0)
print(node.value.value)
next_node = node.next.unwrap()       # follow pointer
maybe_node = node.next.try_unwrap()  # None if invalid
```

Pointer arithmetic (C-style, scaled by element size):

```python
p = lib.inflate(ptr, 0)
p.wrapper = c_int
print(p[0].value)           # element at index 0
print(p[1].value)           # element at index 1
print((p + 2).unwrap().value)  # element at index 2
```

Pointer results are cached; call `.invalidate()` after memory changes.

### Forward References

For mutually referential structs, use `ptr["TypeName"]`:

```python
class tree_t(struct):
    value: c_int
    left: ptr["tree_t"]
    right: ptr["tree_t"]
```

### Arrays

```python
class packet_t(struct):
    length: c_int
    data: array[c_int, 8]     # subscript syntax (preferred)
```

Legacy syntax with `array_of()` is still supported:

```python
class packet_t(struct):
    length: c_int
    data: array = array_of(c_int, 8)
```

Access array elements:

```python
pkt = lib.inflate(packet_t, 0)
print(pkt.data[0].value)       # first element
print(pkt.data.count())        # 8
for element in pkt.data:
    print(element.value)
```

### Enums

```python
from enum import IntEnum

class Color(IntEnum):
    RED = 0
    GREEN = 1
    BLUE = 2

class pixel_t(struct):
    color: enum[Color]        # subscript syntax (preferred, defaults to c_int backing)
    alpha: c_int

# With a custom backing type:
class pixel_t(struct):
    color: enum[Color, c_short]  # 2-byte backing type
    alpha: c_int
```

Legacy syntax with `enum_of()` is still supported:

```python
class pixel_t(struct):
    color: enum = enum_of(Color)
    alpha: c_int
```

```python
pixel = lib.inflate(pixel_t, 0)
print(pixel.color.value)  # Color.RED
```

### Bitfields

```python
class flags_t(struct):
    read: c_int = bitfield_of(c_int, 1)
    write: c_int = bitfield_of(c_int, 1)
    execute: c_int = bitfield_of(c_int, 1)
    reserved: c_int = bitfield_of(c_int, 29)
```

Consecutive bitfields with the same backing type are packed together. The struct above is 4 bytes total, not 16.

### Unions

```python
from libdestruct.common.union import union, union_of, tagged_union

# Plain union — all variants overlaid at the same offset
class packet_t(struct):
    data: union = union_of({"i": c_int, "f": c_float, "l": c_long})

pkt = lib.inflate(packet_t, 0)
pkt.data.i.value  # interpret as int
pkt.data.f.value  # interpret as float (same bytes)

# Tagged union — discriminator selects the active variant
class message_t(struct):
    type: c_int
    payload: union = tagged_union("type", {
        0: c_int,
        1: c_float,
        2: point_t,  # struct variants work too
    })
```

The discriminator field must appear before the union. The union size is the max of all variant sizes. Struct variant fields are accessible directly: `msg.payload.x.value`. Use `.variant` to get the raw variant object. Unknown discriminator values raise `ValueError`.

### Struct Alignment

```python
# Default: packed (no padding)
class packed_t(struct):
    a: c_char
    b: c_int
# size: 5

# Aligned: natural C alignment with padding
class aligned_t(struct):
    _aligned_ = True
    a: c_char
    b: c_int
# size: 8 (1 + 3 padding + 4)

alignment_of(c_int)       # 4
alignment_of(aligned_t)   # 4 (max member alignment)

# Custom alignment width
class wide_t(struct):
    _aligned_ = 16
    a: c_int
# size: 16, alignment: 16
```

### Explicit Field Offsets

```python
from typing import Annotated

class sparse_t(struct):
    a: c_int
    b: Annotated[c_int, offset(0x10)]  # Annotated syntax (preferred)
```

This works with any type, including subscript types:

```python
class example_t(struct):
    a: c_int
    data: Annotated[array[c_int, 4], offset(0x10)]
    ref: Annotated[ptr[c_int], offset(0x20)]
```

Legacy syntax with default values is still supported:

```python
class sparse_t(struct):
    a: c_int
    b: c_int = offset(0x10)
```

### Nested Structs

```python
class vec2(struct):
    x: c_float
    y: c_float

class entity_t(struct):
    id: c_int
    pos: vec2
```

```python
e = lib.inflate(entity_t, 0)
print(e.pos.x.value)
```

### size_of

```python
size_of(c_int)             # 4
size_of(c_long)            # 8
size_of(player_t)          # computed from fields
size_of(array_of(c_int, 10))  # 40
size_of(some_instance)     # works on instances too
```

### Hex Dump

```python
player = lib.inflate(player_t, 0)
print(player.hexdump())
# 00000000  64 00 00 00 88 13 00 00 00 00 c0 3f 00 00 40 c0  |d..........?..@.|  health, score, position_x, position_y
```

Struct hexdumps annotate lines with field names. Primitive hexdumps show raw bytes.

### Dict / JSON Export

```python
point = point_t.from_bytes(memory)
point.to_dict()  # {"x": 10, "y": 20}

import json
json.dumps(entity.to_dict())  # nested structs produce nested dicts
```

`to_dict()` works on all types: primitives return their value, structs return `{name: value}` dicts, arrays return lists, unions return variant values, enums return their int value.

### Freeze / Diff / Reset

```python
x = lib.inflate(c_int, 0)
x.freeze()           # snapshot current value
x.value = 99         # raises ValueError (frozen)

# For non-frozen objects:
x.freeze()           # save state
# ... memory changes externally ...
print(x.diff())      # (old_value, new_value)
x.reset()            # restore to frozen value
x.update()           # update frozen value to current
```

### C Struct Parser

Parse C struct definitions directly (requires `pycparser`):

```python
from libdestruct.c.struct_parser import definition_to_type

player_t = definition_to_type("""
    struct player_t {
        int health;
        unsigned int score;
        float x;
        double y;
    };
""")

player = player_t.from_bytes(data)
```

Supports: nested structs, pointers (including self-referential), arrays, bitfields, typedefs, `#include` directives (requires a C preprocessor), and `__attribute__` stripping.

## Common Patterns

### Parsing a binary format

```python
class header_t(struct):
    magic: c_uint
    version: c_int
    num_entries: c_int
    entries_ptr: ptr[entry_t]

with open("file.bin", "rb") as f:
    data = bytearray(f.read())

lib = inflater(data)
header = lib.inflate(header_t, 0)

for i in range(header.num_entries.value):
    entry = header.entries_ptr[i]
    # process entry...
```

### Modifying binary data in-place

```python
data = bytearray(open("save.bin", "rb").read())
lib = inflater(data)
player = lib.inflate(player_t, 0x100)
player.health.value = 999
open("save.bin", "wb").write(data)
```

### Working with libdebug

libdestruct integrates with [libdebug](https://github.com/libdebug/libdebug) for live process memory inspection. The debugger's memory view can be passed directly to `inflater`.

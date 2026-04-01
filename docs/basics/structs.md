# Structs

Structs are the core building block for describing binary layouts. Define a struct by subclassing `struct` and using type annotations:

```python
from libdestruct import struct, c_int, c_long

class header_t(struct):
    magic: c_int
    version: c_int
    size: c_long
```

## Inflating a Struct

```python
from libdestruct import inflater

memory = bytearray(16)
lib = inflater(memory)
header = lib.inflate(header_t, 0)

print(header.magic.value)    # 0
print(header.version.value)  # 0
print(header.size.value)     # 0
```

Or directly from bytes:

```python
data = b"\xef\xbe\xad\xde" + b"\x01\x00\x00\x00" + b"\x00\x10\x00\x00\x00\x00\x00\x00"
header = header_t.from_bytes(data)
print(f"magic: 0x{header.magic.value:08x}")  # magic: 0xdeadbeef
print(f"version: {header.version.value}")     # version: 1
print(f"size: {header.size.value}")           # size: 4096
```

## Accessing Members

Each struct field is an `obj` instance. Use `.value` to read or write the underlying value:

```python
header.magic.value = 0xcafebabe
print(f"0x{header.magic.value:08x}")  # 0xcafebabe
```

## Nested Structs

Structs can contain other structs:

```python
class point_t(struct):
    x: c_int
    y: c_int

class rect_t(struct):
    origin: point_t
    size: point_t
```

Access nested fields naturally:

```python
data = b"\x00" * 16
rect = rect_t.from_bytes(data)
print(rect.origin.x.value)  # 0
print(rect.size.y.value)    # 0
```

## Serialization

Serialize a struct to bytes with `to_bytes()` or `bytes()`:

```python
raw = header.to_bytes()
# or equivalently
raw = bytes(header)
```

## String Representation

Use `to_str()` for a formatted, human-readable view:

```python
print(header.to_str())
# header_t {
#     magic: 3405691582,
#     version: 1,
#     size: 4096
# }
```

`repr()` includes address and size information:

```python
print(repr(header))
# header_t {
#     address: 0x0,
#     size: 0x10,
#     members: {
#         magic: 3405691582,
#         ...
#     }
# }
```

## Dict / JSON Export

Use `to_dict()` to get a JSON-serializable dictionary of field names to values:

```python
header = header_t.from_bytes(data)
print(header.to_dict())
# {"magic": 3735928559, "version": 1, "size": 4096}
```

Nested structs produce nested dicts, arrays become lists:

```python
import json

rect = rect_t.from_bytes(data)
print(json.dumps(rect.to_dict(), indent=2))
# {
#   "origin": {"x": 0, "y": 0},
#   "size": {"x": 0, "y": 0}
# }
```

`to_dict()` also works on individual fields — primitives return their Python value, enums return their integer value.

## Equality

Two struct instances are equal if they have the same members with the same values:

```python
a = header_t.from_bytes(data)
b = header_t.from_bytes(data)
assert a == b
```

## Keyword Arguments

You can initialize struct fields by name without providing a memory buffer:

```python
header = header_t(magic=0xdeadbeef, version=1, size=4096)
print(header.magic.value)  # 3735928559
```

Since there is no backing memory buffer, libdestruct automatically creates a simulated memory page to hold the values. This is convenient for building structs from scratch — for example, to serialize them later with `to_bytes()`.

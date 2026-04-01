# The Inflater

The inflater is the main entry point for reading typed data from memory.

## Creating an Inflater

```python
from libdestruct import inflater

memory = bytearray(1024)
lib = inflater(memory)
```

The `inflater()` function accepts any `Sequence` — typically `bytes` or `bytearray`.

!!! note
    Use `bytearray` if you need to write values back to memory. With immutable `bytes`, read operations work but writes will fail.

## Inflating Types

Call `inflate(type, address)` to materialize a typed object at the given offset:

```python
from libdestruct import c_int, c_long, struct

# Primitive types
x = lib.inflate(c_int, 0)
y = lib.inflate(c_long, 4)

# Structs
class point_t(struct):
    x: c_int
    y: c_int

point = lib.inflate(point_t, 0)
```

The returned object is a live view into the memory buffer. Changes to the buffer are reflected in the object, and writes through the object update the buffer.

## The `inflate()` Function

For one-off use, the module-level `inflate()` function combines creation and inflation:

```python
from libdestruct import inflate, c_int

memory = (42).to_bytes(4, "little")
x = inflate(c_int, memory, 0)
print(x.value)  # 42
```

## The `from_bytes()` Class Method

Every type supports `from_bytes()` for quick deserialization without explicitly creating an inflater:

```python
from libdestruct import c_int

x = c_int.from_bytes(b"\x2a\x00\x00\x00")
print(x.value)  # 42
```

For structs:

```python
class pair_t(struct):
    a: c_int
    b: c_int

pair = pair_t.from_bytes(b"\x01\x00\x00\x00\x02\x00\x00\x00")
print(pair.a.value)  # 1
print(pair.b.value)  # 2
```

## Multiple Objects from One Buffer

The inflater lets you inflate multiple objects from different offsets in the same memory:

```python
class header_t(struct):
    magic: c_int

class data_t(struct):
    value: c_int

class footer_t(struct):
    checksum: c_int

memory = bytearray(100)
lib = inflater(memory)

header = lib.inflate(header_t, 0)
payload = lib.inflate(data_t, 16)
footer = lib.inflate(footer_t, 80)
```

All objects share the same backing buffer — a write to one is visible to others if their memory regions overlap.

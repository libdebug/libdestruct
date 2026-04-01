# Enums

libdestruct maps integer values in memory to Python `Enum` types using the `enum[T]` subscript syntax or the `enum_of()` factory function.

## Defining Enums

```python
from enum import IntEnum
from libdestruct import struct, c_int, enum

class Color(IntEnum):
    RED = 0
    GREEN = 1
    BLUE = 2

# Subscript syntax (preferred)
class pixel_t(struct):
    color: enum[Color]        # defaults to c_int backing type
    x: c_int
    y: c_int

# With a custom backing type:
class pixel2_t(struct):
    color: enum[Color, c_short]  # 2-byte backing type
    x: c_int
    y: c_int
```

The legacy `enum_of()` syntax is also supported:

```python
from libdestruct import struct, c_int, enum_of

class pixel_t(struct):
    color: enum = enum_of(Color)
    x: c_int
    y: c_int
```

The enum type:

- Reads the raw integer from memory using the backing type (`c_int` by default)
- Converts it to the corresponding `Enum` member (`Color.RED`, etc.)

## Reading Enum Values

```python
from libdestruct import inflater

memory = bytearray(12)
memory[0:4] = (1).to_bytes(4, "little")  # Color.GREEN

lib = inflater(memory)
pixel = lib.inflate(pixel_t, 0)

print(pixel.color.value)  # Color.GREEN
```

## Lenient Mode

By default, enums operate in lenient mode: if the integer value does not match any enum member, the raw integer is returned instead of raising an error.

```python
memory[0:4] = (99).to_bytes(4, "little")  # Not a valid Color
pixel = lib.inflate(pixel_t, 0)

print(pixel.color.value)  # 99 (raw integer, no error)
```

## Standalone Enums

You can also inflate enums directly outside of structs:

```python
from libdestruct import enum, inflater

memory = (2).to_bytes(4, "little")
lib = inflater(memory)

e = lib.inflate(enum[Color], 0)
print(e.value)  # Color.BLUE
```

!!! tip
    For struct fields, the `enum[T]` subscript syntax is the recommended API. It automatically handles type registration and inflation.

## Serialization

Enum values serialize through their backing type:

```python
raw = pixel.color.to_bytes()
print(len(raw))  # 4 (size of c_int)
```

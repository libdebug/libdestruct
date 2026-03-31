# Enums

libdestruct maps integer values in memory to Python `Enum` types using `enum_of()`.

## Defining Enums

```python
from enum import IntEnum
from libdestruct import struct, c_int, enum_of

class Color(IntEnum):
    RED = 0
    GREEN = 1
    BLUE = 2

class pixel_t(struct):
    color: enum_of(Color, c_int)
    x: c_int
    y: c_int
```

`enum_of(PythonEnum, backing_type)` creates a type that:

- Reads the raw integer from memory using the backing type (`c_int`)
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

You can also use `enum` directly (without `enum_of`):

```python
from libdestruct import enum, inflater

memory = (2).to_bytes(4, "little")
lib = inflater(memory)

# The enum() constructor takes a resolver, a Python Enum, and a backing type
```

!!! tip
    For struct fields, `enum_of()` is the recommended API. It automatically handles type registration and inflation.

## Serialization

Enum values serialize through their backing type:

```python
raw = pixel.color.to_bytes()
print(len(raw))  # 4 (size of c_int)
```

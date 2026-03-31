# C Types

libdestruct provides Python equivalents for common C primitive types. All types share a common interface inherited from `obj`.

## Available Types

| libdestruct | C equivalent | Size (bytes) | Signed |
|---|---|---|---|
| `c_char` | `char` / `int8_t` | 1 | Yes |
| `c_uchar` | `unsigned char` / `uint8_t` | 1 | No |
| `c_short` | `short` / `int16_t` | 2 | Yes |
| `c_ushort` | `unsigned short` / `uint16_t` | 2 | No |
| `c_int` | `int` / `int32_t` | 4 | Yes |
| `c_uint` | `unsigned int` / `uint32_t` | 4 | No |
| `c_long` | `long` / `int64_t` | 8 | Yes |
| `c_ulong` | `unsigned long` / `uint64_t` | 8 | No |
| `c_float` | `float` | 4 | — |
| `c_double` | `double` | 8 | — |
| `c_str` | `char[]` | variable | — |

## Usage

### Reading Values

```python
from libdestruct import c_int, c_ulong, inflater

memory = bytearray(12)
lib = inflater(memory)

# Inflate a signed 32-bit integer at offset 0
x = lib.inflate(c_int, 0)
print(x.value)  # 0

# Inflate an unsigned 64-bit integer at offset 4
y = lib.inflate(c_ulong, 4)
print(y.value)  # 0
```

### Writing Values

When backed by a mutable `bytearray`, you can write values back:

```python
memory = bytearray(4)
lib = inflater(memory)
x = lib.inflate(c_int, 0)

x.value = -1
print(memory)  # bytearray(b'\xff\xff\xff\xff')
```

### From Bytes

You can create a standalone value from raw bytes:

```python
from libdestruct import c_int

x = c_int.from_bytes(b"\x2a\x00\x00\x00")
print(x.value)  # 42
```

## size_of()

The `size_of()` function returns the size in bytes of any type, instance, or field descriptor:

```python
from libdestruct import size_of, c_int, c_long, c_float, ptr, struct, array_of

size_of(c_int)    # 4
size_of(c_long)   # 8
size_of(c_float)  # 4
size_of(ptr)      # 8

# Works with struct types
class point_t(struct):
    x: c_int
    y: c_int

size_of(point_t)  # 8

# Works with instances
x = c_int.from_bytes(b"\x00\x00\x00\x00")
size_of(x)        # 4

# Works with array field descriptors
size_of(array_of(c_int, 10))  # 40
```

## Floating-Point Types

`c_float` and `c_double` represent IEEE 754 single-precision (32-bit) and double-precision (64-bit) floating-point numbers.

```python
import struct as pystruct
from libdestruct import c_float, c_double, inflater

# Read a float from bytes
data = pystruct.pack("<f", 3.14)
f = c_float.from_bytes(data)
print(f.value)   # 3.140000104904175
print(float(f))  # same — c_float supports the __float__ protocol

# Write a double to mutable memory
memory = bytearray(8)
lib = inflater(memory)
d = lib.inflate(c_double, 0)
d.value = 2.718281828
```

Both types support special values like `NaN`, `inf`, and `-inf`, and respect endianness settings.

## Strings

`c_str` represents a null-terminated C string. It behaves like an array of characters:

```python
from libdestruct import c_str, inflater

memory = bytearray(b"Hello\x00World\x00")
lib = inflater(memory)

s = lib.inflate(c_str, 0)
print(s.value)  # "Hello"
print(len(s))   # 5
print(s[0])     # 72 (ord('H'))
```

!!! info
    `c_str` reads until the first null byte. The null terminator is not included in `len()` or `value`.

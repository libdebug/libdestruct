# Bitfields

Bitfields let you pack multiple values into a single integer, just like C bitfields. This is common in hardware registers, protocol headers, and OS structures.

## Defining Bitfields

Use `bitfield_of(backing_type, bit_width)` as a struct field descriptor:

```python
from libdestruct import struct, c_uint, c_long, bitfield_of

class flags_t(struct):
    read: c_uint = bitfield_of(c_uint, 1)
    write: c_uint = bitfield_of(c_uint, 1)
    execute: c_uint = bitfield_of(c_uint, 1)
    reserved: c_uint = bitfield_of(c_uint, 29)
```

All four fields share a single `c_uint` (4 bytes). The bits are allocated left-to-right:

- `read` occupies bit 0
- `write` occupies bit 1
- `execute` occupies bit 2
- `reserved` occupies bits 3-31

## Reading Bitfields

```python
# Bit pattern: 0b101 = read=1, write=0, execute=1
memory = (0b101).to_bytes(4, "little")
flags = flags_t.from_bytes(memory)

print(flags.read.value)     # 1
print(flags.write.value)    # 0
print(flags.execute.value)  # 1
```

## Writing Bitfields

Writes only affect the relevant bits — other bits are preserved:

```python
from libdestruct import inflater

memory = bytearray(4)
lib = inflater(memory)
flags = lib.inflate(flags_t, 0)

flags.read.value = 1
flags.execute.value = 1

print(flags.read.value)     # 1
print(flags.write.value)    # 0 (untouched)
print(flags.execute.value)  # 1
```

## Signed Bitfields

Use a signed backing type (e.g., `c_int`) for sign-extended extraction:

```python
from libdestruct import struct, c_int, bitfield_of

class example_t(struct):
    val: c_int = bitfield_of(c_int, 4)

# 4-bit signed: 0b1111 = -1
memory = (0b1111).to_bytes(4, "little")
test = example_t.from_bytes(memory)
print(test.val.value)  # -1
```

## Multiple Backing Types

When consecutive bitfields use different backing types, a new group starts automatically:

```python
class mixed_t(struct):
    a: c_uint = bitfield_of(c_uint, 3)   # bits 0-2 of a c_uint
    b: c_uint = bitfield_of(c_uint, 5)   # bits 3-7 of the same c_uint
    c: c_long = bitfield_of(c_long, 16)  # bits 0-15 of a new c_long
```

`a` and `b` share 4 bytes, `c` starts a new 8-byte group. Total struct size: 12 bytes.

## C Parser Support

The C struct parser handles bitfield syntax:

```python
from libdestruct.c.struct_parser import definition_to_type

flags_t = definition_to_type("""
    struct flags_t {
        unsigned int read:1;
        unsigned int write:1;
        unsigned int execute:1;
        unsigned int reserved:29;
    };
""")
```

## Serialization

Bitfield structs serialize correctly — shared backing bytes are emitted once:

```python
data = flags.to_bytes()
assert len(data) == 4  # one c_uint
```

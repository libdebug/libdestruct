# Struct Alignment

By default, libdestruct structs are **packed** — fields are placed sequentially with no padding, like C structs with `__attribute__((packed))`.

You can opt into natural alignment (matching standard C struct layout) by setting `_aligned_ = True` on your struct:

## Enabling Alignment

```python
from libdestruct import struct, c_char, c_int, c_long, c_short, size_of, alignment_of

class packed_t(struct):
    a: c_char
    b: c_int

size_of(packed_t)  # 5 (1 + 4, no padding)

class aligned_t(struct):
    _aligned_ = True
    a: c_char
    b: c_int

size_of(aligned_t)  # 8 (1 + 3 padding + 4)
```

## Alignment Rules

When `_aligned_ = True`:

1. **Field alignment**: Each field is placed at an offset that is a multiple of its natural alignment (1 for `c_char`, 2 for `c_short`, 4 for `c_int`/`c_float`, 8 for `c_long`/`c_double`/`ptr`).
2. **Tail padding**: The struct's total size is rounded up to a multiple of the struct's alignment (the maximum alignment of any member).

```python
class mixed_t(struct):
    _aligned_ = True
    a: c_char       # offset 0, size 1
    b: c_short      # offset 2 (aligned to 2), size 2
    c: c_char       # offset 4, size 1
    d: c_int        # offset 8 (aligned to 4), size 4
    e: c_char       # offset 12, size 1
    f: c_long       # offset 16 (aligned to 8), size 8

size_of(mixed_t)    # 24 (padded to 8-byte boundary)
```

## Reading Aligned Structs

```python
import struct as pystruct
from libdestruct import inflater

class header_t(struct):
    _aligned_ = True
    flags: c_char
    size: c_int

# flags at offset 0, 3 bytes padding, size at offset 4
memory = pystruct.pack("<b", 0x01) + b"\x00" * 3 + pystruct.pack("<i", 1024)
header = header_t.from_bytes(memory)

print(header.flags.value)  # 1
print(header.size.value)   # 1024
```

## Nested Aligned Structs

Alignment is respected for nested structs too. A nested struct's alignment equals the maximum alignment of its own members:

```python
class inner_t(struct):
    _aligned_ = True
    a: c_char
    b: c_int

class outer_t(struct):
    _aligned_ = True
    x: c_char
    inner: inner_t  # aligned to 4 (inner's max member alignment)

size_of(inner_t)  # 8
size_of(outer_t)  # 12 (1 + 3 padding + 8)
```

## Custom Alignment Width

Set `_aligned_` to an integer to enforce a minimum alignment boundary. Fields still use natural alignment, but the struct's total size is padded to the specified boundary:

```python
class wide_t(struct):
    _aligned_ = 16
    a: c_int

size_of(wide_t)       # 16 (4 bytes data, padded to 16-byte boundary)
alignment_of(wide_t)  # 16
```

`_aligned_ = True` is equivalent to using the maximum natural member alignment (up to 8).

## Interaction with Explicit Offsets

When a field has an explicit `offset()`, alignment does **not** override the specified position. Alignment resumes for subsequent fields without explicit offsets:

```python
from libdestruct import offset

class s_t(struct):
    _aligned_ = True
    a: c_char
    b: c_int = offset(3)   # placed at offset 3, not rounded to 4
    c: c_int               # aligned normally after b

size_of(s_t)  # 7 (3 + 4)
```

## alignment_of()

Use `alignment_of()` to query the alignment requirement of any type:

```python
from libdestruct import alignment_of, c_int, c_long

alignment_of(c_int)      # 4
alignment_of(c_long)     # 8
alignment_of(aligned_t)  # max member alignment
alignment_of(packed_t)   # 1 (packed structs have alignment 1)
```

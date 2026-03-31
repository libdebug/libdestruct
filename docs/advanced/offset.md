# Field Offsets

By default, struct fields are laid out sequentially — each field starts immediately after the previous one. The `offset()` attribute lets you place a field at a specific byte offset.

## Usage

```python
from libdestruct import struct, c_int, offset

class sparse_t(struct):
    a: c_int
    b: c_int = offset(16)
    c: c_int
```

In this example:

- `a` starts at offset 0 (4 bytes)
- `b` starts at offset 16 (skipping 12 bytes of padding)
- `c` starts at offset 20 (immediately after `b`)

## Rules

The offset must be **greater than or equal to** the current position in the struct. You cannot move backwards:

```python
class invalid_t(struct):
    a: c_int          # offset 0, size 4
    b: c_int = offset(2)  # ERROR: 2 < 4 (current offset)
```

This will raise a `ValueError` at struct creation time.

## Use Cases

### Matching Padded C Structs

C compilers often insert padding for alignment. Use `offset()` to match the actual layout:

```python
# C definition (with compiler padding):
# struct data {
#     char flag;       // offset 0
#     // 3 bytes padding
#     int value;       // offset 4
#     // 4 bytes padding
#     long timestamp;  // offset 8 (on some ABIs, offset 8 with 64-bit alignment)
# };

class data_t(struct):
    flag: c_char
    value: c_int = offset(4)
    timestamp: c_long = offset(8)
```

### Skipping Unknown Fields

When reverse engineering, you might know the offset of a field but not what comes before it:

```python
class mystery_t(struct):
    known_field: c_int = offset(0x40)
    another_field: c_long = offset(0x100)
```

## Combining with Other Attributes

`offset()` can be combined with `Field` attributes using a tuple:

```python
from libdestruct.common.field import Field

class example_t(struct):
    data: c_int = (Field(), offset(8))
```

!!! note
    When using tuples of attributes, only one `Field` is allowed per annotation. Multiple `OffsetAttribute`s are also not typical — use a single `offset()` to set the position.

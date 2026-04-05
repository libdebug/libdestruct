# Struct Inheritance

libdestruct structs support Python class inheritance. A derived struct inherits all fields from its parent, with new fields appended after the parent's fields.

## Basic Usage

```python
from libdestruct import struct, c_int, size_of

class base_t(struct):
    a: c_int

class derived_t(base_t):
    b: c_int

size_of(base_t)     # 4
size_of(derived_t)  # 8 (a + b)
```

Reading and writing works as expected:

```python
import struct as pystruct

data = pystruct.pack("<ii", 10, 20)
d = derived_t.from_bytes(data)
print(d.a.value)  # 10
print(d.b.value)  # 20
```

## Multi-Level Inheritance

Inheritance chains of any depth work. Fields are collected in MRO order (grandparent first):

```python
class level_a(struct):
    x: c_int

class level_b(level_a):
    y: c_int

class level_c(level_b):
    z: c_int

size_of(level_c)  # 12

data = pystruct.pack("<iii", 1, 2, 3)
c = level_c.from_bytes(data)
print(c.x.value)  # 1
print(c.y.value)  # 2
print(c.z.value)  # 3
```

## Field Ordering

Parent fields always come first. This is reflected in `to_dict()`, `to_str()`, and `to_bytes()`:

```python
print(list(c.to_dict().keys()))  # ['x', 'y', 'z']
```

## Keyword Initialization

Keyword arguments work across the inheritance chain:

```python
d = derived_t(a=42, b=99)
print(d.a.value)  # 42
print(d.b.value)  # 99
```

## Alignment Inheritance

If a parent struct has `_aligned_ = True`, derived structs inherit the alignment behavior:

```python
from libdestruct import c_char, c_long

class aligned_base(struct):
    _aligned_ = True
    a: c_char
    b: c_int

class aligned_derived(aligned_base):
    c: c_long

size_of(aligned_base)     # 8  (1 + 3 pad + 4)
size_of(aligned_derived)  # 16 (8 + 8)
```

## Combining with Other Features

Struct inheritance works with all other features: pointers, arrays, enums, bitfields, explicit offsets, unions, and freeze/diff/reset.

```python
from libdestruct import ptr

class header_t(struct):
    magic: c_int
    version: c_int

class packet_t(header_t):
    payload: c_long
    next: ptr[c_int]

size_of(packet_t)  # 24 (4 + 4 + 8 + 8)
```

# Unions

libdestruct supports both **plain unions** (C-style, all variants overlaid) and **tagged unions** (discriminated, one active variant selected by another field).

## Plain Unions

Use `union_of({"name": type, ...})` to declare a union where all variants share the same memory. Access each interpretation by name:

```python
from libdestruct import struct, c_int, c_float, c_long, inflater
from libdestruct.common.union import union, union_of

class packet_t(struct):
    data: union = union_of({
        "i": c_int,
        "f": c_float,
        "l": c_long,
    })
```

All variants are inflated at the same offset. Reading one reinterprets the underlying bytes:

```python
import struct as pystruct

memory = pystruct.pack("<f", 3.14)  + b"\x00" * 4  # pad to 8 bytes (c_long size)
pkt = packet_t.from_bytes(memory)

print(pkt.data.f.value)  # 3.140000104904175
print(pkt.data.i.value)  # 1078523331 (same bytes as int)
```

Writing to any variant updates the shared memory:

```python
memory = bytearray(8)
lib = inflater(memory)
pkt = lib.inflate(packet_t, 0)

pkt.data.i.value = 42
# pkt.data.f.value now reflects those same bytes interpreted as float
```

Struct variants work too — their fields are accessible directly:

```python
class point_t(struct):
    x: c_int
    y: c_int

class data_t(struct):
    raw: union = union_of({"val": c_long, "point": point_t})

d = data_t.from_bytes(pystruct.pack("<ii", 10, 20))
print(d.raw.point.x.value)  # 10
print(d.raw.point.y.value)  # 20
```

## Tagged Unions

libdestruct also supports tagged (discriminated) unions, where the active variant is selected at runtime by another field in the same struct.

## Defining a Tagged Union

Use `tagged_union(discriminator, variants)` to declare a union field in a struct. The `discriminator` is the name of another field whose value selects the variant, and `variants` maps discriminator values to types:

```python
from libdestruct import struct, c_int, c_float, c_long, inflater
from libdestruct.common.union import tagged_union, union

class message_t(struct):
    type: c_int
    payload: union = tagged_union("type", {
        0: c_int,
        1: c_float,
        2: c_long,
    })
```

## Reading Values

The union automatically inflates the correct variant based on the discriminator:

```python
import struct as pystruct

# type=0 selects c_int variant
memory = pystruct.pack("<i", 0) + pystruct.pack("<i", 42) + b"\x00" * 4
msg = message_t.from_bytes(memory)
print(msg.payload.value)  # 42

# type=1 selects c_float variant
memory = pystruct.pack("<i", 1) + pystruct.pack("<f", 3.14) + b"\x00" * 4
msg = message_t.from_bytes(memory)
print(msg.payload.value)  # 3.140000104904175
```

## Writing Values

You can write to the active variant:

```python
memory = bytearray(12)
lib = inflater(memory)
msg = lib.inflate(message_t, 0)

msg.payload.value = 100
print(msg.payload.value)  # 100
```

## Struct Variants

When a variant is a struct type, its fields are accessible directly through the union:

```python
class point_t(struct):
    x: c_int
    y: c_int

class packet_t(struct):
    type: c_int
    data: union = tagged_union("type", {
        0: c_int,
        1: point_t,
    })

memory = pystruct.pack("<i", 1) + pystruct.pack("<ii", 10, 20)
pkt = packet_t.from_bytes(memory)

print(pkt.data.x.value)  # 10
print(pkt.data.y.value)  # 20
```

## Size

The size of a union field is the **maximum** size of all its variants. This ensures the struct layout is correct regardless of which variant is active:

```python
from libdestruct import size_of

class msg_t(struct):
    type: c_int              # 4 bytes
    payload: union = tagged_union("type", {
        0: c_int,            # 4 bytes
        1: c_long,           # 8 bytes
    })

size_of(msg_t)  # 12 (4 + max(4, 8))
```

## Accessing the Variant

Use the `variant` property to get the active variant object directly:

```python
data = pystruct.pack("<i", 0) + pystruct.pack("<i", 42) + b"\x00" * 4
msg = message_t.from_bytes(data)
variant_obj = msg.payload.variant  # the raw c_int, c_float, etc.
```

## Error Handling

If the discriminator value doesn't match any variant, a `ValueError` is raised:

```python
class msg_t(struct):
    type: c_int
    payload: union = tagged_union("type", {0: c_int})

# type=99 has no matching variant
memory = pystruct.pack("<i", 99) + b"\x00" * 4
try:
    msg_t.from_bytes(memory)
except ValueError:
    print("ValueError: unknown discriminator")
```

!!! info
    The discriminator field must appear **before** the union field in the struct definition, since fields are inflated in order.

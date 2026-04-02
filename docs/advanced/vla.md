# Variable-Length Arrays

Variable-length arrays (VLAs) model C's flexible array members: an array whose
element count is stored in another field of the same struct.

## Basic Usage

Use the `vla_of` descriptor or the `array[T, "field"]` subscript syntax:

```python
from libdestruct import struct, c_int, inflater, size_of
from libdestruct.common.array import array, vla_of

class packet_t(struct):
    length: c_int
    data: array = vla_of(c_int, "length")
```

The second argument is the **name of the count field** as a string.
At inflation time the library reads the count from that sibling field and
creates an array of exactly that many elements.

```python
import struct as pystruct

raw = pystruct.pack("<iii", 2, 42, 99)
memory = bytearray(raw)
lib = inflater(memory)
pkt = lib.inflate(packet_t, 0)

assert pkt.length.value == 2
assert len(pkt.data) == 2
assert pkt.data[0].value == 42
assert pkt.data[1].value == 99
```

## Subscript Syntax

Instead of `vla_of`, you can use the subscript syntax with a string count:

```python
from libdestruct import struct, c_int
from libdestruct.common.array import array

class packet_t(struct):
    length: c_int
    data: array[c_int, "length"]
```

Both forms are equivalent.

## Size Semantics

Class-level `size_of` returns the **fixed part only** (excludes the VLA):

```python
from libdestruct import struct, c_int, size_of
from libdestruct.common.array import array, vla_of

class packet_t(struct):
    length: c_int
    data: array = vla_of(c_int, "length")

assert size_of(packet_t) == 4  # only the c_int length field
```

Instance-level `size_of` includes the VLA data:

```python
import struct as pystruct
from libdestruct import struct, c_int, inflater, size_of
from libdestruct.common.array import array, vla_of

class packet_t(struct):
    length: c_int
    data: array = vla_of(c_int, "length")

raw = pystruct.pack("<iiii", 3, 10, 20, 30)
memory = bytearray(raw)
lib = inflater(memory)
pkt = lib.inflate(packet_t, 0)

assert size_of(pkt) == 4 + 3 * 4  # 16 bytes
```

## VLA Must Be the Last Field

Like C flexible array members, a VLA must be the last field in the struct.
Placing a field after a VLA raises a `ValueError`:

```python
from libdestruct import struct, c_int, size_of
from libdestruct.common.array import array, vla_of

class bad_t(struct):
    length: c_int
    data: array = vla_of(c_int, "length")
    extra: c_int

try:
    size_of(bad_t)
    assert False, "should have raised"
except ValueError:
    pass  # expected
```

## VLA of Structs

VLA elements can be structs:

```python
import struct as pystruct
from libdestruct import struct, c_int, inflater
from libdestruct.common.array import array, vla_of

class point_t(struct):
    x: c_int
    y: c_int

class path_t(struct):
    count: c_int
    points: array = vla_of(point_t, "count")

raw = pystruct.pack("<iiiii", 2, 1, 2, 3, 4)
memory = bytearray(raw)
lib = inflater(memory)
path = lib.inflate(path_t, 0)

assert path.points[0].x.value == 1
assert path.points[1].y.value == 4
```

## Writing to VLA Elements

VLA elements are writable just like regular array elements:

```python
import struct as pystruct
from libdestruct import struct, c_int, inflater
from libdestruct.common.array import array, vla_of

class packet_t(struct):
    length: c_int
    data: array = vla_of(c_int, "length")

raw = pystruct.pack("<iii", 2, 0, 0)
memory = bytearray(raw)
lib = inflater(memory)
pkt = lib.inflate(packet_t, 0)

pkt.data[0].value = 42
pkt.data[1].value = 99
assert pkt.data[0].value == 42
```

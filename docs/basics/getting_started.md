# Getting Started

## Requirements

- Python 3.10 or later
- `typing_extensions`
- `pycparser` (for C struct parsing)

## Installation

=== "pip"

    ```bash
    pip install libdestruct
    ```

=== "From source"

    ```bash
    git clone https://github.com/mrindeciso/libdestruct.git
    cd libdestruct
    pip install .
    ```

## Core Concepts

libdestruct revolves around three ideas:

1. **Types** — Python classes that mirror C types (`c_int`, `c_long`, `struct`, `ptr`, etc.)
2. **Memory** — a `bytes` or `bytearray` buffer that holds the raw data
3. **Inflater** — the bridge that reads memory and materializes typed objects

### A Minimal Example

```python
from libdestruct import c_int, inflater

memory = (42).to_bytes(4, "little")
lib = inflater(memory)
value = lib.inflate(c_int, 0)

print(value.value)  # 42
```

Here, `inflater(memory)` creates a memory context, and `inflate(c_int, 0)` reads a 4-byte signed integer at offset 0.

### Working with Structs

Structs let you group fields together, just like in C:

```python
from libdestruct import struct, c_int, c_long, inflater

class point_t(struct):
    x: c_int
    y: c_int

memory = bytearray(8)
lib = inflater(memory)
point = lib.inflate(point_t, 0)

# Write values
point.x.value = 10
point.y.value = 20

# Read them back
print(point.x.value)  # 10
print(point.y.value)  # 20
```

!!! note
    When the backing memory is a `bytearray`, writes through `.value` are reflected in the underlying buffer. With immutable `bytes`, writes will raise an error.

### Reading and Writing

Every libdestruct object exposes:

| Property / Method | Description |
|---|---|
| `.value` | Get or set the current value |
| `.address` | The address (offset) in memory |
| `.to_bytes()` | Serialize the object to bytes |
| `bytes(obj)` | Same as `.to_bytes()` |
| `.to_str()` | Human-readable string representation |

### Serialization Round-Trip

You can serialize any object to bytes and deserialize it back:

```python
from libdestruct import struct, c_int

class pair_t(struct):
    a: c_int
    b: c_int

# Create from raw bytes
original = pair_t.from_bytes(b"\x01\x00\x00\x00\x02\x00\x00\x00")

# Serialize
data = original.to_bytes()

# Deserialize
copy = pair_t.from_bytes(data)

assert copy.a.value == 1
assert copy.b.value == 2
```

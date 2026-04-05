# File-Backed Memory

libdestruct can inflate structs directly from binary files using memory-mapped I/O. This is efficient for large files since only accessed pages are loaded into memory.

## Quick Start

Use `inflater_from_file()` for the simplest approach:

```python
from libdestruct import struct, c_int, c_long, inflater_from_file

class header_t(struct):
    magic: c_int
    version: c_int
    size: c_long
```

```python
import tempfile, struct as pystruct, os

# Create a sample binary file
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
tmp.write(pystruct.pack("<iiq", 42, 2, 4096))
tmp.flush()

with inflater_from_file(tmp.name) as lib:
    header = lib.inflate(header_t, 0)
    print(f"magic: {header.magic.value}")     # magic: 42
    print(f"version: {header.version.value}")  # version: 2
    print(f"size: {header.size.value}")        # size: 4096

tmp.close()
os.unlink(tmp.name)
```

## Writable Mode

Pass `writable=True` to modify the file through the inflater. Changes are written back to disk:

```python
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
tmp.write(pystruct.pack("<ii", 0, 0))
tmp.flush()

with inflater_from_file(tmp.name, writable=True) as lib:
    header = lib.inflate(header_t, 0)
    header.magic.value = 123
    header.version.value = 1

# Changes are persisted to the file
with open(tmp.name, "rb") as f:
    data = f.read(8)
    magic, version = pystruct.unpack("<ii", data)

print(f"magic: {magic}")      # magic: 123
print(f"version: {version}")  # version: 1

os.unlink(tmp.name)
```

## Manual mmap Usage

You can also pass an `mmap` object directly to `inflater()`:

```python
import mmap

tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
tmp.write(pystruct.pack("<ii", 42, 99))
tmp.flush()

with mmap.mmap(tmp.fileno(), 0, access=mmap.ACCESS_READ) as m:
    from libdestruct import inflater
    lib = inflater(m)
    header = lib.inflate(header_t, 0)
    print(header.magic.value)  # 42

tmp.close()
os.unlink(tmp.name)
```

This gives you full control over mmap options (access mode, offset, length).

## Multiple Structs from One File

The file inflater works like the regular inflater — inflate multiple structs at different offsets:

```python
class point_t(struct):
    x: c_int
    y: c_int

tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
tmp.write(pystruct.pack("<iiii", 1, 2, 3, 4))
tmp.flush()

with inflater_from_file(tmp.name) as lib:
    p1 = lib.inflate(point_t, 0)
    p2 = lib.inflate(point_t, 8)
    print(f"p1: ({p1.x.value}, {p1.y.value})")  # p1: (1, 2)
    print(f"p2: ({p2.x.value}, {p2.y.value})")  # p2: (3, 4)

tmp.close()
os.unlink(tmp.name)
```

!!! note
    The `inflater_from_file()` function returns a context manager. Always use it with `with` to ensure the file and mmap are properly closed.

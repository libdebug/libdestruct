# Bit Flags

libdestruct supports bit flag fields using Python's `IntFlag`. Flags represent bitwise combinations of named values — common in file permissions, hardware registers, and protocol headers.

## Defining Flags

First, define your flags as a Python `IntFlag`:

```python
from enum import IntFlag

class Perms(IntFlag):
    READ = 4
    WRITE = 2
    EXEC = 1
```

## Using Flags in Structs

### Subscript Syntax (preferred)

```python
from libdestruct import struct, c_int, inflater
from libdestruct.common.flags import flags

class file_t(struct):
    mode: flags[Perms]
```

### Descriptor Syntax

```python
from libdestruct.common.flags import flags_of

class file_t(struct):
    mode: flags = flags_of(Perms)
```

## Reading Flag Values

```python
import struct as pystruct

data = pystruct.pack("<i", 5)  # READ | EXEC
memory = bytearray(data)
lib = inflater(memory)
f = lib.inflate(file_t, 0)

result = f.mode.get()
print(result)                  # Perms.READ|Perms.EXEC
print(Perms.READ in result)    # True
print(Perms.WRITE in result)   # False
```

## Writing Flag Values

```python
memory = bytearray(4)
lib = inflater(memory)
f = lib.inflate(file_t, 0)

f.mode.value = Perms.READ | Perms.WRITE
print(f.mode.get())  # Perms.READ|Perms.WRITE
```

## Custom Backing Type

By default, flags use a 4-byte `c_int` backing. Use a subscript to change the backing type:

```python
from libdestruct import c_short, size_of

class compact_t(struct):
    mode: flags[Perms, c_short]

size_of(compact_t)  # 2
```

Or with the descriptor syntax:

```python
class compact_t(struct):
    mode: flags = flags_of(Perms, size=2)

size_of(compact_t)  # 2
```

## Strict Mode

By default, flags are **lenient** — unknown bits are preserved as part of the `IntFlag` value. In strict mode, unknown bits raise a `ValueError`:

```python
class strict_t(struct):
    mode: flags = flags_of(Perms, lenient=False)

# Value 0xFF has bits beyond READ|WRITE|EXEC
data = pystruct.pack("<i", 0xFF)
memory = bytearray(data)
lib = inflater(memory)
f = lib.inflate(strict_t, 0)

try:
    f.mode.get()
except ValueError:
    print("Unknown bits detected")
```

## Flags vs Enums

Use **flags** when values are bitwise-combinable (permissions, feature flags). Use **enums** when values are mutually exclusive (state machines, error codes).

| Feature | `enum` / `enum_of` | `flags` / `flags_of` |
|---------|---------------------|----------------------|
| Python type | `IntEnum` | `IntFlag` |
| Values | Mutually exclusive | Bitwise combinable |
| Unknown values | Lenient: raw int | Lenient: preserved bits |
| Strict mode | Raises `ValueError` | Raises `ValueError` |

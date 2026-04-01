# Resolvers

Resolvers are the low-level mechanism that connects typed objects to their backing memory. You typically don't interact with resolvers directly — the inflater creates them for you — but understanding them helps when writing custom memory backends.

## How Resolvers Work

Every `obj` instance holds a `Resolver` that knows:

- **Where** in memory the object lives (its address)
- **How** to read bytes from that location
- **How** to write bytes back (if the memory is mutable)

When you access `.value`, the object asks its resolver to read the appropriate number of bytes, then interprets them according to its type.

## Built-in Resolvers

### MemoryResolver

The standard resolver used by `inflater()`. It reads from and writes to a Python `Sequence` (typically `bytes` or `bytearray`).

```python
from libdestruct import inflater

# MemoryResolver is created internally
lib = inflater(bytearray(1024))
```

### FakeResolver

A resolver backed by a simulated 4KB memory page, used internally when you create structs via keyword arguments or `from_bytes()` without explicit memory:

```python
from libdestruct import struct, c_int

class test_t(struct):
    a: c_int

# FakeResolver is used behind the scenes
t = test_t(a=42)
print(t.a.value)  # 42
```

!!! info
    The FakeResolver uses a dictionary of 4KB pages. It is suitable for testing and quick prototyping but is not intended for production use with large address spaces.

## The Resolver Interface

All resolvers implement these methods:

| Method | Description |
|---|---|
| `resolve(size, offset)` | Read `size` bytes starting at the resolved address + offset |
| `resolve_address()` | Return the absolute address of this resolver |
| `modify(size, index, value)` | Write `value` bytes at the resolved address + index |
| `relative_from_own(offset, size)` | Create a child resolver at a relative offset |
| `absolute_from_own(address)` | Create a child resolver at an absolute address |

## Custom Memory Backends

If you need to read from a custom source (e.g., a debugger's memory API, a remote process, a file), you can subclass `Resolver`:

```python
from libdestruct.backing.resolver import Resolver

class DebuggerResolver(Resolver):
    def __init__(self, debugger, address):
        self.debugger = debugger
        self._address = address

    def resolve(self, size, offset=0):
        return self.debugger.read_memory(self._address + offset, size)

    def resolve_address(self):
        return self._address

    def modify(self, size, index, value):
        self.debugger.write_memory(self._address + index, value)

    # ... implement relative_from_own, absolute_from_own
```

!!! tip
    libdestruct was designed with debugger integration in mind. The [libdebug](https://github.com/libdebug/libdebug) project uses libdestruct through a custom resolver that bridges to the debugger's memory access API.

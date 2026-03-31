# Pointers

libdestruct supports typed pointers that can be dereferenced to follow references in memory.

## Defining Pointers in Structs

Use `ptr` with `ptr_to()` to declare a typed pointer field:

```python
from libdestruct import struct, c_int, ptr_to, inflater

class data_t(struct):
    value: c_int
    next: ptr_to(c_int)
```

A pointer occupies 8 bytes (64-bit) and stores an address into the memory buffer.

## Dereferencing

Use `unwrap()` to follow a pointer:

```python
memory = bytearray(16)
lib = inflater(memory)

# Set up: value=42 at offset 0, pointer to offset 12 at offset 4
import struct as pystruct
memory[0:4] = pystruct.pack("<i", 42)
memory[4:12] = pystruct.pack("<q", 12)      # next -> offset 12
memory[12:16] = pystruct.pack("<i", 99)     # value at offset 12

data = lib.inflate(data_t, 0)
print(data.value.value)           # 42
print(data.next.unwrap().value)   # 99
```

### Safe Dereferencing

Use `try_unwrap()` for null-safe pointer access. It returns `None` if the pointer is null (0):

```python
class node_t(struct):
    val: c_int
    next: ptr_to(c_int)

memory = b"\x0a\x00\x00\x00" + b"\x00" * 8  # val=10, next=null
node = node_t.from_bytes(memory)

result = node.next.try_unwrap()
print(result)  # None
```

## Self-Referential Structs

Use `ptr_to_self` for linked lists and trees:

```python
from libdestruct import struct, c_int, ptr_to_self

class node_t(struct):
    val: c_int
    next: ptr_to_self
```

Or use the forward reference syntax with `ptr["TypeName"]`:

```python
from libdestruct import struct, c_int, ptr

class node_t(struct):
    val: c_int
    next: ptr["node_t"]
```

Both forms are equivalent. See [Forward References](../advanced/forward_refs.md) for more details.

### Linked List Example

```python
memory = bytearray(24)

import struct as pystruct
# Node 0 at offset 0: val=10, next -> offset 12
memory[0:4] = pystruct.pack("<i", 10)
memory[4:12] = pystruct.pack("<q", 12)
# Node 1 at offset 12: val=20, next -> null
memory[12:16] = pystruct.pack("<i", 20)
memory[16:24] = pystruct.pack("<q", 0)

lib = inflater(memory)
head = lib.inflate(node_t, 0)

print(head.val.value)                    # 10
print(head.next.unwrap().val.value)      # 20
print(head.next.unwrap().next.try_unwrap())  # None
```

## Pointer Arithmetic

Typed pointers support C-style pointer arithmetic. Adding or subtracting an integer advances/retreats by that many elements (scaled by the pointed-to type's size):

```python
from libdestruct import c_int, ptr, inflater
from libdestruct.backing.memory_resolver import MemoryResolver
import struct as pystruct

# Memory: [ptr to arr] [10] [20] [30]
memory = bytearray(8 + 12)
memory[0:8] = pystruct.pack("<q", 8)       # pointer to offset 8
memory[8:12] = pystruct.pack("<i", 10)
memory[12:16] = pystruct.pack("<i", 20)
memory[16:20] = pystruct.pack("<i", 30)

p = ptr(MemoryResolver(memory, 0), c_int)

print(p.unwrap().value)        # 10
print((p + 1).unwrap().value)  # 20
print((p + 2).unwrap().value)  # 30
```

### Indexing

Use `ptr[n]` as shorthand for `(ptr + n).unwrap()`:

```python
print(p[0].value)  # 10
print(p[1].value)  # 20
print(p[2].value)  # 30
```

### Untyped Pointers

For pointers without a wrapper type, arithmetic advances by 1 byte per unit:

```python
p_raw = ptr(MemoryResolver(memory, 0))  # no wrapper
p2 = p_raw + 4   # advances by 4 bytes
```

## Caching

Pointer dereferencing is cached — repeated calls to `unwrap()` or `try_unwrap()` return the same object without re-inflating:

```python
r1 = node.next.unwrap()
r2 = node.next.unwrap()
assert r1 is r2  # same object
```

If the underlying memory changes, call `invalidate()` to clear the cache:

```python
# Memory was modified externally
node.next.invalidate()
r3 = node.next.unwrap()  # re-inflated from updated memory
```

Setting the pointer's value automatically invalidates the cache:

```python
node.next.value = new_address  # cache cleared automatically
```

## Pointer String Representation

```python
print(data.next.to_str())  # "c_int@0xc" (or "ptr@0xc" for untyped)
```

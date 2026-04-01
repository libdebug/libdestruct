# Forward References

Forward references allow structs to reference types that haven't been fully defined yet — most commonly, the struct itself. This is essential for recursive data structures like linked lists and trees.

## The `ptr["TypeName"]` Syntax

Use a string inside `ptr[...]` to reference a type by name:

```python
from libdestruct import struct, c_int, ptr

class Node(struct):
    val: c_int
    next: ptr["Node"]
```

At inflation time, the string `"Node"` is resolved to the actual `Node` class. This works because Python's `from __future__ import annotations` (used internally by libdestruct) defers annotation evaluation.

## The Legacy `ptr_to_self` Shortcut

For the common case of a pointer to the enclosing struct, the legacy `ptr_to_self` syntax is also available:

```python
from libdestruct import struct, c_int, ptr_to_self

class Node(struct):
    val: c_int
    next: ptr_to_self
```

This is equivalent to `ptr["Node"]` but doesn't require you to spell out the type name. The `ptr["TypeName"]` syntax is preferred as it is more explicit.

## Linked List Example

```python
from libdestruct import struct, c_int, ptr, inflater

class Node(struct):
    val: c_int
    next: ptr["Node"]

# Build a two-node list in memory
# Node layout: c_int(4) + ptr(8) = 12 bytes
memory = bytearray(24)

import struct as pystruct
# Node 0 at offset 0
memory[0:4] = pystruct.pack("<i", 10)
memory[4:12] = pystruct.pack("<q", 12)   # next -> offset 12

# Node 1 at offset 12
memory[12:16] = pystruct.pack("<i", 20)
memory[16:24] = pystruct.pack("<q", 0)   # next -> null

lib = inflater(memory)
head = lib.inflate(Node, 0)

print(head.val.value)                        # 10
print(head.next.unwrap().val.value)          # 20
print(head.next.unwrap().next.try_unwrap())  # None
```

## Tree Example

```python
from libdestruct import struct, c_uint, ptr

class TreeNode(struct):
    data: c_uint
    left: ptr["TreeNode"]
    right: ptr["TreeNode"]
```

## How It Works

When libdestruct encounters a `ptr["TypeName"]` annotation:

1. It stores the string reference during struct class creation
2. At inflation time, it resolves the string against all known struct types
3. The resolved type is used as the pointer's wrapper type

This means the referenced type must be defined before the struct is inflated, but not necessarily before it is declared.

!!! info
    Forward references are resolved through the `TypeRegistry` at inflation time. If the referenced type is not found, an error is raised.

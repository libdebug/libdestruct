# C Struct Parser

libdestruct can parse C struct definitions directly and convert them into usable Python types. This is powered by [pycparser](https://github.com/eliben/pycparser).

## Basic Usage

```python
from libdestruct.c.struct_parser import definition_to_type

player_t = definition_to_type("""
    struct player_t {
        int health;
        unsigned int score;
        long experience;
    };
""")

memory = b"\x64\x00\x00\x00\xe8\x03\x00\x00\x39\x05\x00\x00\x00\x00\x00\x00"
player = player_t.from_bytes(memory)

print(player.health.value)      # 100
print(player.score.value)       # 1000
print(player.experience.value)  # 1337
```

## Supported C Types

The parser recognizes these C type specifiers:

| C Type | Maps to |
|---|---|
| `int` | `c_int` |
| `unsigned int` | `c_uint` |
| `long` | `c_long` |
| `unsigned long` | `c_ulong` |
| `char` | `c_char` |

Type names are normalized — `unsigned int`, `uint`, and `unsigned` all map to `c_uint`.

## Pointers

Single, double, and triple pointers are supported:

```python
t = definition_to_type("""
    struct test {
        int *p;
        int **pp;
        int ***ppp;
    };
""")
```

Self-referential pointers are automatically detected:

```python
node_t = definition_to_type("""
    struct node {
        int value;
        struct node *next;
    };
""")
```

## Arrays

Fixed-size arrays are converted to `array[T, N]` types:

```python
t = definition_to_type("""
    struct buffer {
        int data[16];
    };
""")
```

## Nested Structs

Define multiple structs in a single definition:

```python
t = definition_to_type("""
    struct point {
        int x;
        int y;
    };

    struct rect {
        struct point origin;
        struct point size;
    };
""")
```

The last struct in the definition is returned. All previous structs are cached and available for forward references.

## Typedefs

The parser supports `typedef` declarations. Typedefs are resolved when used as field types in subsequent structs:

```python
t = definition_to_type("""
    typedef unsigned int uint32_t;
    struct S { uint32_t x; };
""")
```

Struct typedefs, pointer typedefs, and chained typedefs all work:

```python
# Struct typedef
t = definition_to_type("""
    typedef struct { int x; int y; } Point;
    struct S { Point p; };
""")

# Pointer typedef
t = definition_to_type("""
    typedef int *intptr;
    struct S { intptr p; };
""")

# Chained typedef
t = definition_to_type("""
    typedef unsigned int u32;
    typedef u32 mytype;
    struct S { mytype x; };
""")
```

## Include Directives

The parser supports `#include` directives by running the C preprocessor:

```python
t = definition_to_type("""
    #include <stdint.h>

    struct packet {
        int type;
        unsigned long length;
    };
""")
```

!!! warning
    Include expansion requires a C preprocessor (`cpp`) to be available on your system.

## GCC Attributes

`__attribute__((...))` annotations are automatically stripped before parsing:

```python
t = definition_to_type("""
    struct __attribute__((packed)) data {
        int x;
        int y;
    };
""")
```

## Caching

Parsed struct definitions are cached globally. Parsing the same struct name twice returns the cached version:

```python
# First call parses
t1 = definition_to_type("struct foo { int x; };")

# Second call with same name returns cached type
t2 = definition_to_type("struct foo { int x; };")
```

# Freeze, Diff & Reset

libdestruct supports snapshotting values for change tracking. This is useful when you want to detect what changed in memory between two points in time.

## Freezing

Call `freeze()` to snapshot the current value:

```python
from libdestruct import c_int, inflater

memory = bytearray(4)
lib = inflater(memory)
x = lib.inflate(c_int, 0)

x.value = 42
x.freeze()
```

Once frozen, the object remembers its value at the time of the freeze. Further reads still return the live value from memory, but writes are blocked:

```python
# Writing to a frozen object raises ValueError
try:
    x.value = 99
except ValueError:
    print("Cannot write to frozen object")
```

## Diffing

Use `diff()` to compare the frozen value with the current live value:

```python
x.value = 42
x.freeze()

# Something changes the underlying memory
memory[0:4] = (100).to_bytes(4, "little")

frozen_val, current_val = x.diff()
print(f"Was: {frozen_val}, Now: {current_val}")
# Was: 42, Now: 100
```

!!! note
    `diff()` only works on frozen objects. It returns a tuple of `(frozen_value, current_value)`.

## Resetting

Call `reset()` to restore the memory to the frozen value:

```python
x.reset()
print(x.value)  # 42 (restored to frozen value)
```

## Updating

Call `update()` to re-freeze with the current live value, discarding the old snapshot:

```python
x.update()
# The frozen value is now whatever is currently in memory
```

## Freezing Structs

When you freeze a struct, all its members are frozen recursively:

```python
from libdestruct import struct, c_int, inflater

class pair_t(struct):
    a: c_int
    b: c_int

memory = bytearray(8)
lib = inflater(memory)
pair = lib.inflate(pair_t, 0)

pair.a.value = 10
pair.b.value = 20

pair.freeze()

# Both members are now frozen
try:
    pair.a.value = 999
except ValueError:
    print("Frozen!")
```

## Workflow Example

A typical workflow for detecting changes:

```python
# 1. Inflate the struct
state = lib.inflate(game_state_t, addr)

# 2. Freeze the current state
state.freeze()

# 3. Let the program run (memory changes externally)
# ...

# 4. Check what changed
for name in ["health", "score", "level"]:
    member = getattr(state, name)
    old, new = member.diff()
    if old != new:
        print(f"{name}: {old} -> {new}")

# 5. Optionally reset to the frozen state
state.reset()
```

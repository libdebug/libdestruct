# Arrays

Fixed-size arrays are created with `array_of()`.

## Defining Arrays

```python
from libdestruct import c_int, array_of, inflater

# An array of 5 c_int values
int_array_t = array_of(c_int, 5)
```

## Inflating Arrays

```python
memory = bytearray(20)  # 5 * 4 bytes
lib = inflater(memory)
arr = lib.inflate(int_array_t, 0)
```

## Indexing

Access elements by index:

```python
memory = b"".join((i).to_bytes(4, "little") for i in range(5))
lib = inflater(memory)
arr = lib.inflate(array_of(c_int, 5), 0)

print(arr[0].value)  # 0
print(arr[2].value)  # 2
print(arr[4].value)  # 4
```

## Iteration

Arrays are iterable:

```python
for element in arr:
    print(element.value)
# 0, 1, 2, 3, 4
```

## Length

```python
print(len(arr))  # 5
```

## Containment

```python
elem = arr[2]
print(elem in arr)  # True
```

## Value Property

The `.value` property returns a list of all element objects:

```python
elements = arr.value
print(len(elements))          # 5
print(elements[0].value)      # 0
```

## Serialization

```python
raw = arr.to_bytes()
# or
raw = bytes(arr)
```

## Arrays in Structs

Use `array_of()` as a type annotation:

```python
from libdestruct import struct, c_int, array_of

class matrix_row_t(struct):
    values: array_of(c_int, 4)
```

```python
data = b"".join((i * 10).to_bytes(4, "little") for i in range(4))
row = matrix_row_t.from_bytes(data)

for v in row.values:
    print(v.value)
# 0, 10, 20, 30
```

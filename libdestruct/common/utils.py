#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

import contextlib
import sys
from types import GenericAlias, MethodType
from typing import TYPE_CHECKING, Any, ForwardRef

from libdestruct.common.field import Field
from libdestruct.common.type_registry import TypeRegistry

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Generator

    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj


def is_field_bound_method(item: obj) -> bool:
    """Check if the provided item is the bound method of a Field object."""
    return isinstance(item, MethodType) and isinstance(item.__self__, Field)


def size_of(item_or_inflater: obj | Callable[[Resolver], obj]) -> int:
    """Return the size in bytes of a type, instance, or field descriptor."""
    # Field instances (e.g. array_of, ptr_to) — must come before .size check
    if isinstance(item_or_inflater, Field):
        return item_or_inflater.get_size()
    if is_field_bound_method(item_or_inflater):
        return item_or_inflater.__self__.get_size()

    # Subscripted GenericAlias types (e.g. array[c_int, 10], enum[Color], ptr[T])
    if isinstance(item_or_inflater, GenericAlias):
        inflater = TypeRegistry().inflater_for(item_or_inflater)
        return size_of(inflater)

    # Struct types: size is on the inflated _type_impl class (check own __dict__ to avoid MRO leaks)
    if isinstance(item_or_inflater, type) and "_type_impl" in item_or_inflater.__dict__:
        return item_or_inflater._type_impl.size

    # Struct types not yet inflated: trigger inflation to compute size
    if isinstance(item_or_inflater, type) and not hasattr(item_or_inflater, "size"):
        impl = TypeRegistry().inflater_for(item_or_inflater)
        if hasattr(impl, "size") and isinstance(impl.size, int):
            return impl.size

    # Check class-level size (works for both types and instances)
    if isinstance(item_or_inflater, type):
        if hasattr(item_or_inflater, "size") and isinstance(item_or_inflater.size, int):
            return item_or_inflater.size
    elif "_vla_fixed_offset" in item_or_inflater.__dict__:
        # VLA struct: size = fixed offset + dynamic VLA size
        vla_offset = item_or_inflater.__dict__["_vla_fixed_offset"]
        members = object.__getattribute__(item_or_inflater, "_members")
        last_member = list(members.values())[-1]
        return vla_offset + last_member.size
    elif "size" in item_or_inflater.__dict__:
        return item_or_inflater.__dict__["size"]
    elif hasattr(item_or_inflater, "size"):
        # Handles both class-level attributes and properties (e.g. vla_impl.size)
        return item_or_inflater.size

    raise ValueError(f"Cannot determine the size of {item_or_inflater}")


def alignment_of(item: obj | type[obj]) -> int:
    """Return the natural alignment of a type or instance.

    For primitive types, alignment equals their size (1, 2, 4, or 8).
    For struct types, alignment is computed as the max of member alignments.
    For packed structs (the default), alignment is 1.
    """
    # For uninflated struct types, trigger inflation first so alignment is computed
    if isinstance(item, type) and not hasattr(item, "size") and "_type_impl" not in item.__dict__:
        with contextlib.suppress(ValueError, TypeError):
            size_of(item)

    # Struct types with computed alignment (check own __dict__ to avoid MRO leaks)
    if isinstance(item, type) and "_type_impl" in item.__dict__:
        impl = item._type_impl
        if hasattr(impl, "alignment"):
            return impl.alignment

    # Explicit alignment attribute (struct_impl instances, arrays, etc.)
    if not isinstance(item, type) and hasattr(item, "alignment") and isinstance(item.alignment, int):
        return item.alignment
    if isinstance(item, type) and "alignment" in item.__dict__ and isinstance(item.__dict__["alignment"], int):
        return item.__dict__["alignment"]

    # Field descriptors — use get_alignment if available, else derive from element type or size
    if isinstance(item, Field):
        if hasattr(item, "get_alignment"):
            return item.get_alignment()
        if hasattr(item, "item"):
            return alignment_of(item.item)
        return _alignment_from_size(item.get_size())
    if is_field_bound_method(item):
        field = item.__self__
        if hasattr(field, "get_alignment"):
            return field.get_alignment()
        if hasattr(field, "item"):
            return alignment_of(field.item)
        return _alignment_from_size(field.get_size())

    # Derive from size for power-of-2 sized types
    try:
        s = size_of(item)
        return _alignment_from_size(s)
    except (ValueError, TypeError):
        return 1


def _alignment_from_size(s: int) -> int:
    """Derive alignment from size: return size if it's a power of 2 and <= 8, else 1."""
    max_alignment = 8
    if s > 0 and (s & (s - 1)) == 0 and s <= max_alignment:
        return s
    return 1


def _align_offset(offset: int, alignment: int) -> int:
    """Round up offset to the next multiple of alignment."""
    remainder = offset % alignment
    return offset + (alignment - remainder) if remainder else offset


def _resolve_annotation(annotation: Any, defining_class: type) -> Any:
    """Resolve a string annotation to its actual type.

    For annotations that are strings (e.g., from ``from __future__ import annotations``),
    evaluates them in the defining class's module namespace.
    Non-string annotations are returned as-is.
    """
    if not isinstance(annotation, str):
        return annotation

    module = sys.modules.get(defining_class.__module__, None)
    globalns = getattr(module, "__dict__", {}) if module else {}
    localns = {defining_class.__name__: defining_class}

    try:
        return eval(annotation, globalns, localns)  # noqa: S307
    except Exception:
        return ForwardRef(annotation)


def iterate_annotation_chain(item: obj, terminate_at: object | None = None) -> Generator[tuple[str, Any, type[obj]]]:
    """Iterate over the annotation chain of the provided item."""
    current_item = item

    chain = []

    while current_item is not terminate_at:
        chain.insert(0, current_item)
        current_item = current_item.__base__ if hasattr(current_item, "__base__") else None

    for reference_item in chain:
        for name, annotation in reference_item.__annotations__.items():
            yield name, _resolve_annotation(annotation, reference_item), reference_item

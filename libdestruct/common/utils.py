#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

import sys
from types import MethodType
from typing import TYPE_CHECKING, Any, ForwardRef

from libdestruct.common.field import Field

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Generator

    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj


def is_field_bound_method(item: obj) -> bool:
    """Check if the provided item is the bound method of a Field object."""
    return isinstance(item, MethodType) and isinstance(item.__self__, Field)


def size_of(item_or_inflater: obj | callable[[Resolver], obj]) -> int:
    """Return the size in bytes of a type, instance, or field descriptor."""
    # Field instances (e.g. array_of, ptr_to) — must come before .size check
    if isinstance(item_or_inflater, Field):
        return item_or_inflater.get_size()
    if is_field_bound_method(item_or_inflater):
        return item_or_inflater.__self__.get_size()

    # Struct types: size is on the inflated _type_impl class
    if isinstance(item_or_inflater, type) and hasattr(item_or_inflater, "_type_impl"):
        return item_or_inflater._type_impl.size

    # Struct types not yet inflated: trigger inflation to compute size
    if isinstance(item_or_inflater, type) and not hasattr(item_or_inflater, "size"):
        from libdestruct.common.type_registry import TypeRegistry

        impl = TypeRegistry().inflater_for(item_or_inflater)
        if hasattr(impl, "size") and isinstance(impl.size, int):
            return impl.size

    # Check class-level size (works for both types and instances)
    if isinstance(item_or_inflater, type):
        if hasattr(item_or_inflater, "size") and isinstance(item_or_inflater.size, int):
            return item_or_inflater.size
    elif hasattr(item_or_inflater.__class__, "size"):
        return item_or_inflater.__class__.size
    elif hasattr(item_or_inflater, "size"):
        return item_or_inflater.size

    raise ValueError(f"Cannot determine the size of {item_or_inflater}")


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

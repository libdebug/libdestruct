#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2025 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#


from __future__ import annotations

import sys
from typing import TYPE_CHECKING, ForwardRef

from libdestruct.common.ptr.ptr import ptr
from libdestruct.common.ptr.ptr_field import PtrField
from libdestruct.common.type_registry import TypeRegistry

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj


registry = TypeRegistry()


class _LazyPtrField(PtrField):
    """A PtrField that lazily resolves a forward reference at inflation time."""

    def __init__(self: _LazyPtrField, forward_ref: ForwardRef, owner: tuple[obj, type[obj]] | None) -> None:
        super().__init__(None)
        self.forward_ref = forward_ref
        self.owner = owner

    def inflate(self: _LazyPtrField, resolver: Resolver) -> obj:
        """Inflate the field, resolving the forward reference on first use."""
        if self.backing_type is None:
            resolved = self._resolve_forward_ref()
            if resolved is not None:
                self.backing_type = registry.inflater_for(resolved)

        if self.backing_type:
            return ptr(resolver, self.backing_type)

        return ptr(resolver)

    def _resolve_forward_ref(self: _LazyPtrField) -> type | None:
        """Resolve the forward reference to an actual type."""
        globalns = {}
        localns = {}

        if self.owner:
            _, owner_type = self.owner

            # Get the user's reference struct for proper module resolution
            ref_struct = getattr(owner_type, "_reference_struct", owner_type)

            if hasattr(ref_struct, "__module__"):
                module = sys.modules.get(ref_struct.__module__)
                if module:
                    globalns = module.__dict__

            # Add the reference struct to locals for self-references
            if hasattr(ref_struct, "__name__"):
                localns[ref_struct.__name__] = ref_struct

        try:
            resolved = eval(self.forward_ref.__forward_arg__, globalns, localns)  # noqa: S307
            if isinstance(resolved, type):
                return resolved
            return None
        except Exception:
            return None


def _subscripted_ptr_handler(
    item: object,
    args: tuple,
    owner: tuple[obj, type[obj]] | None,
) -> Callable[[Resolver], obj] | None:
    """Handle subscripted ptr types like ptr["Node"] or ptr[SomeType]."""
    target = args[0] if args else None

    if target is None:
        field = PtrField(None)
        return field.inflate

    if isinstance(target, type):
        field = PtrField(target)
        field.backing_type = registry.inflater_for(target)
        return field.inflate

    # String or ForwardRef: use lazy resolution
    if isinstance(target, str):
        target = ForwardRef(target)

    if isinstance(target, ForwardRef):
        lazy_field = _LazyPtrField(target, owner)
        return lazy_field.inflate

    field = PtrField(None)
    return field.inflate


def _forward_ref_inflater(
    forward_ref: ForwardRef,
    _: type[obj],
    owner: tuple[obj, type[obj]] | None,
) -> Callable[[Resolver], obj]:
    """Handle bare ForwardRef annotations that couldn't be resolved at annotation time."""
    forward_arg = forward_ref.__forward_arg__

    # Check if it's a ptr forward reference (e.g., from `from __future__ import annotations`
    # where ptr wasn't in scope)
    if forward_arg.startswith("ptr[") and forward_arg.endswith("]"):
        inner_type = forward_arg[4:-1]
        if (inner_type.startswith("'") and inner_type.endswith("'")) or (
            inner_type.startswith('"') and inner_type.endswith('"')
        ):
            inner_type = inner_type[1:-1]

        target_ref = ForwardRef(inner_type)
        lazy_field = _LazyPtrField(target_ref, owner)
        return lazy_field.inflate

    raise ValueError(
        f"Cannot resolve forward reference '{forward_arg}'. "
        f"Ensure the type is imported and available in the module scope.",
    )


registry.register_generic_handler(ptr, _subscripted_ptr_handler)
registry.register_instance_handler(ForwardRef, _forward_ref_inflater)

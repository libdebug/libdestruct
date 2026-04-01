#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.obj import obj

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.backing.resolver import Resolver


class union(obj):
    """A union value, supporting both tagged (single active variant) and plain (all variants overlaid) modes."""

    _variant: obj | None
    """The single active variant (tagged union mode)."""

    _variants: dict[str, obj]
    """Named variants (plain union mode)."""

    _frozen_bytes: bytes | None
    """The frozen bytes of the full union region."""

    def __init__(
        self: union,
        resolver: Resolver | None,
        variant: obj | None,
        max_size: int,
        variants: dict[str, obj] | None = None,
    ) -> None:
        """Initialize the union.

        Args:
            resolver: The backing resolver.
            variant: The single active variant (tagged union mode, None for plain unions).
            max_size: The size of the union (max of all variant sizes).
            variants: Named variants dict (plain union mode, None for tagged unions).
        """
        super().__init__(resolver)
        self._variant = variant
        self._variants = variants or {}
        self.size = max_size
        self._frozen_bytes = None

    @property
    def variant(self: union) -> obj | None:
        """Return the active variant object (tagged union mode)."""
        return self._variant

    def get(self: union) -> object:
        """Return the value of the active variant."""
        if self._variant is not None:
            return self._variant.get()
        if self._variants:
            return {name: v.get() for name, v in self._variants.items()}
        return None

    def _set(self: union, value: object) -> None:
        """Set the value of the active variant."""
        if self._variant is None:
            raise RuntimeError("Cannot set the value of a union without an active variant.")
        self._variant._set(value)

    def to_bytes(self: union) -> bytes:
        """Return the full union-sized region as bytes."""
        if self._frozen_bytes is not None:
            return self._frozen_bytes
        if self.resolver is None:
            return b"\x00" * self.size
        return self.resolver.resolve(self.size, 0)

    def freeze(self: union) -> None:
        """Freeze the union and all its variants."""
        if self.resolver is not None:
            self._frozen_bytes = self.resolver.resolve(self.size, 0)
        else:
            self._frozen_bytes = b"\x00" * self.size
        if self._variant is not None:
            self._variant.freeze()
        for v in self._variants.values():
            v.freeze()
        super().freeze()

    def to_str(self: union, indent: int = 0) -> str:
        """Return a string representation of the union."""
        if self._variant is not None:
            return self._variant.to_str(indent)
        if self._variants:
            members = ", ".join(self._variants)
            return f"union({members})"
        return "union(empty)"

    def __getattr__(self: union, name: str) -> object:
        """Delegate attribute access to named variants or the active variant."""
        variants = object.__getattribute__(self, "_variants")
        if name in variants:
            return variants[name]
        variant = object.__getattribute__(self, "_variant")
        if variant is not None:
            return getattr(variant, name)
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations


def format_hexdump(
    data: bytes,
    base_address: int = 0,
    annotations: dict[int, str] | None = None,
) -> str:
    """Format a classic hex dump of the given data.

    Args:
        data: The bytes to dump.
        base_address: The starting address shown in the offset column.
        annotations: Optional mapping from byte offset to field name, shown in the margin.

    Returns:
        A formatted hex dump string.
    """
    lines = []
    for offset in range(0, len(data), 16):
        chunk = data[offset : offset + 16]
        addr = base_address + offset

        hex_parts = " ".join(f"{b:02x}" for b in chunk)
        # Pad to full 16-byte width
        hex_parts = hex_parts.ljust(47)

        ascii_parts = "".join(chr(b) if chr(b).isprintable() and b < 128 else "." for b in chunk)  # noqa: PLR2004

        line = f"{addr:08x}  {hex_parts}  |{ascii_parts}|"

        # Add field annotations for this line
        if annotations:
            fields_on_line = [
                name for byte_offset, name in sorted(annotations.items()) if offset <= byte_offset < offset + 16
            ]
            if fields_on_line:
                line += "  " + ", ".join(fields_on_line)

        lines.append(line)

    return "\n".join(lines)

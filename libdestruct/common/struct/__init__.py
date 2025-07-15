#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from libdestruct.common.ptr.ptr_factory import ptr_to, ptr_to_self
from libdestruct.common.struct.struct import struct
from libdestruct.common.struct.struct_impl import struct_impl

__all__ = ["ptr_to", "ptr_to_self", "struct", "struct_impl"]

import libdestruct.common.ptr.ptr_field_inflater
import libdestruct.common.struct.struct_inflater  # noqa: F401

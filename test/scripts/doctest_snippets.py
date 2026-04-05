#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

"""Test that all documentation code snippets execute without errors."""

import glob
import os
import unittest

from mktestdocs import check_md_file

# Resolve docs/ relative to the repo root, not the working directory.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Files that contain code blocks requiring unavailable system tools
# (e.g., C preprocessor for #include directives) or intentionally
# erroneous code (e.g., demonstrating ValueError on invalid input).
SKIP_FILES = {
    os.path.join(_REPO_ROOT, "docs/advanced/c_parser.md"),
}


def _make_test(fpath):
    def test_func(self):
        check_md_file(fpath, memory=True)

    test_func.__doc__ = f"Snippets in {fpath} execute without errors"
    return test_func


class DocSnippetTest(unittest.TestCase):
    """Auto-generated tests for documentation code snippets."""


for _path in sorted(glob.glob(os.path.join(_REPO_ROOT, "docs/**/*.md"), recursive=True)):
    if _path in SKIP_FILES:
        continue
    _name = "test_" + os.path.relpath(_path, _REPO_ROOT).replace("/", "_").replace(".", "_").replace("-", "_")
    setattr(DocSnippetTest, _name, _make_test(_path))


if __name__ == "__main__":
    unittest.main()

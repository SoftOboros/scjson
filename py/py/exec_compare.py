"""
Agent Name: python-exec-compare-wrapper

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve()
    parent = here.parents[1]
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    import exec_compare as real  # type: ignore
    real.main()


if __name__ == "__main__":
    main()


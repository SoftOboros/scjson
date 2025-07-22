"""
Agent Name: json-stream-decoder

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

from __future__ import annotations

import json
import sys
from typing import TextIO, Iterator, Any


class JsonStreamDecoder:
    """Buffered JSON stream parser for newline-free object streams."""

    def __init__(self, stream: TextIO, chunk_size: int = 4096) -> None:
        self.stream = stream
        self.chunk_size = chunk_size
        self.buffer = ""

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return self._parse_stream()

    def _parse_stream(self) -> Iterator[dict[str, Any]]:
        while True:
            chunk = self.stream.read(self.chunk_size)
            if not chunk:
                break
            self.buffer += chunk
            messages, self.buffer = self._extract_json_objects(self.buffer)
            for msg in messages:
                try:
                    yield json.loads(msg)
                except json.JSONDecodeError:
                    print(f"[JsonStreamDecoder] Invalid JSON: {msg!r}", file=sys.stderr)
        if self.buffer.strip():
            print("[JsonStreamDecoder] Discarding incomplete message", file=sys.stderr)

    @staticmethod
    def _extract_json_objects(buffer: str) -> tuple[list[str], str]:
        """Return a list of complete JSON objects and the remaining buffer."""
        objs: list[str] = []
        brace = 0
        in_str = False
        escape = False
        start = 0

        for idx, ch in enumerate(buffer):
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_str = not in_str
            if not in_str:
                if ch == "{":
                    if brace == 0:
                        start = idx
                    brace += 1
                elif ch == "}":
                    brace -= 1
                    if brace == 0:
                        objs.append(buffer[start : idx + 1])
                        start = idx + 1
        remainder = buffer[start:]
        return objs, remainder

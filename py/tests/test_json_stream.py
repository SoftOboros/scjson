"""
Agent Name: json-stream-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

from __future__ import annotations

import io
from scjson.json_stream import JsonStreamDecoder


def test_decoder_minified():
    """Parse minified messages delivered in small chunks."""
    data = '{"event":"a"}{"event":"b"}{"event":"c"}'
    decoder = JsonStreamDecoder(io.StringIO(data), chunk_size=5)
    events = [m["event"] for m in decoder]
    assert events == ["a", "b", "c"]


def test_decoder_pretty():
    """Parse pretty-printed messages with whitespace and newlines."""
    data = '{\n  "event": "x"\n}\n{\n  "event": "y",\n  "data": {"z": 1}\n}\n'
    decoder = JsonStreamDecoder(io.StringIO(data), chunk_size=7)
    msgs = list(decoder)
    assert msgs[0]["event"] == "x"
    assert msgs[1] == {"event": "y", "data": {"z": 1}}


def test_decoder_invalid_and_partial(capsys):
    """Ignore invalid JSON and discard trailing partial data."""
    data = '{"event":"a"}{"event":bad}{"event":"c"'
    decoder = JsonStreamDecoder(io.StringIO(data), chunk_size=9)
    results = list(decoder)
    captured = capsys.readouterr()
    assert results == [{"event": "a"}]
    assert "Discarding incomplete" in captured.err


def test_extract_helper():
    """Validate the _extract_json_objects utility."""
    buf = '{"name":"t"}{"name":"u"}{'
    msgs, buf = JsonStreamDecoder._extract_json_objects(buf)
    assert msgs == ['{"name":"t"}', '{"name":"u"}']
    assert buf == '{'


"""
Agent Name: python-engine-cli-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Basic tests for CLI engine-trace handling of control tokens in the
events stream (per-step time advancement).
"""

from __future__ import annotations

from pathlib import Path
import json

from click.testing import CliRunner
from scjson.cli import main


def _chart_noop() -> str:
    """Return a minimal SCXML chart that accepts a single external event.

    The chart has no timers; this keeps assertions simple while verifying
    that the CLI tolerates advance_time control tokens in the event stream.

    Returns
    -------
    str
        SCXML document as a string.
    """
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <transition event="go" target="done"/>
          </state>
          <final id="done"/>
        </scxml>
        """
    ).strip()


def test_engine_trace_accepts_advance_time_token(tmp_path: Path) -> None:
    """engine-trace should accept {"advance_time": N} lines without error.

    The control tokens must not create additional trace steps; only lines
    with an actual "event" should increment the step counter.
    """
    chart = tmp_path / "basic.scxml"
    chart.write_text(_chart_noop(), encoding="utf-8")
    events_file = tmp_path / "basic.events.jsonl"
    # Two advance_time control tokens surrounding one event
    events = [
        {"advance_time": 0.1},
        {"event": "go"},
        {"advance_time": 0.2},
    ]
    events_file.write_text("\n".join(json.dumps(o) for o in events), encoding="utf-8")
    out_file = tmp_path / "trace.jsonl"

    # Invoke via CLI runner and ensure no extra steps are emitted for control tokens
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "engine-trace",
            "-I",
            str(chart),
            "-e",
            str(events_file),
            "--xml",
            "-o",
            str(out_file),
        ],
    )
    assert result.exit_code == 0, result.output

    lines = [l for l in out_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    # Expect exactly 2 trace lines: step 0 and the single event step
    assert len(lines) == 2
    step0 = json.loads(lines[0])
    step1 = json.loads(lines[1])
    assert step0.get("step") == 0
    assert step1.get("step") == 1
    assert step1.get("event", {}).get("name") == "go"

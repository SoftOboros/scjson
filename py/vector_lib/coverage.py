"""
Agent Name: python-vector-coverage

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Coverage accounting for engine traces generated during vector simulation.
"""

from __future__ import annotations

from typing import Dict, Iterable, Set, Tuple


class CoverageTracker:
    """Accumulate simple coverage metrics from engine traces.

    The tracker records:
    - Unique entered state IDs
    - Unique fired transitions as (source, tuple(sorted(targets)))
    - Done events observed (names starting with done.)
    - Error events observed (names starting with error.)
    """

    def __init__(self) -> None:
        self.entered_states: Set[str] = set()
        self.fired_transitions: Set[Tuple[str, Tuple[str, ...]]] = set()
        self.done_events: Set[str] = set()
        self.error_events: Set[str] = set()

    def add_step(self, trace: Dict) -> None:
        """Add a single engine trace entry to the coverage.

        Parameters
        ----------
        trace : dict
            Engine trace entry (from DocumentContext.trace_step).
        """
        for s in trace.get("enteredStates", []) or []:
            self.entered_states.add(str(s))
        for tr in trace.get("firedTransitions", []) or []:
            src = str(tr.get("source"))
            tgts = tuple(sorted(str(t) for t in (tr.get("targets") or [])))
            self.fired_transitions.add((src, tgts))
        evt = trace.get("event") or {}
        name = evt.get("name") if isinstance(evt, dict) else None
        if isinstance(name, str):
            if name.startswith("done."):
                self.done_events.add(name)
            if name.startswith("error"):
                self.error_events.add(name)

    def size(self) -> int:
        """Return a scalar size metric of current coverage."""
        return (
            len(self.entered_states)
            + len(self.fired_transitions)
            + len(self.done_events)
            + len(self.error_events)
        )

    def summary(self) -> Dict[str, int]:
        """Return a summary of coverage counts."""
        return {
            "enteredStates": len(self.entered_states),
            "firedTransitions": len(self.fired_transitions),
            "doneEvents": len(self.done_events),
            "errorEvents": len(self.error_events),
        }


<p align="center"><img src="../../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: conv-i-lua-parity-audit

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# CONV-I Lua Parity Audit

## Section 0. Authority Policy

This is a converter-parity audit record for the Lua implementation
(`lua/`), a companion to `SCJSON-CONV-00-CONCEPTS.md` CONV-I ("Language
Propagation, Corpus, and Reference Gates"). It satisfies the Roadmap step 0
prerequisite named in `docs/TODO-ENGINE-LUA.md` ("Audit the current
'minimal subset converter' against the tutorial corpus; file gaps as
CONV-family backlog items, not here") and is the CONV-family destination
that step 0 asked for.

This document does not amend CONV-00's frozen invariants or field
registry. Gaps found here are backlog items against the existing CONV-E/F/H
surfaces already accepted in `SCJSON-CONV-00-CONCEPTS.md`; they do not
propose new schema fields.

Normative sections: Section 4 and Section 5.

Informative sections: Section 1, Section 2, Section 3, Section 6, and
Section 7.

## Section 1. Audit Context

`docs/COMPATIBILITY.md` rates Lua **Experimental** ("minimal subset
converter"), the lowest tier of the nine language implementations — Go,
Swift, and C# are Beta by comparison. `docs/TODO-ENGINE-LUA.md` (EXEC-J,
full execution-engine parity) makes converter parity a prerequisite: engine
traces are only meaningful once the underlying SCJSON documents parse
correctly, and CONV-I's own problem statement warns that "corpus entries
that exercise converter-only surfaces... MUST NOT be misclassified as
execution-conformance failures." This audit exists to separate the two
concerns before any Lua engine-trace work is scheduled.

Scope: `lua/scjson.lua` (the converter library), `lua/bin/scjson` (the CLI
entry point), and `lua/tests/scjson_spec.lua` (the existing test suite),
read against `scjson.schema.json` and the CONV-E ("Help Text"), CONV-F
("SCXML Comment Promotion"), CONV-G (extension metadata registry), and
CONV-H (root-reachable chart inclusion / XInclude) surfaces that
`SCJSON-CONV-00-CONCEPTS.md` Section 7 already marks accepted for Python
and JavaScript.

## Section 2. Method Note

This audit is a **static code-level review**, not a live harness run. The
environment used to perform it has no Lua 5.4 runtime (`choco search lua`
lists `lua51`/`lua52`/`lua53` but no `lua54`), no `luaexpat`/`dkjson`
packages, and no Docker (the project's own `Dockerfile` provides "a full
development environment for all supported languages," but Docker itself is
unavailable here). `python py/uber_test.py -l lua` could not be executed.

Findings below are derived from reading `lua/scjson.lua` in full
(652 lines) against the schema and the CONV-E/F/G/H text, plus the existing
`lua/tests/scjson_spec.lua` (29 lines, two specs). They are high-confidence
because the absence of matching identifiers (`help_text`, `other_attributes`,
`comment`, `xinclude`) was confirmed by exhaustive grep across `lua/`, not by
sampling. They are not a substitute for the live `uber_test.py -l lua` gate
that CONV-I's acceptance criteria ultimately require (see LUA-CONV-G6,
Section 4) — that gate needs a runtime this environment does not have.

## Section 3. Findings Inventory

### L1: No `other_attributes` / `other_element` structural surface

`scjson.schema.json` defines `other_attributes` and/or `other_element` on
essentially every element type (20+ occurrences across the file). The Lua
converter has no equivalent field. Unrecognized XML attributes on a known
element are merged directly into the flat map as top-level keys
(`lua/scjson.lua:178-206`, specifically the fallthrough `else map[k] = v end`
at line 205). Unrecognized child elements are folded into the generic
`content` array via `any_element_to_value` (`lua/scjson.lua:132-157`,
invoked at line 273) rather than populated under a distinct `other_element`
field. Net effect: Lua output does not use the same structural shape as
Python/JavaScript for extension attributes or foreign elements, even though
content-folding is a partial (not schema-conformant-shape) mitigation.

### L2: No `help_text` support (CONV-E gap)

Zero occurrences of `help_text` anywhere under `lua/`. CONV-E ("Help Text")
is marked accepted for Python and JavaScript in `SCJSON-CONV-00-CONCEPTS.md`
Section 7; Lua does not parse, preserve, or emit it.

### L3: No SCXML comment promotion (CONV-F gap)

Zero occurrences of "comment" anywhere under `lua/`. `lom.parse`
(`lxp.lom`, `lua/scjson.lua:16`) is not known to expose comment nodes to
`element_to_map`, and no pre/post-pass equivalent to
`py/scjson/comment_promotion.py` or `js/src/comment_promotion.js` exists.
CONV-F is marked complete for Python and JavaScript only; Lua was never in
scope for that work package and remains at zero.

### L4: No XInclude preserve/resolve handling (CONV-H/CONV-I gap)

Zero occurrences of "xinclude" or "xi:include" anywhere under `lua/`.
CONV-I's corpus policy explicitly requires "XInclude preserve/resolve
behavior" coverage in the checked-in corpus and names it as a surface
maintained-language converters are evaluated against. Lua has no handling
of either mode.

### L5: Minimal test coverage corroborates the Experimental rating

`lua/tests/scjson_spec.lua` has exactly two specs (lines 13 and 21): a bare
`<scxml xmlns="..."/>` round-trip asserting default `version`/
`datamodel_attribute`, and a flat single-state round-trip asserting a
`"state"` key exists in the re-serialized JSON string. There is no test
coverage for nested states, `parallel`/`history`/`invoke`/`finalize`,
`datamodel`/`data`, `donedata`, `send`/`param`, or any of L1-L4's surfaces.
This is consistent with — and gives concrete evidence for —
`docs/COMPATIBILITY.md` rating Lua "Experimental: minimal subset
converter" rather than Beta.

### L6: No gap — reserved-keyword field aliasing is correct

`lua/scjson.lua:189-227` (attribute-side: `type` → `type_value`,
`initial` → `initial_attribute`/`initial` depending on element, `datamodel`
→ `datamodel_attribute`; child-element-side: `if`/`else`/`raise` → `if_value`
/`else_value`/`raise_value` at lines 236-240) matches the canonical naming
registry in `SCJSON-CONV-00-CONCEPTS.md` Section 3 ("XML Element Name vs.
SCJSON Field Name") exactly. No action needed; noted here so a future
implementer doesn't waste time re-auditing it.

### L7: No gap — token-list handling is correct

`transition.target` and `scxml`/root `initial` are split into arrays
(`lua/scjson.lua:181-188`, using `split_tokens` at line 163), matching
CONV-INV-3 ("Token attributes such as transition `target` and state/root
`initial` MUST be split into arrays where the schema marks token lists").
No action needed.

### L8: Harness wiring exists but is unconfirmed live

`py/uber_test.py` already has a `LANG_CMDS["lua"]` entry pointing at
`lua/bin/scjson` directly (no build step required, unlike Go/C#/Swift), so
harness wiring is not itself a gap. However, per the Section 2 method note,
this audit could not confirm what `uber_test.py -l lua` actually reports
against the tutorial corpus, because no Lua runtime was available. This is
tracked as LUA-CONV-G6 (Section 4), not folded into L1-L5 above.

## Section 4. CONV-I Lua Sub-Gates

| Gate | Decision | Rationale |
|------|----------|-----------|
| LUA-CONV-G1 | Accept | Add `other_attributes`/`other_element` structural support (L1), matching the schema shape rather than flattening unknowns into top-level keys or folding them into `content`. |
| LUA-CONV-G2 | Accept | Add `help_text` parse/emit support (L2), mirroring the Python/JavaScript CONV-E behavior. |
| LUA-CONV-G3 | Accept | Add SCXML comment promotion (L3), mirroring `py/scjson/comment_promotion.py` / `js/src/comment_promotion.js` pre/post-pass structure per CONV-F and CONV-INV-8 (deterministic across Python and JavaScript; Lua would be a third implementation and MUST match the same promoted-value semantics, not invent its own). |
| LUA-CONV-G4 | Accept | Add XInclude preserve-mode handling at minimum (L4); resolve-mode MAY be deferred to a follow-up gate if preserve-mode alone unblocks corpus parity. |
| LUA-CONV-G5 | Accept | Expand `lua/tests/scjson_spec.lua` to cover nested states, `parallel`/`history`/`invoke`/`finalize`, `datamodel`/`data`, `donedata`, and `send`/`param` (L5) before any tier change is claimed in `docs/COMPATIBILITY.md`. |
| LUA-CONV-G6 | Defer | Live confirmation via `python py/uber_test.py -l lua` against the tutorial corpus. Blocked on Lua 5.4 + `luaexpat` + `dkjson` runtime availability (not present in this audit's environment; no Docker fallback either). Whoever picks up LUA-CONV-G1..G5 implementation MUST also run this gate before claiming any status-tier change. |

Registration policy: **Specification Required** — these are CONV-I
sub-gates, not new frozen invariants; a PR-level note updating this table's
status is sufficient when a gate lands. Do not silently mark
`docs/COMPATIBILITY.md`'s Lua row as anything other than Experimental until
LUA-CONV-G1 through LUA-CONV-G6 all land.

## Section 5. Backlog Classification Summary

Accepted as CONV-I Lua backlog (converter-parity prerequisite for EXEC-J):

- LUA-CONV-G1 other_attributes/other_element structural support.
- LUA-CONV-G2 help_text support.
- LUA-CONV-G3 SCXML comment promotion.
- LUA-CONV-G4 XInclude preserve-mode support (resolve-mode may follow).
- LUA-CONV-G5 expanded test corpus covering nested/compound constructs.

Deferred (blocked on environment, not scope):

- LUA-CONV-G6 live `uber_test.py -l lua` confirmation pass.

Not gaps (verified correct, no backlog item):

- Reserved-keyword field aliasing (L6).
- Token-list splitting for `target`/`initial` (L7).

Out of scope for this audit (belongs to EXEC-J, not CONV-I):

- Execution/trace engine work of any kind. This audit only covers
  converter (SCXML ↔ SCJSON) fidelity, per `docs/TODO-ENGINE-LUA.md`
  Roadmap step 0's own scoping note ("file gaps as CONV-family backlog
  items, not here").

## Section 6. Files Cited

- `lua/scjson.lua` (full file read; key lines: 16-19 dependencies, 41-68
  `SCXML_ELEMS`, 132-157 `any_element_to_value`, 163-169 `split_tokens`,
  175-303 `element_to_map`, 178-227 attribute handling and reserved-keyword
  aliasing, 234-271 child-element handling, 421-551 `map_to_element`)
- `lua/bin/scjson` (CLI usage/commands, lines 32-46)
- `lua/tests/scjson_spec.lua` (both specs, lines 13 and 21)
- `lua/README.md` (runtime dependency list: `lua5.4`, `luaexpat`, `dkjson`)
- `scjson.schema.json` (`other_attributes`/`other_element` occurrences)
- `docs/COMPATIBILITY.md` (Lua rated Experimental)
- `docs/TODO-ENGINE-LUA.md` (EXEC-J checklist; Roadmap step 0 origin of this
  audit)
- `docs/concepts/SCJSON-CONV-00-CONCEPTS.md` (Section 3 field-name registry,
  Section 4 frozen invariants, Section 6 CONV-I work package)
- `py/uber_test.py` (`LANG_CMDS["lua"]` entry)

## Section 7. Change Log

- 2026-07-05: Initial Lua converter-parity audit. Six findings (L1-L5, L8)
  plus two confirmed non-gaps (L6, L7); six CONV-I sub-gates opened
  (LUA-CONV-G1..G6), five accepted as backlog and one (G6, live harness
  confirmation) deferred on runtime availability. No implementation code
  changed as part of this audit.

---

Back to
- Converter Concepts: `docs/concepts/SCJSON-CONV-00-CONCEPTS.md`
- Lua Engine Checklist: `docs/TODO-ENGINE-LUA.md`
- Compatibility Matrix: `docs/COMPATIBILITY.md`

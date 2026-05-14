<p align="center"><img src="../../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: pyrel-037-backlog-grooming

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# PYREL-037 Backlog Grooming Session

## Section 0. Authority Policy

This is a backlog grooming record for the `release/0.3.7-py` branch. It is a
companion to `docs/concepts/SCJSON-00-CONCEPTS.md` and applies the new
spec-before-code discipline to the Python release backlog and existing TODO
docs.

Normative sections: Section 4, Section 5, Section 6, Section 7, Section 8, and
Section 10.

Informative sections: Section 1, Section 2, Section 3, Section 9, Section 11,
and Section 12.

## Section 1. Session Context

Branch: `release/0.3.7-py`

Compared against local `main`, the branch contains three commits:

- `3b14a64 fix(py): root activation no longer collides with state ids of same name`
- `1f9845f fix(pydantic): loosen other_attributes typing to dict[str, Any]`
- `749cd56 SBC: Intialize Spec Before Code discipline`

The branch is Python-release shaped, but it changes shared semantics that
matter to the Python language surface:

- Python engine root activation identity.
- Pydantic validation behavior for `other_attributes`.
- Repository-level spec-before-code governance and frozen decision inventory.

## Section 2. Release Delta Inventory

### Delta D1: Python version and changelog

`py/pyproject.toml` moves the Python package from `0.3.6` to `0.3.7`.
`py/CHANGELOG.md` and top-level `CHANGELOG.md` were added.

Release effect: accepted for 0.3.7, but the changelog should also mention the
pydantic `other_attributes` fix before release because the branch now contains
that second Python-facing change.

### Delta D2: Root activation sentinel

`py/scjson/context.py` now gives the root activation the sentinel
`__scxml_root__` instead of deriving it from the document `name`.

Release effect: accepted. This fixes a silent trace/configuration bug when
`<scxml name="X">` collides with `<state id="X">`.

Release gap: no focused regression test was found in `py/tests` for the
collision case.

### Delta D3: Pydantic `other_attributes` typed metadata

The pydantic and pydantic_strict generated models now use
`dict[str, Any]` for `other_attributes`. Dataclass models remain
`dict[str, str]`.

Release effect: accepted. This matches JSON usage where downstream tools store
typed metadata on extension attributes.

Release gaps:

- No focused validation regression was found in `py/tests`.
- The new generator patch script should be classified as either a release
  artifact or a source-tree-only maintenance script before packaging.

### Delta D4: Spec-before-code baseline

`AGENTS.md`, `CLAUDE.md`, and `docs/concepts/SCJSON-00-CONCEPTS.md` establish
the semantic baseline.

Release effect: accepted. The baseline should not force archival of old docs
inside this release; it identifies cleanup work for later.

## Section 3. Validation Snapshot

Commands run:

```bash
env PYTHONPATH=py pytest -q py/tests
```

Result:

- 104 passed
- 1 skipped
- 3 failed
- 86 warnings

The failures were:

- `py/tests/test_cli.py::test_recursive_conversion`
- `py/tests/test_cli.py::test_recursive_validation`
- `py/tests/test_cli.py::test_recursive_verify`

Observed cause: the `tutorial` submodule is not initialized locally
(`git submodule status` shows `-a442d41... tutorial`), so recursive conversion
has no input files and does not create the expected output directory.

Follow-up command:

```bash
env PYTHONPATH=py pytest -q py/tests -k 'not recursive'
```

Result:

- 104 passed
- 1 skipped
- 3 deselected
- 83 warnings

Interpretation: no non-recursive Python test regression was observed in this
workspace. The release still needs either initialized submodules for final
validation or test skips/guards that make missing tutorial data explicit.

## Section 4. Python 0.3.7 Release Gates

The following items are accepted release gates for 0.3.7.

| Gate | Decision | Rationale |
|------|----------|-----------|
| PYREL-037-G1 | Accept | Add a focused regression test for `<scxml name="X">` plus `<state id="X">` showing observable configuration and transitions keep the user state. |
| PYREL-037-G2 | Accept | Add focused pydantic and pydantic_strict tests proving typed `other_attributes` values validate. |
| PYREL-037-G3 | Accept | Confirm dataclass models intentionally remain `dict[str, str]` and document that split in release notes or tests. |
| PYREL-037-G4 | Accept | Update `py/CHANGELOG.md` and top-level `CHANGELOG.md` to mention the pydantic `other_attributes` fix. |
| PYREL-037-G5 | Accept | Decide whether `py/patch_other_attributes_any.py`, `py/patch_scxml_forward_ref.py`, and `py/gen_models.sh` belong in the Python sdist/wheel source surface. If yes, add packaging manifest coverage. If no, document them as repository-only generation tools. |
| PYREL-037-G6 | Accept | Run final validation with an initialized `tutorial` submodule, or make recursive tutorial tests skip clearly when tutorial data is absent. Initialize other submodules only if the chosen validation profile requires them. |
| PYREL-037-G7 | Accept | Correct `docs/ENGINE-PY.md` time-control wording so it matches the current CLI default: `advance_time` control tokens do not emit trace steps unless `--emit-time-steps` is set. |

## Section 5. Existing TODO Inventory: Python Engine

Source doc: `docs/TODO-ENGINE-PY.md`.

### Accepted for 0.3.7 release cleanup

| TODO area | Decision | Notes |
|-----------|----------|-------|
| Review `ENGINE_KNOWN_UNSUPPORTED` | Accept | Required by the TODO itself and relevant to release confidence. The current unsupported list is small and optional-W3C-only, but should be explicitly retained or reduced. |
| Stock corpus validation | Accept | Keep as a release validation gate, but it depends on initialized submodules. |
| Documentation update | Accept | The time-control contradiction is a concrete doc bug created before the new baseline. |
| Trace/schema checklist status | Accept | Several top-level unchecked goals are now partially or fully landed. Rebaseline rather than leaving broad false negatives. |

### Accepted, but moved to a larger initiative

| TODO area | Decision | Notes |
|-----------|----------|-------|
| Invoke/finalize ordering investigation | Defer | This is cross-engine behavioral policy. It needs a spec-before-code phase before more ordering changes. |
| Vector generation Phase 3 | Defer | Parallel/invoke minimization is real work, but not a 0.3.7 bugfix gate. |
| Deterministic ordering where SCXML permits implementation choice | Defer | Too broad for this release. Fold into an execution-semantics concepts doc. |
| CI full corpus zero-mismatch gate | Defer | Desirable, but not a blocker for a focused Python bugfix release unless the release owner declares it mandatory. |

### Rejected for this release

| TODO area | Decision | Notes |
|-----------|----------|-------|
| Apache Commons SCXML comparison wrapper | Reject for 0.3.7 | SCION is already the behavioral reference under `SCJSON-00`. Apache Commons may remain historical research, not a Python release gate. |
| Java runner wrapper preferred path | Reject for 0.3.7 | The Node/SCION wrapper is already the accepted reference path. |
| Re-implement already landed broad milestones M1-M4 | Reject as written | These broad milestone boxes are stale. Replace with narrower conformance gates instead of treating them as outstanding implementation work. |

## Section 6. Existing TODO Inventory: Ruby Engine

Source doc: `docs/TODO-ENGINE-RUBY.md`.

Ruby engine work is out of scope for the Python 0.3.7 release. The Ruby TODO
doc remains useful as backlog input, but it should not drive Python release
gates.

### Accepted for future Ruby initiative grooming

- Full macrostep loop and conflict resolution.
- Error handling and ordering parity with SCION.
- CI subset against SCION and Python.
- Ruby-specific corpus for multi-document invoke/finalize.
- Expression, timer, and finalize-ordering policy.

### Accepted as TODO cleanup, not release work

Several Ruby items are already landed but still unchecked or duplicated:

- Dedicated Ruby guide exists.
- Ruby details doc exists.
- README Ruby sections appear to have landed.
- Version bump to 0.3.5 appears to have landed.
- Secondary-engine harness integration appears to exist through
  `--secondary "ruby/bin/scjson engine-trace"`.

These should be rechecked or rewritten in a Ruby-specific backlog pass.

### Rejected for Python 0.3.7

All Ruby packaging, RubyGems metadata, Ruby corpus, and Ruby trace-parity items
are rejected as blockers for this Python release. They may be accepted in a
future Ruby release spec.

## Section 7. Localized TODO Docs

Localized TODO docs existed under:

- `en-US/docs/`
- `fr-CA/docs/`
- `es-MX/docs/`

Decision: reject localized TODO files as planning authority and remove the
localized documentation trees from this repository. Root `docs/TODO-*` files
own backlog state. Translated publication is provided by softoboros.com through
submodule inclusion and should not feed back localized planning copies here.

## Section 8. Backlog Classification Summary

Accepted for Python 0.3.7:

- Root activation collision test.
- Typed pydantic `other_attributes` tests.
- Changelog coverage for both Python fixes.
- Packaging decision for generator patch scripts.
- Final validation with submodules or explicit missing-submodule skips.
- Python engine guide time-control correction.
- Review of `ENGINE_KNOWN_UNSUPPORTED`.

Deferred to larger spec-before-code initiatives:

- Invoke/finalize ordering policy.
- Vector generation Phase 3 and minimization.
- Full corpus CI zero-mismatch policy.
- Cross-engine deterministic ordering where SCXML is implementation-defined.
- Ruby engine conformance.

Rejected as 0.3.7 blockers:

- Apache Commons wrapper.
- Java reference runner replacement.
- Ruby release work.
- Locale TODO grooming as an independent source of truth.
- Broad stale milestone boxes that no longer correspond to concrete work.

## Section 9. Proposed Next Spec Documents

This grooming session produced the following child planning docs:

- `SCJSON-CONV-00-CONCEPTS.md`: converter representation, structural fields,
  attribute aliases, tokenization, and unknown extension handling.
- `SCJSON-EXEC-00-CONCEPTS.md`: execution trace semantics, ordering modes,
  error/done event families, invoke/finalize policy, and normalization
  boundaries.
- `SCJSON-WORKSTREAMS-00-MANAGER-MAP.md`: explicit dependency graph and
  manager-ready worker scopes.

These should be accepted and used as the manager's working context before
archiving or heavily rewriting the old inference and engine docs.

## Section 10. Acceptance Checklist

- [x] Branch delta against `main` inventoried.
- [x] Python release gates accepted.
- [x] Existing root TODO docs inventoried.
- [x] Python TODO items classified as accept, defer, or reject for 0.3.7.
- [x] Ruby TODO items classified as out of scope for Python 0.3.7.
- [x] Localized TODO docs classified as non-authoritative planning copies.
- [x] Localized documentation trees removed from the repository source surface.
- [ ] Implement accepted Python 0.3.7 release gates.
- [ ] Rebaseline `docs/TODO-ENGINE-PY.md` after accepted release gates land.
- [ ] Reconcile old docs with `SCJSON-00-CONCEPTS.md` before archiving.

## Section 11. Files Cited

- `CHANGELOG.md`
- `docs/TODO-ENGINE-PY.md`
- `docs/TODO-ENGINE-RUBY.md`
- `docs/concepts/SCJSON-CONV-00-CONCEPTS.md`
- `docs/concepts/SCJSON-EXEC-00-CONCEPTS.md`
- `docs/concepts/SCJSON-WORKSTREAMS-00-MANAGER-MAP.md`
- `docs/concepts/SCJSON-00-CONCEPTS.md`
- `py/CHANGELOG.md`
- `py/gen_models.sh`
- `py/patch_other_attributes_any.py`
- `py/patch_scxml_forward_ref.py`
- `py/pyproject.toml`
- `py/scjson/context.py`
- `py/scjson/pydantic/generated.py`
- `py/scjson/pydantic_strict/generated.py`
- `py/tests/test_cli.py`

## Section 12. Change Log

- 2026-05-14: Initial backlog grooming record for Python 0.3.7 release branch.
- 2026-05-14: Added localized-doc removal decision and manager workstream
  split.

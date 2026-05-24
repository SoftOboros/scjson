"""
Agent Name: help-text-round-trip-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

CONV-E acceptance tests for the first-class ``help_text`` field. See
``docs/concepts/SCJSON-CONV-00-CONCEPTS.md`` (CONV-INV-7, CONV-E) for the
normative contract these tests pin.

Scope:

- Schema/model surface: pydantic, pydantic_strict, dataclasses, and
  dataclasses_strict generated models expose ``help_text: list[str]`` on every
  SCJSON element family named in CONV-E.
- JSON round-trip semantics: entry order preserved, single-entry arrays never
  collapsed to scalars, empty arrays omitted from canonical JSON when
  ``omit_empty=True`` is set on :class:`SCXMLDocumentHandler`.
- Independence from ``other_attributes``: ``help_text`` lives in its own field
  and never leaks into the extension bag.
- Canonical schema artifacts: ``scjson.schema.json``, ``js/scjson.schema.json``,
  and ``java/src/main/resources/scjson.schema.json`` agree on ``help_text``.

XML round-trip note (CONV-E vs CONV-F): the patched generated models tag
``help_text`` with xsdata ``metadata={"type": "Ignore"}``, so the xsdata XML
serializer/parser does not emit or consume ``help_text`` as an SCXML element
or attribute. SCXML comment promotion into ``help_text`` is owned by CONV-F
and lands in a follow-up. Tests in this module exercise the JSON-side
contract that CONV-E commits to today.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import scjson.dataclasses as dataclass_models
import scjson.dataclasses_strict as strict_dataclass_models
import scjson.pydantic as pydantic_models
import scjson.pydantic_strict as strict_pydantic_models
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler


# Frozen by CONV-E: ``help_text`` MUST exist on these SCJSON element families
# and MUST NOT exist on scalar datatype / enumeration models.
APPLIES_TO = [
    "Scxml",
    "State",
    "Parallel",
    "Final",
    "History",
    "Initial",
    "Transition",
    "Onentry",
    "Onexit",
    "Invoke",
    "Finalize",
    "Datamodel",
    "Data",
    "Donedata",
    "Content",
    "Param",
    "Assign",
    "Log",
    "Raise",
    "If",
    "Elseif",
    "Else",
    "Foreach",
    "Send",
    "Cancel",
    "Script",
]

# Enumeration models that must NOT carry ``help_text``.
NOT_APPLIES_TO_ENUMS = [
    "AssignTypeDatatype",
    "BindingDatatype",
    "BooleanDatatype",
    "ExmodeDatatype",
    "HistoryTypeDatatype",
    "TransitionTypeDatatype",
]


ALL_MODEL_MODULES = [
    pydantic_models,
    strict_pydantic_models,
    dataclass_models,
    strict_dataclass_models,
]


# ---------------------------------------------------------------------------
# Field-shape tests (every generated variant).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module", ALL_MODEL_MODULES)
@pytest.mark.parametrize("class_name", APPLIES_TO)
def test_help_text_field_exists_with_list_str_type(module, class_name):
    """Every CONV-E applies-to model exposes ``help_text: list[str]``."""
    cls = getattr(module, class_name)
    hints = get_type_hints(cls)
    assert "help_text" in hints, (
        f"{module.__name__}.{class_name} is missing the CONV-E ``help_text`` field"
    )
    assert hints["help_text"] == list[str], (
        f"{module.__name__}.{class_name}.help_text must be typed list[str]; "
        f"got {hints['help_text']}"
    )


@pytest.mark.parametrize("module", ALL_MODEL_MODULES)
@pytest.mark.parametrize("class_name", APPLIES_TO)
def test_help_text_defaults_to_empty_list(module, class_name):
    """Default constructor produces an empty list, not None or a singleton."""
    cls = getattr(module, class_name)
    # Some models require positional id/etc.; try kwargs that the constructor
    # tolerates, falling back to skipping fields with required attributes.
    try:
        instance = cls()
    except (TypeError, ValueError):
        # Models with required attributes get a minimal valid construction.
        if class_name == "Data":
            instance = cls(id="d1")
        elif class_name == "Assign":
            instance = cls(location="x")
        elif class_name == "Elseif":
            instance = cls(cond="true")
        elif class_name == "Raise":
            instance = cls(event="ev")
        elif class_name == "Param":
            instance = cls(name="p")
        elif class_name == "Foreach":
            instance = cls(array="a", item="i")
        elif class_name == "If":
            instance = cls(cond="true")
        elif class_name in ("History", "Initial"):
            transition_cls = getattr(module, "Transition")
            instance = cls(transition=transition_cls())
        else:
            pytest.skip(
                f"{module.__name__}.{class_name} requires fields this test "
                "does not synthesize"
            )
    assert instance.help_text == []


@pytest.mark.parametrize("module", ALL_MODEL_MODULES)
@pytest.mark.parametrize("class_name", NOT_APPLIES_TO_ENUMS)
def test_enum_models_have_no_help_text(module, class_name):
    """Scalar datatype / enumeration models must not expose ``help_text``."""
    cls = getattr(module, class_name)
    assert not hasattr(cls, "help_text"), (
        f"{module.__name__}.{class_name} is an enum and must not own help_text"
    )


# ---------------------------------------------------------------------------
# Pydantic JSON round-trip tests.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module", [pydantic_models, strict_pydantic_models]
)
def test_pydantic_help_text_accepts_and_preserves_entries(module):
    """Pydantic models accept multi-entry help_text and preserve order."""
    entries = ["first line", "second line", "third line"]
    s = module.Scxml(name="m1", help_text=entries)
    dumped = s.model_dump()
    assert dumped["help_text"] == entries
    # Round-trip via JSON string preserves identity.
    js = json.dumps(dumped, default=str)
    rt = json.loads(js)
    assert rt["help_text"] == entries
    # And validating back into the model preserves the field.
    s2 = module.Scxml.model_validate(rt)
    assert s2.help_text == entries


@pytest.mark.parametrize(
    "module", [pydantic_models, strict_pydantic_models]
)
def test_pydantic_help_text_single_entry_stays_array(module):
    """A one-entry array MUST NOT be collapsed to a scalar."""
    s = module.State(id="S1", help_text=["only one"])
    dumped = s.model_dump()
    assert isinstance(dumped["help_text"], list)
    assert dumped["help_text"] == ["only one"]


@pytest.mark.parametrize(
    "module", [pydantic_models, strict_pydantic_models]
)
def test_pydantic_help_text_distinct_from_other_attributes(module):
    """Setting both fields preserves each independently after round-trip."""
    s = module.Transition(
        event="go",
        help_text=["doc on transition"],
        other_attributes={"position": "1,2"},
    )
    dumped = s.model_dump()
    assert dumped["help_text"] == ["doc on transition"]
    assert dumped["other_attributes"] == {"position": "1,2"}
    # help_text must not leak into other_attributes.
    assert "help_text" not in dumped["other_attributes"]
    # Re-validate.
    rt = module.Transition.model_validate(dumped)
    assert rt.help_text == ["doc on transition"]
    assert rt.other_attributes == {"position": "1,2"}
    assert "help_text" not in rt.other_attributes


# ---------------------------------------------------------------------------
# Dataclasses JSON round-trip tests.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module", [dataclass_models, strict_dataclass_models]
)
def test_dataclass_help_text_round_trip_via_asdict(module):
    """Dataclass models surface help_text through asdict and re-validation."""
    s = module.Scxml(
        name="m1",
        help_text=["root doc"],
        state=[
            module.State(
                id="S1",
                help_text=["state S1 doc"],
                transition=[
                    module.Transition(
                        event="go",
                        target=["S2"],
                        help_text=["t1", "t2"],
                    )
                ],
            )
        ],
    )
    d = asdict(s)
    assert d["help_text"] == ["root doc"]
    assert d["state"][0]["help_text"] == ["state S1 doc"]
    assert d["state"][0]["transition"][0]["help_text"] == ["t1", "t2"]


# ---------------------------------------------------------------------------
# SCXMLDocumentHandler integration: omit_empty + help_text co-existence.
# ---------------------------------------------------------------------------


def test_handler_omit_empty_drops_unset_help_text():
    """``omit_empty=True`` (default) drops empty help_text arrays from canonical JSON.

    The handler builds JSON from the dataclasses model via ``asdict`` then
    runs :py:meth:`SCXMLDocumentHandler._remove_empty`. An untouched
    ``help_text`` is an empty list, which the recursive helper drops.
    """
    xml = (
        '<scxml xmlns="http://www.w3.org/2005/07/scxml" name="m1">'
        '<state id="S1"/></scxml>'
    )
    handler = SCXMLDocumentHandler()
    canonical = json.loads(handler.xml_to_json(xml))
    assert "help_text" not in canonical
    assert "help_text" not in canonical["state"][0]


def test_handler_preserves_help_text_through_remove_empty():
    """``_remove_empty`` keeps non-empty help_text entries intact."""
    s = dataclass_models.Scxml(
        name="m1",
        help_text=["root doc"],
        state=[
            dataclass_models.State(
                id="S1",
                help_text=["state doc"],
                transition=[
                    dataclass_models.Transition(
                        event="go",
                        target=["S2"],
                        help_text=["go doc"],
                    )
                ],
            )
        ],
    )
    cleaned = SCXMLDocumentHandler._remove_empty(asdict(s))
    assert cleaned["help_text"] == ["root doc"]
    assert cleaned["state"][0]["help_text"] == ["state doc"]
    assert cleaned["state"][0]["transition"][0]["help_text"] == ["go doc"]


def test_handler_help_text_does_not_leak_into_other_attributes():
    """After parsing a JSON document with help_text, other_attributes stays clean.

    Independence between ``help_text`` and ``other_attributes`` is normative
    (CONV-E "intentionally separate"). Setting both on the same element MUST
    keep them in their own buckets, and the converter MUST NOT silently
    forward one into the other.
    """
    payload = {
        "name": "m1",
        "version": 1.0,
        "datamodel_attribute": "null",
        "help_text": ["root doc"],
        "other_attributes": {"position": "1,2", "description": "legacy doc"},
        "state": [
            {
                "id": "S1",
                "help_text": ["state doc"],
                "other_attributes": {"position": "3,4"},
            }
        ],
    }
    s = pydantic_models.Scxml.model_validate(payload)
    assert s.help_text == ["root doc"]
    assert "help_text" not in s.other_attributes
    assert s.other_attributes == {"position": "1,2", "description": "legacy doc"}
    state0 = s.state[0]
    assert state0.help_text == ["state doc"]
    assert "help_text" not in state0.other_attributes
    assert state0.other_attributes == {"position": "3,4"}


# ---------------------------------------------------------------------------
# Canonical schema artifact + mirror parity.
# ---------------------------------------------------------------------------


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_SCHEMA = REPO_ROOT / "scjson.schema.json"
JS_SCHEMA = REPO_ROOT / "js" / "scjson.schema.json"
JAVA_SCHEMA = REPO_ROOT / "java" / "src" / "main" / "resources" / "scjson.schema.json"


def _load_schema(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


@pytest.mark.parametrize("class_name", ["Scxml", "State", "Transition", "Data"])
def test_canonical_schema_exposes_help_text(class_name):
    """``scjson.schema.json`` validates help_text as an array of strings."""
    schema = _load_schema(ROOT_SCHEMA)
    defs = schema["$defs"]
    assert class_name in defs, f"$defs missing {class_name}"
    props = defs[class_name]["properties"]
    assert "help_text" in props, (
        f"scjson.schema.json $defs.{class_name} is missing help_text"
    )
    entry = props["help_text"]
    assert entry.get("type") == "array"
    assert entry.get("items") == {"type": "string"}


def test_canonical_schema_enum_defs_have_no_help_text():
    """Enumeration ``$defs`` entries MUST NOT advertise help_text."""
    schema = _load_schema(ROOT_SCHEMA)
    for enum_name in NOT_APPLIES_TO_ENUMS:
        entry = schema["$defs"].get(enum_name)
        assert entry is not None, f"$defs missing {enum_name}"
        assert "properties" not in entry, (
            f"{enum_name} unexpectedly has properties in canonical schema"
        )


def test_schema_mirror_parity_root_js_java():
    """The three published schema copies stay byte-identical."""
    root_bytes = ROOT_SCHEMA.read_bytes()
    js_bytes = JS_SCHEMA.read_bytes()
    java_bytes = JAVA_SCHEMA.read_bytes()
    assert root_bytes == js_bytes, (
        "js/scjson.schema.json drifted from canonical root scjson.schema.json"
    )
    assert root_bytes == java_bytes, (
        "java/src/main/resources/scjson.schema.json drifted from canonical "
        "root scjson.schema.json"
    )

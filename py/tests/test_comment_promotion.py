"""
Agent Name: comment-promotion-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

CONV-F (SCXML Comment Promotion) acceptance tests for the Python side. See
``docs/concepts/SCJSON-CONV-00-CONCEPTS.md`` (CONV-F, §270-388) for the
normative contract these tests pin.

Coverage matrix (mirrors CONV-F §354-376):

* Parser cases — root-leading, root-trailing, parent-trailing, nested-state,
  transition-leading, onentry/onexit-leading, multiple-consecutive, and
  whitespace-separated comments promote to the expected element.
* Non-promotion — comments inside ``<script>`` / ``<data>``, processing
  instructions, and comments inside opaque extension subtrees do not become
  ``help_text``.
* Emission — round-trip count/order/owner/repaired text preserved; root
  comments emit after the XML declaration and before ``<scxml>``; multiple
  entries per element emit as one comment per entry without coalescing.
* Escaping — ``<``, ``>``, ``&``, ``--``, trailing ``-``, leading indentation,
  multi-line content emit as valid XML and survive round-trip.
* Engine-trace invariance — adding ``help_text`` does not change activation
  order on a simple machine.

The static schema/model surface (every applies-to model exposes
``help_text: list[str]``; enum models do not) is already pinned by
``py/tests/test_help_text_round_trip.py`` (CONV-E); this module focuses on the
XML-side promotion / emission behavior CONV-F adds.
"""

from __future__ import annotations

import json
import re

import pytest

from scjson.comment_promotion import (
    emit_safe_comment_text,
    extract_help_text_from_xml,
    repair_comment_text,
)
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler


def _convert(xml: str) -> dict:
    """Run the canonical XML -> JSON conversion and return the parsed dict."""
    handler = SCXMLDocumentHandler()
    return json.loads(handler.xml_to_json(xml))


def _round_trip(xml: str) -> tuple[dict, str]:
    """Round-trip XML through JSON and back, returning (json_dict, xml_out)."""
    handler = SCXMLDocumentHandler()
    js = handler.xml_to_json(xml)
    xml_out = handler.json_to_xml(js)
    return json.loads(js), xml_out


SCXML_NS = 'xmlns="http://www.w3.org/2005/07/scxml"'


# ---------------------------------------------------------------------------
# Repair text helpers (unit tests).
# ---------------------------------------------------------------------------


def test_repair_single_line_trims_edges():
    """Single-line comment text only loses edge whitespace."""
    assert repair_comment_text("  hello  ") == "hello"


def test_repair_multiline_dedents_common_indent():
    """Block comment loses one common leading-indent margin."""
    raw = "\n    line one\n    line two\n      indented inside\n    "
    out = repair_comment_text(raw)
    assert out == "line one\nline two\n  indented inside"


def test_repair_multiline_trims_blank_edges():
    """Leading and trailing blank lines are removed.

    Note: only blank lines are stripped; in-body trailing whitespace on a
    surviving content line is preserved (it is part of the content, not a
    blank-line edge). The two-space common indent IS removed by dedent.
    """
    raw = "\n\n  body  \n\n"
    out = repair_comment_text(raw)
    assert out == "body  "


def test_emit_safe_doubles_dashes():
    """Forbidden ``--`` is replaced with ``- -`` (CONV-F §340-344)."""
    assert emit_safe_comment_text("a -- b -- c") == "a - - b - - c"


def test_emit_safe_trailing_dash_pads_space():
    """Body ending in ``-`` gets one trailing space."""
    assert emit_safe_comment_text("note-") == "note- "


# ---------------------------------------------------------------------------
# Parser cases: positive promotion.
# ---------------------------------------------------------------------------


def test_root_leading_comment_attaches_to_root():
    xml = f'<!-- root preface --><scxml {SCXML_NS} name="m1"><state id="S1"/></scxml>'
    data = _convert(xml)
    assert data["help_text"] == ["root preface"]


def test_root_trailing_comment_attaches_to_root():
    xml = (
        f'<scxml {SCXML_NS} name="m1"><state id="S1"/></scxml>'
        f'<!-- afterword -->'
    )
    data = _convert(xml)
    assert data["help_text"] == ["afterword"]


def test_parent_trailing_comment_attaches_to_parent():
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<state id="S1">'
        f'<transition event="go" target="S2"/>'
        f'<!-- trailing -->'
        f'</state></scxml>'
    )
    data = _convert(xml)
    assert data["state"][0]["help_text"] == ["trailing"]
    assert data["state"][0]["transition"][0].get("help_text") is None


def test_nested_state_leading_comment():
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<state id="S1">'
        f'<!-- about nested --><state id="N1"/>'
        f'</state></scxml>'
    )
    data = _convert(xml)
    assert data["state"][0]["state"][0]["help_text"] == ["about nested"]


def test_transition_leading_comment():
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<state id="S1">'
        f'<!-- transition note --><transition event="go" target="S1"/>'
        f'</state></scxml>'
    )
    data = _convert(xml)
    assert data["state"][0]["transition"][0]["help_text"] == ["transition note"]


def test_onentry_and_onexit_leading_comments():
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<state id="S1">'
        f'<!-- entry --><onentry><log expr="\'hi\'"/></onentry>'
        f'<!-- exit --><onexit><log expr="\'bye\'"/></onexit>'
        f'</state></scxml>'
    )
    data = _convert(xml)
    state = data["state"][0]
    assert state["onentry"][0]["help_text"] == ["entry"]
    assert state["onexit"][0]["help_text"] == ["exit"]


def test_multiple_consecutive_comments_all_promote_in_order():
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<state id="S1"><!-- a --><!-- b --><onentry/></state></scxml>'
    )
    data = _convert(xml)
    assert data["state"][0]["onentry"][0]["help_text"] == ["a", "b"]


def test_whitespace_separated_comment_still_promotes():
    """A comment separated from the next element by whitespace-only text still
    attaches to that next element."""
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<state id="S1">\n  <!-- doc -->\n  <transition event="go" target="S1"/>\n'
        f'</state></scxml>'
    )
    data = _convert(xml)
    assert data["state"][0]["transition"][0]["help_text"] == ["doc"]


def test_non_whitespace_text_severs_promotion_to_parent():
    """Per CONV-F §306-307: ``<state><!--a--><transition/>text<!--b--></state>``
    yields ``a -> Transition`` and ``b -> State``."""
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<state id="S1"><!-- a --><transition event="go" target="S1"/>text<!-- b --></state>'
        f'</scxml>'
    )
    data = _convert(xml)
    assert data["state"][0]["transition"][0]["help_text"] == ["a"]
    assert data["state"][0]["help_text"] == ["b"]


def test_root_pre_and_post_root_comments_combine_on_root():
    xml = (
        f'<!-- pre --><scxml {SCXML_NS} name="m1"><state id="S1"/></scxml><!-- post -->'
    )
    data = _convert(xml)
    assert data["help_text"] == ["pre", "post"]


# ---------------------------------------------------------------------------
# Parser cases: non-promotion.
# ---------------------------------------------------------------------------


def test_script_body_comment_not_promoted():
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<script>x = 1; <!-- inside script --></script></scxml>'
    )
    data = _convert(xml)
    assert "help_text" not in data
    for script in data.get("script", []):
        assert "help_text" not in script


def test_data_body_comment_not_promoted():
    xml = (
        f'<scxml {SCXML_NS} name="m1" datamodel="ecmascript">'
        f'<datamodel><data id="x"><!-- inside data -->1</data></datamodel></scxml>'
    )
    data = _convert(xml)
    dm = data.get("datamodel", [{}])[0]
    for d in dm.get("data", []):
        assert "help_text" not in d


def test_processing_instruction_not_promoted():
    xml = (
        '<?xml-stylesheet href="x.xsl" type="text/xsl"?>'
        f'<scxml {SCXML_NS} name="m1"><state id="S1"/></scxml>'
    )
    data = _convert(xml)
    # No help_text from the PI.
    assert "help_text" not in data
    assert "help_text" not in data["state"][0]


def test_comment_inside_opaque_extension_not_promoted():
    """A comment buried inside an unknown extension element is silently
    dropped from the promotion path (CONV-F rule 6)."""
    # ``<content>`` accepts mixed content; a comment inside it sits in an
    # opaque extension subtree because <foo> is not an SCJSON element.
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<state id="S1"><onentry><send><content>'
        f'<foo><!-- buried --></foo>'
        f'</content></send></onentry></state></scxml>'
    )
    data = _convert(xml)
    state = data["state"][0]
    onentry = state["onentry"][0]
    send = onentry["send"][0]
    # Promote nothing on the content / send / onentry from the buried comment.
    content = send.get("content", [{}])[0]
    assert "help_text" not in content
    assert "help_text" not in send
    assert "help_text" not in onentry


# ---------------------------------------------------------------------------
# Emission cases.
# ---------------------------------------------------------------------------


def test_round_trip_preserves_count_order_owner_and_text():
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<!-- A --><state id="S1">'
        f'<!-- B --><!-- C --><transition event="go" target="S2"/>'
        f'</state>'
        f'<state id="S2"/>'
        f'</scxml>'
    )
    data1, xml_out = _round_trip(xml)
    data2 = _convert(xml_out)
    # Owners and order survive the round-trip.
    assert data2["state"][0]["help_text"] == ["A"]
    assert data2["state"][0]["transition"][0]["help_text"] == ["B", "C"]
    # And the JSON before and after is structurally identical for help_text.
    assert data1["state"][0]["help_text"] == data2["state"][0]["help_text"]
    assert (
        data1["state"][0]["transition"][0]["help_text"]
        == data2["state"][0]["transition"][0]["help_text"]
    )


def test_multiple_entries_emit_one_comment_each_no_coalesce():
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<state id="S1"><!-- one --><!-- two --><!-- three --><onentry/></state>'
        f'</scxml>'
    )
    handler = SCXMLDocumentHandler()
    js = handler.xml_to_json(xml)
    xml_out = handler.json_to_xml(js)
    # Count the comments preceding the <onentry/> tag in the output.
    onentry_comments = re.findall(r"<!--\s*one\s*-->", xml_out)
    assert len(onentry_comments) == 1
    assert "<!--one-->" in xml_out.replace(" ", "")
    assert "<!--two-->" in xml_out.replace(" ", "")
    assert "<!--three-->" in xml_out.replace(" ", "")
    # No coalescing into a single multi-line comment with both bodies.
    assert "one\ntwo" not in xml_out
    assert "one two three" not in xml_out


def test_root_help_text_emits_after_xml_decl_before_scxml():
    handler = SCXMLDocumentHandler()
    payload = {
        "name": "m1",
        "version": 1.0,
        "datamodel_attribute": "null",
        "help_text": ["root doc"],
        "state": [{"id": "S1"}],
    }
    xml_out = handler.json_to_xml(json.dumps(payload))
    # XML declaration is first, then the comment, then the root element.
    assert xml_out.lstrip().startswith("<?xml")
    decl_end = xml_out.index("?>")
    comment_pos = xml_out.index("<!--root doc-->")
    root_open = re.search(r"<[A-Za-z][A-Za-z0-9_:]*scxml", xml_out)
    assert root_open is not None
    assert decl_end < comment_pos < root_open.start()


# ---------------------------------------------------------------------------
# Escaping cases.
# ---------------------------------------------------------------------------


def test_escaping_lt_gt_amp_round_trip():
    """Comment text containing ``<``, ``>``, ``&`` emits as valid XML."""
    handler = SCXMLDocumentHandler()
    payload = {
        "name": "m1",
        "version": 1.0,
        "datamodel_attribute": "null",
        "state": [{"id": "S1", "help_text": ["a<b>c&d"]}],
    }
    xml_out = handler.json_to_xml(json.dumps(payload))
    # lxml renders comment bodies literally; the metacharacters survive.
    assert "a<b>c&d" in xml_out
    # Round-trip recovers the original text.
    rt = _convert(xml_out)
    assert rt["state"][0]["help_text"] == ["a<b>c&d"]


def test_escaping_double_dash_replaced_with_dash_space_dash():
    handler = SCXMLDocumentHandler()
    payload = {
        "name": "m1",
        "version": 1.0,
        "datamodel_attribute": "null",
        "state": [{"id": "S1", "help_text": ["a -- b"]}],
    }
    xml_out = handler.json_to_xml(json.dumps(payload))
    assert "<!--a - - b-->" in xml_out
    # Round-trip: repaired form is what comes back, not the original.
    rt = _convert(xml_out)
    assert rt["state"][0]["help_text"] == ["a - - b"]


def test_escaping_trailing_dash_padded_with_space():
    handler = SCXMLDocumentHandler()
    payload = {
        "name": "m1",
        "version": 1.0,
        "datamodel_attribute": "null",
        "state": [{"id": "S1", "help_text": ["finishes with-"]}],
    }
    xml_out = handler.json_to_xml(json.dumps(payload))
    assert "<!--finishes with- -->" in xml_out
    rt = _convert(xml_out)
    assert rt["state"][0]["help_text"] == ["finishes with-"]


def test_multiline_dedent_and_round_trip_preserves_repaired_form():
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<state id="S1">'
        f'<!--\n'
        f'    first line\n'
        f'    second line\n'
        f'      indented\n'
        f'  --><transition event="go" target="S1"/>'
        f'</state></scxml>'
    )
    handler = SCXMLDocumentHandler()
    js = handler.xml_to_json(xml)
    js_data = json.loads(js)
    transition = js_data["state"][0]["transition"][0]
    assert transition["help_text"] == ["first line\nsecond line\n  indented"]
    # Round-trip preserves repaired form.
    xml_out = handler.json_to_xml(js)
    js2 = json.loads(handler.xml_to_json(xml_out))
    assert (
        js2["state"][0]["transition"][0]["help_text"]
        == js_data["state"][0]["transition"][0]["help_text"]
    )


# ---------------------------------------------------------------------------
# Engine-trace invariance.
# ---------------------------------------------------------------------------


def test_engine_trace_invariant_under_help_text():
    """Adding ``help_text`` MUST NOT change DocumentContext activation order
    or any observable engine trace (CONV-F §375-376)."""
    from scjson.context import DocumentContext

    handler = SCXMLDocumentHandler()
    bare = (
        f'<scxml {SCXML_NS} name="m1" initial="S1">'
        f'<state id="S1"><transition event="go" target="S2"/></state>'
        f'<state id="S2"/></scxml>'
    )
    commented = (
        f'<!-- preface --><scxml {SCXML_NS} name="m1" initial="S1">'
        f'<!-- about S1 --><state id="S1">'
        f'<!-- about transition --><transition event="go" target="S2"/>'
        f'</state>'
        f'<state id="S2"><!-- trailing --></state></scxml>'
    )

    ctx_a = DocumentContext.from_xml_string(bare)
    ctx_b = DocumentContext.from_xml_string(commented)

    def _trace(ctx) -> list[tuple]:
        order: list[tuple] = []
        order.append(("initial", tuple(sorted(ctx.configuration))))
        ctx.enqueue("go")
        ctx.microstep()
        order.append(("after-go", tuple(sorted(ctx.configuration))))
        return order

    assert _trace(ctx_a) == _trace(ctx_b)


# ---------------------------------------------------------------------------
# Pre-pass surface (used by callers other than the handler).
# ---------------------------------------------------------------------------


def test_extract_returns_address_map_with_local_names():
    """The pre-pass returns addresses keyed on local element names so they
    survive namespace insertion (CONV-F §323-325)."""
    xml = (
        f'<scxml {SCXML_NS} name="m1">'
        f'<!-- s1 doc --><state id="S1"/></scxml>'
    )
    _, addr_map = extract_help_text_from_xml(xml)
    # Expect one entry for the state.
    expected_key = (("scxml", 0), ("state", 0))
    assert addr_map.get(expected_key) == ["s1 doc"]

"""
Agent Name: comment-promotion

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

CONV-F (SCXML Comment Promotion) — Python side.

See ``docs/concepts/SCJSON-CONV-00-CONCEPTS.md`` (CONV-F, lines ~270-388) for
the normative contract this module implements.

Public surface (used by :class:`scjson.SCXMLDocumentHandler.SCXMLDocumentHandler`):

* :func:`extract_help_text_from_xml` — XML pre-pass. Walks an SCXML string with
  lxml (comments preserved), assigns deterministic addresses to every element,
  partitions XML comment nodes onto their owning element per CONV-F rules 1-8,
  and returns the comment-free XML plus an ``address -> [comment_text, ...]``
  map.
* :func:`attach_help_text_to_model` — after xsdata produces a model from the
  comment-free XML, walks the model in the same deterministic order and
  appends each comment string to the matching element's ``help_text`` list.
* :func:`inject_help_text_comments_into_xml` — post-pass for the
  SCJSON-to-SCXML direction. Takes the model and the xsdata-serialized XML
  string, and inserts ``<!-- ... -->`` nodes immediately before the owning
  element (or before the ``<scxml>`` root for root-level entries).

Design notes
------------

**Addressing.** Each element gets a tuple-of-tuples address of the form
``(("scxml", 0), ("state", 1), ("transition", 0), ...)`` where each segment is
``(local_tag_name, index_among_same-tag_element_siblings)``. This indexes
naturally into the xsdata model: ``model.state[1].transition[0]`` lines up
with the lxml element at the same address path, because xsdata preserves
sibling order within a typed list and CONV-F only needs to attach metadata
per element, not re-derive interleaving order.

**Namespace insertion (CONV-F §323-325).** Addresses use *local* names, so
they survive the default-namespace insertion that
:meth:`SCXMLDocumentHandler.xml_to_json` applies after the pre-pass.

**Script / Data exclusion (CONV-F rule 5).** Comments whose XML ancestry
includes a ``<script>`` or ``<data>`` are not promoted. They remain inside the
CDATA-backed source string that xsdata captures on those elements.

**Extension subtrees (CONV-F rule 6).** Any element whose local name is not
one of the SCJSON-recognized SCXML element tags is treated as an opaque
extension. Comments inside such subtrees are not promoted; this includes
``<content>`` payloads that are not a nested ``<scxml>``.

**Emission text safety (CONV-F §340-344).** Comment text containing ``--`` is
emitted as ``- -``; bodies ending in ``-`` get one trailing space; XML
metacharacters are handled by lxml's comment node serialization.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, Iterable

from lxml import etree as _ET


# ---------------------------------------------------------------------------
# SCJSON element tag set
# ---------------------------------------------------------------------------

#: Local tag names that own a ``help_text`` field on the model side. Mirrors
#: ``APPLIES_TO`` in ``py/tests/test_help_text_round_trip.py``.
APPLIES_TO_TAGS: frozenset[str] = frozenset(
    {
        "scxml",
        "state",
        "parallel",
        "final",
        "history",
        "initial",
        "transition",
        "onentry",
        "onexit",
        "invoke",
        "finalize",
        "datamodel",
        "data",
        "donedata",
        "content",
        "param",
        "assign",
        "log",
        "raise",
        "if",
        "elseif",
        "else",
        "foreach",
        "send",
        "cancel",
        "script",
    }
)

#: Tags whose textual content is opaque target-language source. Comments
#: inside these elements remain content and MUST NOT be promoted (CONV-F
#: rule 5).
SOURCE_BODY_TAGS: frozenset[str] = frozenset({"script", "data"})

#: SCXML elements whose character data is part of their semantic payload.
#: Other recognized SCXML elements are element-only for conversion purposes;
#: stray non-whitespace text there is invalid SCXML and is ignored after it
#: has served its CONV-F role of severing comment promotion to the next child.
MIXED_TEXT_TAGS: frozenset[str] = frozenset({"script", "data", "content"})

#: Cached ``class -> {xml_tag: attribute_name}`` map. Lazily populated from
#: the dataclass models module on first use; the same shape applies to the
#: pydantic models because both are generated from the same xsdata schema.
_TAG_TO_ATTR_CACHE: dict[type, dict[str, str]] = {}


def _local_name(tag: str) -> str:
    """Strip an optional ``{namespace}`` prefix from an lxml element tag."""
    if isinstance(tag, str) and tag.startswith("{"):
        end = tag.find("}")
        if end != -1:
            return tag[end + 1 :]
    return tag


def _is_comment(node: Any) -> bool:
    """Return True if ``node`` is an lxml comment node."""
    return getattr(node, "tag", None) is _ET.Comment


def _is_processing_instruction(node: Any) -> bool:
    """Return True if ``node`` is an lxml processing instruction node."""
    return getattr(node, "tag", None) is _ET.ProcessingInstruction


# ---------------------------------------------------------------------------
# Comment text repair (parser side and emitter side share this).
# ---------------------------------------------------------------------------


def repair_comment_text(raw: str) -> str:
    """Repair raw XML comment body text per CONV-F §294-299.

    Strips a common leading indentation margin from multi-line block comments
    and trims leading/trailing blank lines. Does NOT paragraph-wrap or
    coalesce. Single-line comments are stripped only of edge whitespace.

    :param raw: Comment body text as returned by lxml (without ``<!--`` /
        ``-->`` delimiters).
    :returns: Repaired text suitable for storage in ``help_text``.
    """
    if raw is None:
        return ""
    if "\n" not in raw:
        # Single-line comment: trim edge whitespace only.
        return raw.strip()
    # Multi-line: split, drop leading and trailing blank lines, then
    # de-indent by the smallest non-empty indentation.
    lines = raw.splitlines()
    # Drop leading and trailing blank lines.
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""
    # Compute common leading indent from non-blank lines.
    indents = [
        len(line) - len(line.lstrip(" \t"))
        for line in lines
        if line.strip()
    ]
    common = min(indents) if indents else 0
    if common:
        lines = [
            (line[common:] if len(line) >= common else line) for line in lines
        ]
    return "\n".join(lines)


def emit_safe_comment_text(text: str) -> str:
    """Return a body string safe to wrap in ``<!-- ... -->``.

    Per CONV-F §340-344: the forbidden sequence ``--`` is replaced with
    ``- -`` and a body ending in ``-`` gets one trailing space appended.

    :param text: Repaired help_text entry.
    :returns: Comment-safe body.
    """
    safe = text.replace("--", "- -")
    if safe.endswith("-"):
        safe = safe + " "
    return safe


# ---------------------------------------------------------------------------
# Pre-pass: XML -> (comment-free XML, address map).
# ---------------------------------------------------------------------------


Address = tuple[tuple[str, int], ...]


def _assign_address_and_walk(
    elem: _ET._Element,
    address: Address,
    address_map: dict[Address, list[str]],
    inside_source_body: bool = False,
    inside_extension: bool = False,
) -> None:
    """Walk an element subtree, partitioning comments onto owning addresses.

    :param elem: lxml element to visit.
    :param address: address tuple for ``elem`` itself.
    :param address_map: out-parameter ``address -> [comment_text, ...]``.
    :param inside_source_body: True if any ancestor is ``<script>`` /
        ``<data>``; suppresses promotion of any comment in this subtree.
    :param inside_extension: True if any ancestor is an opaque extension
        element (a local tag not in :data:`APPLIES_TO_TAGS`); suppresses
        promotion.
    """
    local = _local_name(elem.tag)
    elem_in_source = inside_source_body or local in SOURCE_BODY_TAGS
    elem_in_extension = inside_extension or (
        local not in APPLIES_TO_TAGS and address != ()  # root pass guard
    )

    # Buffer of pending comments awaiting a *next* element sibling.
    pending: list[str] = []

    # Index counter for ELEMENT children, scoped per-local-name.
    per_tag_counter: dict[str, int] = {}

    # We also need to flag whether any non-whitespace text (rule "non-whitespace
    # character data attaches to parent because intent is ambiguous") has been
    # seen between a pending comment and the next element. The simplest rule
    # consistent with the spec: if the *immediately preceding* tail/text node
    # to the element is non-whitespace, flush pending to parent. We approximate
    # by tracking a "non-ws text since last comment" flag.
    saw_non_ws_text_since_last_comment = False

    # Examine the element's leading text first: it appears before any child
    # nodes. We don't promote based on parent text, but if there is
    # non-whitespace text BEFORE the first comment-or-element, it does not
    # affect rule 1; we only care about non-ws between a comment and the next
    # element.

    # Now iterate children in document order. lxml exposes them via
    # iteration; element.text precedes the first child; each child carries
    # element.tail for the text after it.
    children = list(elem)

    for child in children:
        # First, examine any "tail" of the previous sibling sitting between
        # the previous child and this one. lxml stores it on the *previous*
        # node's .tail. We handle it by inspecting this child's preceding
        # sibling tail at the moment of visit.
        # Simpler: iterate over the raw text-or-comment-or-element sequence.
        pass

    # Easier and more correct: build an ordered list of (kind, payload).
    # lxml does not expose text nodes as separate children; reconstruct
    # using element.text (before children[0]) plus each child.tail (after
    # the child it lives on).
    seq: list[tuple[str, Any]] = []
    if elem.text is not None:
        seq.append(("text", elem.text))
    for child in children:
        if _is_comment(child):
            seq.append(("comment", child))
        elif _is_processing_instruction(child):
            seq.append(("pi", child))
        else:
            seq.append(("element", child))
        if child.tail is not None:
            seq.append(("text", child.tail))

    saw_non_ws_text_since_last_comment = False
    for kind, payload in seq:
        if kind == "text":
            if payload and payload.strip():
                # Non-whitespace text severs the "pending comment -> next
                # element" relationship per the spec's deterministic edge
                # cases ("Comments separated by non-whitespace character data
                # attach to the parent").
                if pending:
                    # Flush pending to parent (this element), respecting
                    # script/data and extension exclusions.
                    if not elem_in_source and not elem_in_extension:
                        address_map.setdefault(address, []).extend(pending)
                    pending = []
                saw_non_ws_text_since_last_comment = True
            # whitespace-only text does not flush
            continue

        if kind == "pi":
            # Processing instructions: never promote (rule 8 / edge cases).
            continue

        if kind == "comment":
            raw = payload.text or ""
            repaired = repair_comment_text(raw)
            # Even empty repaired strings are preserved (CONV-F does not
            # require dropping empties).
            pending.append(repaired)
            # The non-ws-text flag does not need to reset on comment; the
            # flag only matters at the moment we evaluate flush vs attach.
            continue

        if kind == "element":
            child_local = _local_name(payload.tag)
            idx = per_tag_counter.get(child_local, 0)
            per_tag_counter[child_local] = idx + 1
            child_addr: Address = address + ((child_local, idx),)

            # If this child is itself a promotion-target (its local name is in
            # APPLIES_TO_TAGS) AND we are not inside a script/data body or an
            # extension subtree, attach pending comments to it.
            target_eligible = (
                child_local in APPLIES_TO_TAGS
                and not elem_in_source
                and not elem_in_extension
            )
            if pending and target_eligible:
                address_map.setdefault(child_addr, []).extend(pending)
            elif pending:
                # Pending comments cannot promote to this child (extension or
                # source body). Flush to parent if parent is promotion-eligible
                # and not in an excluded subtree.
                if (
                    address != ()
                    and not elem_in_source
                    and not elem_in_extension
                    and _local_name_from_address(address) in APPLIES_TO_TAGS
                ):
                    address_map.setdefault(address, []).extend(pending)
                # Otherwise silently drop (extension subtree).
            pending = []
            saw_non_ws_text_since_last_comment = False

            # Recurse.
            _assign_address_and_walk(
                payload,
                child_addr,
                address_map,
                inside_source_body=elem_in_source,
                inside_extension=elem_in_extension,
            )

    # After processing all children, any remaining pending comments attach to
    # this element (rule 3: comment with no following element sibling attaches
    # to its parent). Suppress under script/data and extension subtrees.
    if pending:
        if (
            not elem_in_source
            and not elem_in_extension
            and _local_name_from_address(address or (("scxml", 0),))
            in APPLIES_TO_TAGS
        ):
            address_map.setdefault(address, []).extend(pending)


def _local_name_from_address(addr: Address) -> str:
    """Return the local-name of the last segment of ``addr`` (or '')."""
    if not addr:
        return ""
    return addr[-1][0]


def extract_help_text_from_xml(
    xml_str: str,
) -> tuple[str, dict[Address, list[str]]]:
    """Extract comment-promotion metadata from an SCXML string.

    Parses ``xml_str`` with lxml (comments preserved), assigns deterministic
    addresses to every element, partitions comment nodes per CONV-F rules
    1-8, strips the comments, and returns the comment-free XML serialization
    plus an ``address -> [help_text, ...]`` map.

    Pre-root comments (CONV-F rule 4) are attached to the root ``Scxml`` at
    address ``(("scxml", 0),)``. Post-root comments are also attached there.

    :param xml_str: Raw SCXML string.
    :returns: Tuple of ``(comment_free_xml_str, address_map)``. If parsing
        fails, returns ``(xml_str, {})`` to let the downstream xsdata parser
        produce a descriptive error.
    """
    parser = _ET.XMLParser(remove_comments=False, resolve_entities=False)
    try:
        # Use fromstring so we accept both bytes and str without needing a
        # file-like object. lxml requires bytes for unicode XML declarations,
        # so encode as utf-8.
        if isinstance(xml_str, str):
            data = xml_str.encode("utf-8")
        else:
            data = xml_str
        # Parse via ElementTree so we can access top-level siblings (the
        # comments before/after the root element).
        tree = _ET.ElementTree(_ET.fromstring(data, parser=parser))
    except _ET.XMLSyntaxError:
        return xml_str, {}
    except Exception:
        return xml_str, {}

    root = tree.getroot()
    root_local = _local_name(root.tag)
    root_addr: Address = ((root_local, 0),)
    address_map: dict[Address, list[str]] = {}

    # Pre-root and post-root comments (rule 4): lxml exposes them via the
    # root's getprevious() / getnext() chain.
    pre_root: list[str] = []
    sibling = root.getprevious()
    pre_chain: list[Any] = []
    while sibling is not None:
        pre_chain.append(sibling)
        sibling = sibling.getprevious()
    for sib in reversed(pre_chain):
        if _is_comment(sib):
            pre_root.append(repair_comment_text(sib.text or ""))

    post_root: list[str] = []
    sibling = root.getnext()
    while sibling is not None:
        if _is_comment(sibling):
            post_root.append(repair_comment_text(sibling.text or ""))
        sibling = sibling.getnext()

    if root_local in APPLIES_TO_TAGS and (pre_root or post_root):
        address_map.setdefault(root_addr, []).extend(pre_root)
        address_map.setdefault(root_addr, []).extend(post_root)

    # Walk the root subtree.
    _assign_address_and_walk(root, root_addr, address_map)

    # Strip comments from the tree and re-serialize.
    _strip_comments_in_place(root)
    _strip_unsupported_character_data_in_place(root)

    # Also strip pre-root and post-root comments (we already harvested them).
    for sib in pre_chain:
        if _is_comment(sib):
            sib.getparent() if hasattr(sib, "getparent") else None
            # ElementTree-level siblings of root: remove via the tree.
            try:
                sib.getparent().remove(sib)  # type: ignore[attr-defined]
            except Exception:
                pass
    sibling = root.getnext()
    while sibling is not None:
        nxt = sibling.getnext()
        if _is_comment(sibling):
            try:
                sibling.getparent().remove(sibling)  # type: ignore[attr-defined]
            except Exception:
                pass
        sibling = nxt

    # lxml does not always expose .getparent() for root-level comments
    # (their "parent" is the document, not an element). The fromstring path
    # discards them at serialization anyway when we call tostring on root.
    # We serialize from root, which loses pre/post-root siblings naturally.
    cleaned = _ET.tostring(root, encoding="unicode")

    return cleaned, address_map


def _strip_comments_in_place(elem: _ET._Element) -> None:
    """Remove every comment node from ``elem``'s subtree, preserving tails.

    When a comment node has a ``.tail``, lxml's ``remove()`` discards it.
    We splice the tail onto whatever text would absorb it (the previous
    sibling's tail, or the parent's text) so the resulting XML still
    contains the original whitespace.
    """
    # Walk children, remove comments.
    for child in list(elem):
        if _is_comment(child):
            tail = child.tail or ""
            prev = child.getprevious()
            if prev is not None and not _is_comment(prev):
                prev.tail = (prev.tail or "") + tail
            else:
                elem.text = (elem.text or "") + tail
            elem.remove(child)
        else:
            _strip_comments_in_place(child)


def _strip_unsupported_character_data_in_place(elem: _ET._Element) -> None:
    """Drop invalid character data from recognized element-only SCXML nodes.

    CONV-F uses non-whitespace character data between a pending comment and the
    next child element to decide comment ownership. After that decision is
    recorded, the converter should not feed such invalid element-only text to
    xsdata because xsdata may surface it as a wildcard with no qname. Mixed
    payload elements and opaque extension subtrees keep their text intact.
    """
    local = _local_name(elem.tag)
    structural_scxml = local in APPLIES_TO_TAGS and local not in MIXED_TEXT_TAGS

    if structural_scxml and elem.text and elem.text.strip():
        elem.text = ""

    for child in list(elem):
        _strip_unsupported_character_data_in_place(child)
        if structural_scxml and child.tail and child.tail.strip():
            child.tail = ""


# ---------------------------------------------------------------------------
# Attach helper: walks the xsdata model in lockstep with the address map.
# ---------------------------------------------------------------------------


def _build_tag_to_attr_map(cls: type) -> dict[str, str]:
    """Return ``{xml_tag_name: python_attribute_name}`` for child fields.

    Pydantic and dataclass model variants share the same xsdata metadata, so
    we read it via ``dataclasses.fields`` when available and fall back to
    ``model_fields`` for pydantic v2 models.
    """
    if cls in _TAG_TO_ATTR_CACHE:
        return _TAG_TO_ATTR_CACHE[cls]

    mapping: dict[str, str] = {}
    # Path 1: dataclass
    if is_dataclass(cls):
        for f in fields(cls):
            md = f.metadata or {}
            if md.get("type") == "Element":
                tag = md.get("name", f.name)
                mapping[tag] = f.name
    else:
        # Path 2: pydantic v2 — model_fields carries the json_schema_extra
        # metadata but xsdata stores it in field.metadata, which pydantic
        # surfaces via FieldInfo.metadata or json_schema_extra. Read the
        # attribute's metadata defaultdict on the underlying class via the
        # generated stub: pydantic xsdata generation uses Field(...) calls
        # that map to model_fields[name].metadata (an ordered list).
        model_fields = getattr(cls, "model_fields", {})
        for name, finfo in model_fields.items():
            # xsdata-generated pydantic uses metadata in FieldInfo as a list
            # of dicts. Try several access paths defensively.
            md_list = getattr(finfo, "metadata", None) or []
            md: dict[str, Any] = {}
            if isinstance(md_list, list):
                for entry in md_list:
                    if isinstance(entry, dict):
                        md.update(entry)
            elif isinstance(md_list, dict):
                md = dict(md_list)
            # Fallback: json_schema_extra
            extra = getattr(finfo, "json_schema_extra", None)
            if isinstance(extra, dict):
                # Common xsdata-pydantic shape: {"type": "Element", "name": "..."}
                if "type" in extra and "type" not in md:
                    md["type"] = extra["type"]
                if "name" in extra and "name" not in md:
                    md["name"] = extra["name"]
            if md.get("type") == "Element":
                tag = md.get("name", name)
                mapping[tag] = name
    _TAG_TO_ATTR_CACHE[cls] = mapping
    return mapping


def _resolve_child(parent: Any, tag: str, index: int) -> Any | None:
    """Return ``parent``'s ``index``-th child whose XML tag name is ``tag``.

    Returns ``None`` if no such attribute exists or the index is out of range.
    """
    if parent is None:
        return None
    mapping = _build_tag_to_attr_map(type(parent))
    attr = mapping.get(tag)
    if attr is None:
        return None
    coll = getattr(parent, attr, None)
    if coll is None:
        return None
    if not isinstance(coll, list):
        # Singleton field (e.g. History.transition / Initial.transition).
        return coll if index == 0 else None
    if 0 <= index < len(coll):
        return coll[index]
    return None


def _resolve_address(model_root: Any, address: Address) -> Any | None:
    """Navigate ``model_root`` to the element at ``address``.

    Address ``(("scxml", 0),)`` resolves to ``model_root`` itself.
    """
    if not address:
        return None
    # First segment is the root element name; it should match model_root.
    # We don't check the name (the parser already enforced root == scxml).
    node: Any = model_root
    for tag, idx in address[1:]:
        node = _resolve_child(node, tag, idx)
        if node is None:
            return None
    return node


def attach_help_text_to_model(
    model: Any, address_map: dict[Address, list[str]]
) -> None:
    """Append each address's comment list to the corresponding model element.

    Comments are *appended* to any existing ``help_text`` entries, per
    CONV-F rule 7.

    :param model: The xsdata-produced root model instance (e.g. ``Scxml``).
    :param address_map: Output of :func:`extract_help_text_from_xml`.
    """
    if not address_map:
        return
    for address, comments in address_map.items():
        if not comments:
            continue
        target = _resolve_address(model, address)
        if target is None:
            continue
        existing = getattr(target, "help_text", None)
        if existing is None:
            # Element variant without help_text — skip silently.
            continue
        try:
            existing.extend(comments)
        except AttributeError:
            # pydantic v2 may treat list assignment specially; rebind.
            setattr(target, "help_text", list(existing) + list(comments))


# ---------------------------------------------------------------------------
# Post-pass: inject comments into xsdata-serialized XML.
# ---------------------------------------------------------------------------


def _collect_help_text_addresses(
    model: Any, address: Address, out: dict[Address, list[str]]
) -> None:
    """Walk ``model`` and record every non-empty ``help_text`` by address."""
    if model is None:
        return
    ht = getattr(model, "help_text", None)
    if ht:
        out[address] = list(ht)
    # Recurse into typed child fields.
    cls = type(model)
    mapping = _build_tag_to_attr_map(cls)
    for tag, attr in mapping.items():
        coll = getattr(model, attr, None)
        if coll is None:
            continue
        if isinstance(coll, list):
            for idx, child in enumerate(coll):
                child_addr = address + ((tag, idx),)
                _collect_help_text_addresses(child, child_addr, out)
        else:
            child_addr = address + ((tag, 0),)
            _collect_help_text_addresses(coll, child_addr, out)


def _navigate_xml(
    root: _ET._Element, address: Address
) -> _ET._Element | None:
    """Find the lxml element at ``address`` under ``root``.

    The first segment must match ``root``'s local name (we don't enforce it
    explicitly because xsdata always emits the same root name as the model).
    Subsequent segments index by ``(local_tag, index_among_same-tag_siblings)``.
    """
    if not address:
        return None
    node = root
    for tag, idx in address[1:]:
        match: _ET._Element | None = None
        count = 0
        for child in node:
            if _is_comment(child) or _is_processing_instruction(child):
                continue
            if _local_name(child.tag) == tag:
                if count == idx:
                    match = child
                    break
                count += 1
        if match is None:
            return None
        node = match
    return node


def _make_comment_nodes(entries: Iterable[str]) -> list[_ET._Element]:
    """Return one lxml Comment node per entry, content-safe per CONV-F."""
    nodes = []
    for entry in entries:
        body = emit_safe_comment_text(entry)
        nodes.append(_ET.Comment(body))
    return nodes


def inject_help_text_comments_into_xml(xml_str: str, model: Any) -> str:
    """Re-emit ``xml_str`` with ``help_text`` entries as leading XML comments.

    The input is the canonical XML produced by xsdata (no comments). The
    output is byte-equivalent except that for each model element with a
    non-empty ``help_text`` list, one ``<!-- ... -->`` node is inserted as
    an immediately preceding sibling, in array order, at the element's
    leading indentation. The root ``Scxml``'s entries land after the XML
    declaration and before the ``<scxml>`` start tag.

    Comment bodies are repaired with :func:`emit_safe_comment_text` so the
    serializer never emits the forbidden ``--`` sequence or a trailing
    ``-`` before ``-->``.

    :param xml_str: xsdata-produced SCXML string.
    :param model: The model whose ``help_text`` lists drive injection.
    :returns: SCXML string with leading comments inserted.
    """
    address_help: dict[Address, list[str]] = {}
    # Pull root local name from the xsdata output (it may be "scxml" or a
    # namespace-prefixed variant; we strip the prefix in addressing).
    parser = _ET.XMLParser(remove_comments=False, resolve_entities=False)
    try:
        tree = _ET.ElementTree(
            _ET.fromstring(
                xml_str.encode("utf-8") if isinstance(xml_str, str) else xml_str,
                parser=parser,
            )
        )
    except Exception:
        return xml_str
    root = tree.getroot()
    root_local = _local_name(root.tag)
    root_addr: Address = ((root_local, 0),)

    _collect_help_text_addresses(model, root_addr, address_help)
    if not address_help:
        return xml_str

    # Pop the root entries: they need special handling (insert before <scxml>
    # rather than as a child sibling).
    root_entries = address_help.pop(root_addr, None)

    # Process child entries in document order. Insert each comment as a
    # preceding sibling, copying the target's leading indentation (the
    # parent's existing text-before-target whitespace).
    for address, entries in address_help.items():
        target = _navigate_xml(root, address)
        if target is None:
            continue
        parent = target.getparent()
        if parent is None:
            continue
        # Determine the indentation used to introduce ``target``. lxml stores
        # it as the trailing whitespace of the preceding text node — which
        # is either parent.text (if target is first child) or
        # prev_sibling.tail. We want to preserve that exact prefix on each
        # injected comment so the result re-pretty-prints identically.
        prev = target.getprevious()
        if prev is None:
            leading_text = parent.text or ""
        else:
            leading_text = prev.tail or ""

        # Compute the indent string: the run of " "/"\t" that follows the
        # last newline in leading_text.
        if "\n" in leading_text:
            indent = leading_text.rsplit("\n", 1)[1]
        else:
            indent = leading_text

        comment_nodes = _make_comment_nodes(entries)
        # Insert each comment in array order, immediately before ``target``.
        # After insertion, the previous sibling becomes the new comment, so
        # we have to set tails so:
        #   prev.tail = leading_text (unchanged for the first comment)
        #   each comment.tail = "\n" + indent (so the next sibling continues
        #                        on a fresh line at the same indentation)
        # Finally, the last inserted comment's tail should be "\n" + indent
        # so target itself sits at the same indentation.
        idx = list(parent).index(target)
        for offset, cnode in enumerate(comment_nodes):
            parent.insert(idx + offset, cnode)
            cnode.tail = "\n" + indent if leading_text else ""
        # Make sure the *first* injected comment inherits the original
        # leading whitespace (preceding sibling tail / parent.text) — that
        # is already true, because we did not touch ``prev.tail`` /
        # ``parent.text``. The *target* node is now preceded by the last
        # comment whose tail provides the newline+indent.

    # Root-level entries: build comment nodes and insert them as siblings
    # before the root in the document. lxml lets us add them via
    # addprevious(); ElementTree-level "siblings of root" are preserved on
    # serialization with xml_declaration=True.
    serialized: bytes | str
    if root_entries:
        # Determine if the original xsdata output started with an XML
        # declaration so we can preserve it on the way out.
        had_decl = xml_str.lstrip().startswith("<?xml")

        # Insert root-level comments as document-root siblings before root.
        for entry in root_entries:
            body = emit_safe_comment_text(entry)
            root.addprevious(_ET.Comment(body))

        # Format with newline separators between root-level comments. lxml's
        # tostring of an ElementTree preserves root siblings; on a single
        # element it does not. So serialize the ElementTree.
        serialized = _ET.tostring(
            tree,
            encoding="utf-8",
            xml_declaration=had_decl,
            pretty_print=False,
        )
        out = serialized.decode("utf-8")
        # lxml does not auto-insert newlines between root-level comments
        # and the root element. Insert a newline between adjacent root-level
        # siblings for readability without breaking parsers.
        return _normalize_root_sibling_spacing(out)

    # No root-level entries — re-emit from root (matches original behavior).
    return _ET.tostring(root, encoding="unicode")


def _normalize_root_sibling_spacing(xml_text: str) -> str:
    """Insert a newline between adjacent root-level XML comments / root tag.

    lxml ``tostring`` packs root-level siblings tightly:
    ``<?xml ... ?><!--c--><!--d--><scxml ...>``. For readability we want a
    newline between each. This is purely cosmetic; the result is still a
    valid XML document.
    """
    # Walk the string and split on the boundaries between
    # ``--><!--`` and ``--><scxml`` (or any root start tag). We use simple
    # string replacement to avoid re-parsing.
    out = xml_text
    # Pretty-separate comment-to-comment boundaries.
    out = out.replace("--><!--", "-->\n<!--")
    # Separate the XML declaration from the first root-level node.
    out = out.replace("?><!--", "?>\n<!--")
    # Separate the last root-level comment from the root start tag.
    # Heuristic: a `-->` followed immediately by `<` and an element name
    # (not `!` or `?`) is the comment-to-root boundary.
    import re

    out = re.sub(r"-->(<[A-Za-z_])", r"-->\n\1", out)
    return out

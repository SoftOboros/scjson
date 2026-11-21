"""
Agent Name: executable-order-interchange

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Preserve direct SCXML executable child order across grouped SCJSON fields.
"""

from collections import Counter, defaultdict, deque

from lxml import etree
from pydantic import BaseModel, model_validator

from .comment_promotion import _resolve_child


NAMESPACE = "http://www.w3.org/2005/07/scxml"
ACTION_FIELDS = {
    "raise": "raise_value",
    "if": "if_value",
    "foreach": "foreach",
    "send": "send",
    "script": "script",
    "assign": "assign",
    "log": "log",
    "cancel": "cancel",
}
MARKER_FIELDS = {"elseif": "elseif", "else": "else_value"}


class MisplacedExecutionOrder(ValueError):
    """An SCJSON executable-order field appeared on a structural node."""


def validate_order_location(data, fields):
    """Reject reserved order metadata on typed nodes unable to own it."""
    if isinstance(data, dict) and "execution_order" in data and "execution_order" not in fields:
        raise MisplacedExecutionOrder("execution_order is valid only on an executable container")


class ScxmlModel(BaseModel):
    """Base of typed SCXML nodes. Opaque wildcard and attribute data are separate."""

    @model_validator(mode="before")
    @classmethod
    def _locate_execution_order(cls, data):
        validate_order_location(data, cls.model_fields)
        return data


def _kind(qname):
    """Use local names only for SCXML. Wildcard names retain their namespace."""
    if qname.startswith("{" + NAMESPACE + "}"):
        return qname.split("}", 1)[1]
    return qname if qname.startswith("{") else "{}" + qname


def _items(value):
    if value is None:
        return ()
    return value if isinstance(value, list) else (value,)


def ordered_children(container):
    """Return validated (XML kind, original payload) pairs or None for legacy input."""
    order = getattr(container, "execution_order", None)
    if order is None:
        return None
    if not isinstance(order, list) or not all(isinstance(kind, str) for kind in order):
        raise ValueError("execution_order must be an array of child-kind strings")
    queues = {}
    for kind, field in (ACTION_FIELDS | MARKER_FIELDS).items():
        queues[kind] = deque(_items(getattr(container, field, None)))
    for child in getattr(container, "other_element", ()):
        qname = child.get("qname") if isinstance(child, dict) else getattr(child, "qname", None)
        if not isinstance(qname, str) or not qname:
            raise ValueError("execution_order requires a QName for every extension child")
        key = _kind(qname)
        if not key.startswith("{"):
            raise ValueError("execution_order wildcard children must be outside the SCXML namespace")
        queues.setdefault(key, deque()).append(child)

    children = []
    saw_else = False
    for kind in order:
        if kind in MARKER_FIELDS:
            if not hasattr(container, "elseif"):
                raise ValueError(f"execution_order marker {kind!r} outside if")
            if saw_else:
                raise ValueError(f"execution_order marker {kind!r} after else")
            saw_else = kind == "else"
        if not queues.get(kind):
            raise ValueError(f"execution_order has an unknown or excess child {kind!r}")
        children.append((kind, queues[kind].popleft()))
    remaining = {kind: len(items) for kind, items in queues.items() if items}
    if remaining:
        raise ValueError(f"execution_order omits executable children {remaining}")
    return children


def _walk(element, model):
    """Pair standard XML children with their typed payloads using per-kind indexes."""
    yield element, model
    counters = Counter()
    for child in element:
        if not isinstance(child.tag, str) or not child.tag.startswith("{" + NAMESPACE + "}"):
            continue
        kind = _kind(child.tag)
        index = counters[kind]
        counters[kind] += 1
        payload = _resolve_child(model, kind, index)
        if payload is None and kind == "scxml":
            # xsdata places embedded invoke machines in mixed content.
            inline = [entry for entry in getattr(model, "content", ()) or ()
                      if type(entry).__name__ == "Scxml"]
            payload = inline[index] if index < len(inline) else None
        if payload is not None:
            yield from _walk(child, payload)


def capture_order(model, xml):
    # xsdata accepts a few legacy inputs with truncated outer markup. Capture
    # the same recovered tree after xsdata has accepted the input.
    parser = etree.XMLParser(recover=True, resolve_entities=False, no_network=True)
    root = etree.fromstring(xml if isinstance(xml, bytes) else xml.encode("utf-8"), parser)
    for element, container in _walk(root, model):
        if hasattr(container, "execution_order"):
            kinds = [_kind(child.tag) for child in element if isinstance(child.tag, str)]
            if len(set(kinds)) > 1 or any(kind in MARKER_FIELDS for kind in kinds):
                container.execution_order = kinds
                ordered_children(container)
                if len(set(kinds)) <= 1:
                    container.execution_order = None


def restore_order(model, xml):
    root = etree.fromstring(xml.encode("utf-8"), etree.XMLParser(resolve_entities=False, no_network=True))
    changed = False
    for element, container in _walk(root, model):
        sequence = ordered_children(container)
        if sequence is None:
            continue
        expected = [kind for kind, _ in sequence]
        if expected == [_kind(child.tag) for child in element]:
            continue
        groups = defaultdict(deque)
        tails = []
        for child in element:
            groups[_kind(child.tag)].append(child)
            tails.append(child.tail)
        if Counter(expected) != {kind: len(children) for kind, children in groups.items()}:
            raise ValueError("execution_order disagrees with the serialized XML children")
        element[:] = [groups[kind].popleft() for kind in expected]
        for child, tail in zip(element, tails):
            child.tail = tail
        changed = True
    if not changed:
        return xml
    declaration, sep, _ = xml.partition("?>")
    prefix = declaration + sep + "\n" if sep and xml.startswith("<?xml ") else ""
    return prefix + etree.tostring(root, encoding="unicode") + ("\n" if xml.endswith("\n") else "")


def canonical_json(model, data):
    """Remove absent order fields and retain the original singleton elseif wire shape."""
    if hasattr(model, "execution_order"):
        if model.execution_order is None:
            data.pop("execution_order", None)
        if isinstance(data.get("elseif"), list) and len(data["elseif"]) <= 1:
            data["elseif"] = next(iter(data["elseif"]), None)
    # Traverse model fields only; wildcard JSON and arbitrary user data are opaque.
    for name, value in data.items():
        field = getattr(model, name, None)
        if isinstance(value, dict) and field is not None and not isinstance(field, dict):
            if isinstance(field, list):
                if name != "elseif" or len(field) != 1:
                    continue
                field = field[0]
            canonical_json(field, value)
        elif isinstance(value, list) and isinstance(field, list):
            for child, item in zip(field, value):
                if isinstance(item, dict):
                    canonical_json(child, item)
    return data

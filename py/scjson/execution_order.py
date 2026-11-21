"""
Agent Name: executable-order-interchange

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Preserve executable and structural child order across grouped SCJSON fields.
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
REGION_KINDS = ("state", "parallel")
STATE_KINDS = (*REGION_KINDS, "final")


class MisplacedExecutionOrder(ValueError):
    """An SCJSON executable-order field appeared on a structural node."""


class InvalidStructuralOrder(ValueError):
    """A structural child sequence is invalid or misplaced."""


class InvalidRegionOrder(InvalidStructuralOrder):
    """A parallel region sequence is invalid or appears on another SCXML node."""


def validate_order_location(data, fields):
    """Reject reserved order metadata on typed nodes unable to own it."""
    if isinstance(data, dict) and "execution_order" in data and "execution_order" not in fields:
        raise MisplacedExecutionOrder("execution_order is valid only on an executable container")
    if isinstance(data, dict) and "region_order" in data and "region_order" not in fields:
        raise InvalidRegionOrder("region_order is valid only on a parallel")
    if isinstance(data, dict) and "state_order" in data and "state_order" not in fields:
        raise InvalidStructuralOrder("state_order is valid only on scxml and state")


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


def _ordered_structural(container, field, kinds):
    order = getattr(container, field, None)
    if order is None:
        return None
    error = InvalidRegionOrder if field == "region_order" else InvalidStructuralOrder
    if not isinstance(order, list):
        raise error(f"{field} must be an array of child kinds")
    queues = {kind: deque(getattr(container, kind)) for kind in kinds}
    children = []
    for kind in order:
        if kind not in kinds:
            raise error(f"{field} has an invalid kind {kind!r}")
        if not queues[kind]:
            raise error(f"{field} has an excess occurrence of {kind!r}")
        children.append((kind, queues[kind].popleft()))
    if any(queues.values()):
        raise error(f"{field} omits one or more direct children")
    return children


def ordered_regions(container):
    """Return validated (kind, region) pairs, or None for a legacy parallel."""
    return _ordered_structural(container, "region_order", REGION_KINDS)


def _structural_fields(container):
    if hasattr(container, "region_order"):
        return "region_order", REGION_KINDS
    return "state_order", STATE_KINDS


def ordered_state_children(container):
    """Return explicit structural order, or None for legacy grouped input."""
    return _ordered_structural(container, *_structural_fields(container))


def _iter_structural(container, field, kinds):
    children = _ordered_structural(container, field, kinds)
    if children is not None:
        yield from children
    else:
        for kind in kinds:
            for child in getattr(container, kind, ()):
                yield kind, child


def iter_regions(container):
    """Yield (kind, region) in explicit order or the legacy grouped order."""
    yield from _iter_structural(container, "region_order", REGION_KINDS)


def iter_state_children(container):
    """Yield direct state children in authored order or legacy grouped order."""
    yield from _iter_structural(container, *_structural_fields(container))


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
        field, kinds = _structural_fields(container)
        if hasattr(container, field):
            direct = [_kind(c.tag) for c in element if isinstance(c.tag, str)]
            order = [kind for kind in direct if kind in kinds]
            if len(set(order)) > 1:
                setattr(container, field, order)
                ordered_state_children(container)
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
        sequence = ordered_state_children(container)
        if sequence is not None:
            field, kinds = _structural_fields(container)
            slots = [i for i, child in enumerate(element) if _kind(child.tag) in kinds]
        else:
            sequence = ordered_children(container)
            slots = range(len(element))
            field = "execution_order"
        if sequence is None:
            continue
        expected = [kind for kind, _ in sequence]
        children = list(element)
        if expected == [_kind(children[i].tag) for i in slots]:
            continue
        groups = defaultdict(deque)
        tails = [child.tail for child in children]
        for i in slots:
            child = children[i]
            groups[_kind(child.tag)].append(child)
        if Counter(expected) != {kind: len(children) for kind, children in groups.items()}:
            raise ValueError(f"{field} disagrees with the serialized XML children")
        for i, kind in zip(slots, expected):
            children[i] = groups[kind].popleft()
        element[:] = children
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
    field, _ = _structural_fields(model)
    if hasattr(model, field) and getattr(model, field) is None:
        data.pop(field, None)
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

"""Check reserved child spellings at the SCJSON interchange boundary.

Agent Name: executable-key-intake

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

from . import dataclasses as models
from .comment_promotion import _build_tag_to_attr_map


ACTION_KEYS = {"raise": "raise_value", "if": "if_value", "else": "else_value"}


class InvalidExecutableKey(ValueError):
    """A reserved executable key would be ignored or shadow another spelling."""


def check_action_fields(data, fields, *, allow_camel=False, path=""):
    """Check a single modeled executable container before field coercion."""
    if not isinstance(data, dict) or "if_value" not in fields:
        return
    for tag, key in ACTION_KEYS.items():
        camel = tag + "Value"
        present = [name for name in (tag, camel, key) if name in data]
        if not present:
            continue
        name = present[0]
        if len(present) > 1:
            raise InvalidExecutableKey(f"{path}/{name}: conflicting spellings {', '.join(present)}")
        if key not in fields:
            raise InvalidExecutableKey(f"{path}/{name}: {tag!r} is only valid inside an if_value block")
        if name == tag or (name == camel and not allow_camel):
            raise InvalidExecutableKey(f"{path}/{name}: use {key!r} for the {tag!r} child")


def validate_executable_keys(data, *, allow_camel=False):
    """Check raw chart keys without validating unrelated fields in editor drafts.

    :param data: A decoded SCJSON document.
    :param allow_camel: Accept a single projected spelling before normalization.
    :raises InvalidExecutableKey: The diagnostic includes the input JSON pointer.
    """
    def walk(node, cls, path):
        if not isinstance(node, dict):
            return
        fields = _build_tag_to_attr_map(cls)
        check_action_fields(node, cls.__dataclass_fields__, allow_camel=allow_camel, path=path)
        for tag, key in fields.items():
            if allow_camel and tag in ACTION_KEYS and tag + "Value" in node:
                key = tag + "Value"
            if key in node:
                visit(node[key], getattr(models, tag.capitalize()), f"{path}/{key}")
        # <content> holds character data, XML wildcard nodes, or an embedded
        # SCXML document. Data, script, and extension payloads are opaque.
        if cls is models.Content:
            visit(node.get("content"), models.Scxml, path + "/content", mixed=True)

    def visit(value, cls, path, mixed=False):
        children = enumerate(value) if isinstance(value, list) else [(None, value)]
        for index, child in children:
            if mixed and isinstance(child, dict) and "qname" in child:
                continue
            walk(child, cls, path if index is None else f"{path}/{index}")

    walk(data, models.Scxml, "")

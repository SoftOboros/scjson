"""
Agent Name: executable-state-tree

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Structural state traversal and session-local identities shared by execution and lowering.
"""

from .execution_order import iter_state_children


def structural_children(node):
    """Visit selectable children in document order, followed by history pseudostates."""
    yield from iter_state_children(node)
    for history in getattr(node, "history", ()):
        yield "history", history


def anonymous_state_ids(root):
    """Allocate repeatable identities without colliding with authored IDs, including later siblings."""
    declared = set()
    unnamed = []

    def visit(parent):
        for kind, child in structural_children(parent):
            state_id = getattr(child, "id", None)
            if state_id:
                declared.add(state_id)
            else:
                unnamed.append((kind, child))
            visit(child)

    visit(root)
    if len(unnamed) == 1 and "anon" not in declared:
        # Preserve the interpreter's historic name when it identifies exactly one node.
        return {id(unnamed[0][1]): "anon"}
    result = {}
    for index, (kind, child) in enumerate(unnamed, 1):
        key = f"$generated-{kind}-{index}"
        while key in declared:
            key += "_"
        result[id(child)] = key
        declared.add(key)
    return result

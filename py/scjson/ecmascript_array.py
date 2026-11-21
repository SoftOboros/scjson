"""
Agent Name: ecmascript-array-execution

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Implement the JSON-array subset of Array.prototype.concat for the Python engine.
"""

import ast


class _ArrayOperations:
    @staticmethod
    def concat(receiver, *arguments):
        """Return a fresh shallow array, spreading each array argument by one level."""
        if not isinstance(receiver, list):
            raise TypeError("array concat requires an array receiver")
        result = receiver.copy()
        for value in arguments:
            if isinstance(value, list):
                result.extend(value)
            else:
                result.append(value)
        return result


def prepare_array_calls(source, env, mode="eval"):
    """Bind ECMAScript concat calls without changing names or data in the chart.

    :param source: Normalized ECMAScript expression or script.
    :param env: Original execution scope.
    :param mode: Python parsing mode, either eval or exec.
    :returns: Source and scope for the existing evaluator.
    """
    if "concat" not in source:
        return source, env
    try:
        tree = ast.parse(source, mode=mode)
    except SyntaxError:
        return source, env
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == "concat"]
    if not calls:
        return source, env
    # A chart can use our preferred implementation name as a normal variable.
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    binding = "_scjson_arrays"
    while binding in env or binding in names:
        binding += "_"
    for call in calls:
        receiver = call.func.value
        call.func.value = ast.Name(id=binding, ctx=ast.Load())
        call.args.insert(0, receiver)
    return ast.unparse(tree), {**env, binding: _ArrayOperations}

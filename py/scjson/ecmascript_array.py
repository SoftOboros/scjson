"""
Agent Name: ecmascript-array-execution

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Adapt JSON collection operations to ECMAScript semantics for the Python engine.
"""

import ast
import re


class _ArrayOperations:
    # Standard inherited string properties on ordinary JSON objects and arrays.
    object_properties = frozenset(
        "constructor hasOwnProperty isPrototypeOf propertyIsEnumerable toLocaleString "
        "toString valueOf __proto__ __defineGetter__ __defineSetter__ __lookupGetter__ __lookupSetter__".split()
    )
    array_properties = frozenset(
        "length at concat copyWithin entries every fill filter find findIndex findLast findLastIndex "
        "flat flatMap forEach includes indexOf join keys lastIndexOf map pop push reduce reduceRight "
        "reverse shift slice some sort splice toReversed toSorted toSpliced unshift values with".split()
    )

    @staticmethod
    def has_property(key, receiver):
        """Test JSON object keys and canonical array indices without searching values."""
        if key is None:
            key = "null"
        elif isinstance(key, bool):
            key = "true" if key else "false"
        elif isinstance(key, float) and key.is_integer():
            key = str(int(key))
        else:
            key = str(key)
        if isinstance(receiver, dict):
            return key in receiver or key in _ArrayOperations.object_properties
        if isinstance(receiver, list):
            if key in _ArrayOperations.array_properties or key in _ArrayOperations.object_properties:
                return True
            return bool(re.fullmatch(r"0|[1-9][0-9]{0,9}", key)) and int(key) < len(receiver)
        raise TypeError("the right operand of in must be an object")

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
    """Bind ECMAScript collection operations without changing names or data in the chart.

    :param source: Normalized ECMAScript expression or script.
    :param env: Original execution scope.
    :param mode: Python parsing mode, either eval or exec.
    :returns: Source and scope for the existing evaluator.
    """
    if "concat" not in source and not re.search(r"\bin\b", source):
        return source, env
    try:
        tree = ast.parse(source, mode=mode)
    except SyntaxError:
        return source, env
    # A chart can use our preferred implementation name as a normal variable.
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    binding = "_scjson_arrays"
    while binding in env or binding in names:
        binding += "_"
    class BindCollections(ast.NodeTransformer):
        changed = False

        def visit_Call(self, node):
            self.generic_visit(node)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "concat":
                node.args.insert(0, node.func.value)
                node.func.value = ast.Name(id=binding, ctx=ast.Load())
                self.changed = True
            return node

        def visit_Compare(self, node):
            self.generic_visit(node)
            if not any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops):
                return node
            if len(node.ops) != 1 or not isinstance(node.ops[0], ast.In):
                raise ValueError("unsupported compound ECMAScript property test")
            method = ast.Attribute(value=ast.Name(id=binding, ctx=ast.Load()), attr="has_property", ctx=ast.Load())
            self.changed = True
            return ast.copy_location(ast.Call(func=method, args=[node.left, node.comparators[0]], keywords=[]), node)

    adapter = BindCollections()
    tree = adapter.visit(tree)
    if not adapter.changed:
        return source, env
    return ast.unparse(tree), {**env, binding: _ArrayOperations}

#!/usr/bin/env python3
"""
Agent Name: patch_scxml-forward-ref

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

AST-based patch tool that cleans and redefines fields in ``ScxmlContentType``
inside xsdata-generated Python models.

Steps:
  1. Removes legacy ``field(...)`` declarations for content, expr and
     ``other_attributes``.
  2. Re-inserts cleaned ``Optional`` declarations and a ``field`` call with a
     ``default_factory`` for ``other_attributes``.
  3. Adds missing typing imports (``List``, ``Optional``).
  4. Formats the result with ``black``.

USAGE::
    python patch_scxml_ast.py --file path/to/generated.py
"""

import argparse
import ast
import re
import subprocess
from pathlib import Path
from typing import Dict, List


def extract_readme_descriptions(readme_path: Path) -> Dict[str, str]:
    """Parse ``README.md`` for name/description pairs.

    :param readme_path: Path to the ``README.md`` file.
    :returns: Mapping of class names to short descriptions.
    """
    doc_map: Dict[str, str] = {}
    pattern = re.compile(r"- `([^`]+)` \u2013 (.+)")
    for line in readme_path.read_text().splitlines():
        match = pattern.search(line)
        if match:
            doc_map[match.group(1)] = match.group(2).strip()
    return doc_map


class FieldStripper(ast.NodeTransformer):
    """Strip and replace legacy field declarations in a class."""

    def __init__(self, class_name: str, field_names: List[str]):
        """Create a new transformer.

        :param class_name: Name of the class to patch.
        :param field_names: Fields to remove before re-insertion.
        """
        self.class_name = class_name
        self.field_names = set(field_names)
        self.inside_target_class = False

    def visit_ClassDef(self, node):
        """Patch the target class definition.

        :param node: ``ast.ClassDef`` node under inspection.
        :returns: Modified ``ast.ClassDef`` node.
        """
        if node.name == self.class_name:
            self.inside_target_class = True
            node.body = [
                stmt for stmt in node.body if not self._is_field_to_remove(stmt)
            ]
            node = self._insert_clean_fields(node)
            self.inside_target_class = False
        return node

    def _is_field_to_remove(self, stmt):
        """Return ``True`` if ``stmt`` assigns one of the fields to remove."""
        return (
            isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and stmt.target.id in self.field_names
        )

    def _insert_clean_fields(self, node):
        """Insert the cleaned field declarations."""
        # content and expr as Optional
        new_fields = [
            self._make_optional(
                "content", 'Optional[List["Scxml"]]', "Recursive SCJSON"
            ),
            self._make_optional("expr", "Optional[str]", None),
            self._make_field_call(
                "other_attributes",
                "dict[str, str]",
                'field(default_factory=dict, title="Other Attributes")',
            ),
        ]
        insert_index = 0
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.ClassDef) and stmt.name == "Meta":
                insert_index = i
                break
        node.body[insert_index:insert_index] = new_fields
        return node

    def _make_optional(self, name, type_str, comment=None):
        """Create an optional annotated assignment."""
        node = ast.AnnAssign(
            target=ast.Name(id=name, ctx=ast.Store()),
            annotation=ast.parse(type_str).body[0].value,
            value=ast.Constant(value=None),
            simple=1,
        )
        return node

    def _make_field_call(self, name, type_str, field_expr: str):
        """Create a ``field`` annotated assignment."""
        return ast.AnnAssign(
            target=ast.Name(id=name, ctx=ast.Store()),
            annotation=ast.parse(type_str).body[0].value,
            value=ast.parse(field_expr).body[0].value,
            simple=1,
        )


class DocstringAdder(ast.NodeTransformer):
    """Insert docstrings from a lookup table when absent."""

    def __init__(self, mapping: Dict[str, str]):
        """Initialise transformer.

        :param mapping: Map of class names to docstring text.
        """
        self.mapping = mapping

    def visit_ClassDef(self, node: ast.ClassDef):
        """Attach a docstring when one is missing.

        :param node: ``ast.ClassDef`` node being visited.
        :returns: Modified ``ClassDef`` node.
        """
        doc = ast.get_docstring(node)
        if not doc and node.name in self.mapping:
            node.body.insert(
                0, ast.Expr(value=ast.Constant(value=self.mapping[node.name]))
            )
        return self.generic_visit(node)


def patch_generated_model(file_path: str, class_name: str, fields_to_remove: List[str]):
    """Patch a generated model file on disk.

    :param file_path: Target file to modify.
    :param class_name: Name of the class to patch.
    :param fields_to_remove: Legacy fields to strip and re-add.
    :returns: ``None``
    """
    path = Path(file_path)
    original_code = path.read_text()
    parsed = ast.parse(original_code)

    transformer = FieldStripper(class_name=class_name, field_names=fields_to_remove)
    modified_ast = transformer.visit(parsed)

    readme = Path(__file__).with_name("README.md")
    doc_map = extract_readme_descriptions(readme) if readme.exists() else {}
    if doc_map:
        modified_ast = DocstringAdder(doc_map).visit(modified_ast)

    modified_code = ast.unparse(modified_ast)

    # Post-processing to ensure List import
    lines = modified_code.splitlines()
    typing_line_found = False
    for i, line in enumerate(lines):
        if line.startswith("from typing import"):
            typing_line_found = True
            if "List" not in line:
                lines[i] = line.rstrip() + ", List"
            break
    if not typing_line_found:
        lines.insert(0, "from typing import Optional, List  # inserted by patch")

    # Write and format
    modified_code = "\n".join(lines)
    path.write_text(modified_code)
    subprocess.run(["black", str(path)], check=True)

    print(f"\n✅ Patched {file_path}")
    print(f"   • Cleaned and replaced fields in: {class_name}")
    print("   • Ensured typing imports")
    print("   • Formatted with Black")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Patch SCXML model for recursive schema compatibility."
    )
    parser.add_argument(
        "--file", required=True, help="Path to the generated Python model file."
    )
    parser.add_argument(
        "--class",
        dest="class_name",
        default="ScxmlContentType",
        help="Class name to patch.",
    )
    parser.add_argument(
        "--remove",
        nargs="+",
        default=["content", "expr", "other_attributes"],
        help="Field names to remove and rewrite.",
    )
    args = parser.parse_args()
    patch_generated_model(args.file, args.class_name, args.remove)

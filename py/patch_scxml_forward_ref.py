#!/usr/bin/env python3
"""
patch_scxml_ast.py

AST-based patch tool that cleans and redefines fields in `ScxmlContentType`
inside xsdata-generated Python models.

Steps:
  1. Removes legacy `field(...)` declarations for content, expr, other_attributes
  2. Re-inserts:
     • Optional[...] declarations for expr, content
     • Field(...) with default_factory for other_attributes
  3. Adds missing typing imports (List, Optional)
  4. Formats the result with `black`

USAGE:
    python patch_scxml_ast.py --file path/to/generated.py

AUTHOR:
    Softoboros Technology Inc.
"""

import argparse
import ast
import subprocess
from pathlib import Path
from typing import List


class FieldStripper(ast.NodeTransformer):
    def __init__(self, class_name: str, field_names: List[str]):
        self.class_name = class_name
        self.field_names = set(field_names)
        self.inside_target_class = False

    def visit_ClassDef(self, node):
        if node.name == self.class_name:
            self.inside_target_class = True
            node.body = [stmt for stmt in node.body if not self._is_field_to_remove(stmt)]
            node = self._insert_clean_fields(node)
            self.inside_target_class = False
        return node

    def _is_field_to_remove(self, stmt):
        return (
            isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and stmt.target.id in self.field_names
        )

    def _insert_clean_fields(self, node):
        # content and expr as Optional
        new_fields = [
            self._make_optional("content", 'Optional[List["Scxml"]]', "Recursive SCJSON"),
            self._make_optional("expr", "Optional[str]", None),
            self._make_field_call(
                "other_attributes",
                "dict[str, str]",
                "field(default_factory=dict, title=\"Other Attributes\")",
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
        node = ast.AnnAssign(
            target=ast.Name(id=name, ctx=ast.Store()),
            annotation=ast.parse(type_str).body[0].value,
            value=ast.Constant(value=None),
            simple=1,
        )
        return node

    def _make_field_call(self, name, type_str, field_expr: str):
        return ast.AnnAssign(
            target=ast.Name(id=name, ctx=ast.Store()),
            annotation=ast.parse(type_str).body[0].value,
            value=ast.parse(field_expr).body[0].value,
            simple=1,
        )


def patch_generated_model(file_path: str, class_name: str, fields_to_remove: List[str]):
    path = Path(file_path)
    original_code = path.read_text()
    parsed = ast.parse(original_code)

    transformer = FieldStripper(class_name=class_name, field_names=fields_to_remove)
    modified_ast = transformer.visit(parsed)
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
    parser = argparse.ArgumentParser(description="Patch SCXML model for recursive schema compatibility.")
    parser.add_argument("--file", required=True, help="Path to the generated Python model file.")
    parser.add_argument("--class", dest="class_name", default="ScxmlContentType", help="Class name to patch.")
    parser.add_argument(
        "--remove",
        nargs="+",
        default=["content", "expr", "other_attributes"],
        help="Field names to remove and rewrite.",
    )
    args = parser.parse_args()
    patch_generated_model(args.file, args.class_name, args.remove)

"""
Agent Name: python-jinja-gen

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Jinja2-based code generation helpers for producing language bindings and
schemas from scjson's Pydantic models. Used by CLI subcommands to emit
TypeScript, Rust, Swift, and Ruby artifacts, as well as the
``scjson.schema.json`` file.
"""

import sys
import os
from pathlib import Path
import importlib
import inspect
import textwrap
from typing import List
from enum import Enum
from pydantic import BaseModel
from jinja2 import Environment, select_autoescape, FileSystemLoader
from .CaseStyle import (
    to_camel,
    to_pascal,
    to_snake,
    to_scream,
    to_kebab,
    to_train,
)

class JinjaGenPydantic(object):
    """Render Pydantic models with Jinja2 templates.

    Params
    - template_path: Base folder for templates; defaults to bundled templates.
    - input: Root model name to discover (e.g., ``"Scxml"``).
    - output: Output directory for generated artifacts.
    - module: Module name exposing Pydantic models (e.g., ``"scjson.pydantic"``).
    - lang: Target language: ``"typescript"``, ``"rust"``, ``"swift"``, or ``"ruby"``.

    Returns
    - None
    """

    def __init__(
        self,
        template_path: str = "",
        input: str = "Scxml",
        output: str = "scjson",
        module: str = "scjson.pydantic",
        lang: str = "typescript",
    ) -> None:
        """Initialize the generator with optional configuration."""
        my_path = os.path.join(Path(__file__).parent, "templates")
        self.template_path = template_path or my_path
        self.output = output
        self.input = input
        self.module_name = module
        self.lang = lang
        self.interfaces = {}
        self.schema = {}
        self.schemas = {}
        self.objekts = {}
        self.schema = {}
        self.array_types = []
        self.env = Environment(loader=FileSystemLoader(self.template_path),
                autoescape=select_autoescape([]),
                trim_blocks=True,
                extensions=["jinja2.ext.do"]  # This enables {% do %}
                )
        self.env.globals.update(len=len)
        self.env.globals.update(range=range)
        self.env.globals.update(eval=eval)
        self.env.globals.update(sorted=sorted)
        self.env.globals.update(issubclass=issubclass)
        self.env.globals.update(type=type)
        self.env.globals.update(dir=dir)
        self.env.globals.update(str=str)
        self.env.globals.update(textwrap=textwrap)
        if self.lang == "rust":
            self.env.globals.update(
                get_field_default=JinjaGenPydantic._get_rust_default_value,
                get_field_type=JinjaGenPydantic._get_rust_field_type,
            )
        elif self.lang == "swift":
            self.env.globals.update(
                get_field_default=JinjaGenPydantic._get_swift_default_value,
                get_field_type=JinjaGenPydantic._get_swift_field_type,
                swift_prop_name=JinjaGenPydantic._swift_prop_name,
                swift_enum_case=JinjaGenPydantic._swift_enum_case,
                swift_enum_name=JinjaGenPydantic._swift_enum_name,
            )
        elif self.lang == "ruby":
            self.env.globals.update(
                get_field_default=JinjaGenPydantic._get_ruby_default_value,
                get_field_type=JinjaGenPydantic._get_ruby_field_type,
                ruby_attr_name=JinjaGenPydantic._ruby_attr_name,
                ruby_enum_name=JinjaGenPydantic._ruby_enum_name,
                ruby_from_hash=JinjaGenPydantic._ruby_from_hash_expr,
                ruby_to_hash=JinjaGenPydantic._ruby_to_hash_expr,
            )
        else:
            self.env.globals.update(
                get_field_default=JinjaGenPydantic._get_default_value,
                get_field_type=JinjaGenPydantic._get_field_type,
            )
        self.env.globals.update(
            get_schema_types=JinjaGenPydantic._get_schema_types,
            list_join=JinjaGenPydantic._list_join,
            is_field_enum=JinjaGenPydantic._is_field_enum,
            first_enum=JinjaGenPydantic._first_enum_member,
            first_enum_value=JinjaGenPydantic._first_enum_value,
            rust_ident=JinjaGenPydantic._rust_ident,
        )
        self.env.globals.update(    to_camel=to_camel,
                                    to_pascal=to_pascal,
                                    to_snake=to_snake,
                                    to_scream=to_scream,
                                    to_kebab=to_kebab,
                                    to_train=to_train
                                )
        #Find all Pydantic models in a given module.
        if self.module_name not in sys.modules:
            module = importlib.import_module(self.module_name)
        else:
            module = sys.modules[self.module_name]
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if ((issubclass(obj, BaseModel) or issubclass(obj, Enum))
                    and obj is not BaseModel
                    and (name == input or name.find(input) != 0)):
                try:
                    self.objekts[name] = obj
                except Exception as e:
                    print(f"Skipping {name} due to schema generation error: {e}")
        # collect array types for tempalate use.
        ptuples = {}
        for name, objekt in self.objekts.items():
            if not self._check_props(objekt, name):
                continue
            for prop_name, prop in self.schema['properties'].items():
                if "type" in prop and prop["type"] == "array" and "items" in prop and "$ref"in prop["items"]:
                    p_type = prop["items"]["$ref"].split("/")[-1]
                    ptuples[(name, prop_name)] = p_type
        self.all_arrays = sorted(list(set(ptuples.values())))
        self.name_field = "id"

    def render_to_file(self, out_name: str, template_name: str, template_env: dict = {}) -> None:
        """Render a template to an output file.

        Params
        - out_name: Destination file name, relative to ``self.output``.
        - template_name: Template filename within ``self.template_path``.
        - template_env: Variables exported to the template context.

        Returns
        - None
        """
        outname = os.path.join(self.output, out_name)
        ts = self.env.get_template(template_name).render(template_env)
        with open(outname, "w") as tsfile:
            tsfile.write(ts)
        print(f'Generated: {outname}')

    def _get_default_value(prop: dict, defs: dict = None) -> str:
        """Extracts the correct default value for a property in the Pydantic schema."""
        def get_fallback_default(prop: dict) -> str:
            """Returns a sensible default value when no explicit default is provided."""
            type_name = prop["type"]
            items = prop["items"] if "items" in prop else ""
            if items and '$ref' in items:
                items = items['$ref'].split('/')[-1] + 'Props'
            return {
                "string": '""',
                "integer": "0",
                "number": "0.0",
                "boolean": "false",
                "array": "[]",
                "object": "{}",
            }.get(type_name, "null")  # Default to null for unknown types
        ret_val = "null"
        if "type" in prop:
            if "default" in prop:
                if prop["type"] == "string":
                    ret_val = f'"{prop["default"]}"'
                else:
                    ret_val = prop["default"]
            else:
                ret_val = get_fallback_default(prop)
        elif "$ref" in prop:
            ref_name = prop["$ref"].split("/")[-1]
            if "default" in prop:
                ret_val = f'{ref_name}Props.{to_pascal(prop["default"])}'
            elif ref_name in defs and 'enum' in defs[ref_name]:
                ret_val = f'{ref_name}Props.{to_pascal(defs[ref_name]["enum"][0])}'
            else:
                ret_val = f'default{ref_name}()'
        if "anyOf" in prop:
            for option in prop["anyOf"]:
                if option.get("type") and option["type"] != "null":
                    ret_val = prop.get("default", get_fallback_default(option))                    
                    break
        if ret_val == "None" or ret_val == None:
            ret_val = "null"
        return ret_val

    def _get_field_type(prop: dict | str) -> str:
        """Extracts the correct type for a property in the Pydantic schema."""
        def xlate_type(prop: dict | str, is_array: bool = False) -> str:
            if "type" in prop:
                if prop["type"] == "array":
                    p_type = f"{xlate_type(prop['items'], is_array=True)}[]"
                else:
                    p_type = prop["type"]
            elif '$ref' in prop:
                p_type = prop['$ref'].split('/')[-1] + 'Props'
            else:
                p_type = str(prop)
            return ('null' if p_type in ['None', None, 'null']
                            else 'number' if p_type == 'integer'
                            else f'{p_type}[]' if p_type == 'array'
                            else 'Record<string, object>' if p_type in ['object', '{}']
                            else p_type)
        ret_val = "null"
        # Case 1: Simple `type` field with a direct default
        if "type" in prop or "$ref" in prop:
            ret_val = xlate_type(prop)
        # Case 2: `anyOf` case (handling optional fields)
        if "anyOf" in prop:
            types = sorted(
                [xlate_type(t) for t in prop["anyOf"]],
                key=lambda t: (t == "null")
            )            
            ret_val = ' | '.join(types)
        # None -> null, integer -> number, else ->
        return ret_val

    def _get_rust_default_value(prop: dict, defs: dict | None = None) -> str:
        """Return a Rust expression for the property's default value."""

        def get_fallback(prop: dict) -> str:
            type_name = prop.get("type")
            mapping = {
                "string": 'String::new()',
                "integer": "0",
                "number": "0.0",
                "boolean": "false",
                "array": "Vec::new()",
                "object": "Map::new()",
            }
            return mapping.get(type_name, "Value::Null")

        ret_val = "Value::Null"
        if "type" in prop:
            if "default" in prop:
                if prop["type"] == "string":
                    ret_val = f'"{prop["default"]}".to_string()'
                elif prop["type"] == "boolean":
                    ret_val = str(prop["default"]).lower()
                else:
                    ret_val = str(prop["default"])
            else:
                ret_val = get_fallback(prop)
        elif "$ref" in prop:
            ref_name = prop["$ref"].split("/")[-1]
            if "default" in prop:
                ret_val = f'{ref_name}Props::{to_pascal(prop["default"])}'
            elif defs and ref_name in defs and "enum" in defs[ref_name]:
                first = defs[ref_name]["enum"][0]
                ret_val = f'{ref_name}Props::{to_pascal(first)}'
            else:
                ret_val = f'default_{ref_name.lower()}()'
        if "anyOf" in prop:
            has_null = any(opt.get("type") == "null" for opt in prop["anyOf"])
            ret_val = "None" if has_null else "Value::Null"
        return ret_val

    def _get_rust_field_type(prop: dict | str) -> str:
        """Return the Rust type for a schema property."""

        def xlate(prop: dict | str) -> str:
            if "type" in prop:
                if prop["type"] == "array":
                    return f"Vec<{xlate(prop['items'])}>"
                else:
                    dtype = prop["type"]
            elif "$ref" in prop:
                dtype = prop["$ref"].split("/")[-1] + "Props"
            else:
                dtype = str(prop)
            return (
                "String" if dtype == "string" else
                "i64" if dtype == "integer" else
                "f64" if dtype == "number" else
                "bool" if dtype == "boolean" else
                "Vec<Value>" if dtype == "array" else
                "Map<String, Value>" if dtype in ["object", "{}"] else
                dtype
            )

        ret_val = "None"
        if "type" in prop or "$ref" in prop:
            ret_val = xlate(prop)
        elif "anyOf" in prop:
            types = [xlate(t) for t in prop["anyOf"] if t.get("type") != "null"]
            if len(types) == 1:
                ret_val = f"Option<{types[0]}>"
            else:
                ret_val = "Value"
        return ret_val

    @staticmethod
    def _analyze_property(prop: dict, defs: dict | None = None) -> dict:
        """Return normalized metadata for a schema property."""

        if prop is None:
            return {"nullable": True, "variant": "any", "schema": None}

        nullable = False
        working = prop
        if "anyOf" in prop:
            non_null = [opt for opt in prop["anyOf"] if opt.get("type") != "null"]
            if len(non_null) == 1:
                nullable = True
                working = non_null[0]
            else:
                return {"nullable": True, "variant": "any", "schema": prop}

        if "$ref" in working:
            ref = working["$ref"].split("/")[-1]
            schema = (defs or {}).get(ref, {})
            if schema.get("enum"):
                return {
                    "nullable": nullable,
                    "variant": "enum",
                    "ref": ref,
                    "values": schema.get("enum", []),
                    "schema": working,
                }
            return {
                "nullable": nullable,
                "variant": "model",
                "ref": ref,
                "schema": working,
            }

        dtype = working.get("type")
        if dtype == "array":
            item_schema = working.get("items") or {}
            item_info = JinjaGenPydantic._analyze_property(item_schema, defs)
            return {
                "nullable": nullable,
                "variant": "array",
                "item": item_info,
                "schema": working,
                "item_schema": item_schema,
            }

        if dtype == "object":
            return {"nullable": nullable, "variant": "object", "schema": working}

        if dtype in {"string", "integer", "number", "boolean"}:
            return {
                "nullable": nullable,
                "variant": "primitive",
                "type": dtype,
                "schema": working,
            }

        if dtype == "null":
            return {"nullable": True, "variant": "any", "schema": working}

        return {"nullable": nullable, "variant": "any", "schema": working}

    @staticmethod
    def _swift_enum_name(ref: str) -> str:
        return f"{to_pascal(ref)}Props"

    @staticmethod
    def _swift_enum_case(value: str) -> str:
        return JinjaGenPydantic._swift_ident(to_camel(value))

    @staticmethod
    def _swift_prop_name(name: str) -> str:
        return JinjaGenPydantic._swift_ident(to_camel(name))

    @staticmethod
    def _swift_ident(name: str) -> str:
        ident = name or "value"
        keywords = {
            "associatedtype", "class", "deinit", "enum", "extension", "func",
            "import", "init", "inout", "let", "operator", "private", "protocol",
            "public", "rethrows", "static", "struct", "subscript", "typealias",
            "var", "break", "case", "continue", "default", "defer", "do", "else",
            "fallthrough", "for", "guard", "if", "in", "internal", "repeat", "return",
            "switch", "where", "while", "as", "Any", "catch", "false", "is",
            "nil", "throw", "throws", "true", "try", "await", "async", "actor"
        }
        if ident and ident[0].isdigit():
            ident = f"_{ident}"
        if ident in keywords:
            return f"`{ident}`"
        return ident

    @staticmethod
    def _swift_literal(value) -> str:
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace("\"", "\\\"")
            escaped = escaped.replace("\n", "\\n")
            return f'"{escaped}"'
        if isinstance(value, list):
            inner = ", ".join(JinjaGenPydantic._swift_literal(v) for v in value)
            return f"[{inner}]"
        if isinstance(value, dict):
            return "[:]"
        return "JSONValue.null"

    @staticmethod
    def _swift_json_value_literal(value) -> str:
        if value is None:
            return "JSONValue.null"
        if isinstance(value, bool):
            return "JSONValue.bool(true)" if value else "JSONValue.bool(false)"
        if isinstance(value, int):
            return f"JSONValue.integer({value})"
        if isinstance(value, float):
            return f"JSONValue.number({value})"
        if isinstance(value, str):
            return f"JSONValue.string({JinjaGenPydantic._swift_literal(value)})"
        if isinstance(value, list):
            inner = ", ".join(JinjaGenPydantic._swift_json_value_literal(v) for v in value)
            return f"JSONValue.array([{inner}])"
        if isinstance(value, dict):
            return "JSONValue.object([:])"
        return "JSONValue.null"

    @staticmethod
    def _get_swift_field_type(prop: dict, defs: dict | None = None) -> str:
        info = JinjaGenPydantic._analyze_property(prop, defs)
        variant = info["variant"]
        nullable = info.get("nullable", False)

        if variant == "primitive":
            mapping = {
                "string": "String",
                "integer": "Int",
                "number": "Double",
                "boolean": "Bool",
            }
            base = mapping.get(info.get("type"), "JSONValue")
        elif variant == "enum":
            base = JinjaGenPydantic._swift_enum_name(info["ref"])
        elif variant == "model":
            base = f"{info['ref']}Props"
        elif variant == "array":
            item_schema = info.get("item_schema") or info.get("schema", {}).get("items")
            inner = JinjaGenPydantic._get_swift_field_type(item_schema, defs) if item_schema else "JSONValue"
            inner = inner[:-1] if inner.endswith("?") else inner
            base = f"[{inner}]"
        elif variant == "object":
            base = "JSONDictionary"
        else:
            base = "JSONValue"

        if nullable and not base.endswith("?") and not base.startswith("["):
            base = f"{base}?"
        elif nullable and base.startswith("["):
            base = f"{base}?"

        return base

    @staticmethod
    def _get_swift_default_value(prop: dict, defs: dict | None = None) -> str:
        if prop is None:
            return "nil"

        info = JinjaGenPydantic._analyze_property(prop, defs)
        variant = info["variant"]
        nullable = info.get("nullable", False)

        if "default" in prop:
            default_value = prop["default"]
            if default_value is None:
                return "nil"
            if variant == "enum":
                enum_name = JinjaGenPydantic._swift_enum_name(info["ref"])
                case_name = JinjaGenPydantic._swift_enum_case(str(default_value))
                return f"{enum_name}.{case_name}"
            if variant == "any":
                return JinjaGenPydantic._swift_json_value_literal(default_value)
            return JinjaGenPydantic._swift_literal(default_value)

        if nullable:
            return "nil"

        if variant == "primitive":
            mapping = {
                "string": '""',
                "integer": "0",
                "number": "0.0",
                "boolean": "false",
            }
            return mapping.get(info.get("type"), "JSONValue.null")

        if variant == "enum":
            enum_name = JinjaGenPydantic._swift_enum_name(info["ref"])
            values = info.get("values") or []
            default_case = values[0] if values else ""
            case_name = JinjaGenPydantic._swift_enum_case(default_case)
            return f"{enum_name}.{case_name}"

        if variant == "model":
            return f"{info['ref']}Props()"

        if variant == "array":
            return "[]"

        if variant == "object":
            return "[:]"

        return "JSONValue.null"

    @staticmethod
    def _ruby_enum_name(ref: str) -> str:
        return f"{to_pascal(ref)}Props"

    @staticmethod
    def _ruby_class_name(ref: str) -> str:
        return f"{ref}Props"

    @staticmethod
    def _ruby_attr_name(name: str) -> str:
        ident = to_snake(name) or name
        if ident and ident[0].isdigit():
            ident = f"_{ident}"
        keywords = {
            "alias", "and", "begin", "break", "case", "class", "def", "defined",
            "do", "else", "elsif", "end", "ensure", "false", "for", "if", "in",
            "module", "next", "nil", "not", "or", "redo", "rescue", "retry",
            "return", "self", "super", "then", "true", "undef", "unless", "until",
            "when", "while", "yield"
        }
        if ident in keywords:
            ident = f"{ident}_attr"
        return ident

    @staticmethod
    def _ruby_literal(value) -> str:
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace("'", "\\'")
            escaped = escaped.replace("\n", "\\n")
            return f"'{escaped}'"
        if isinstance(value, list):
            inner = ", ".join(JinjaGenPydantic._ruby_literal(v) for v in value)
            return f"[{inner}]"
        if isinstance(value, dict):
            return "{}"
        return "nil"

    @staticmethod
    def _get_ruby_field_type(prop: dict, defs: dict | None = None) -> str:
        info = JinjaGenPydantic._analyze_property(prop, defs)
        variant = info["variant"]
        if variant == "primitive":
            mapping = {
                "string": "String",
                "integer": "Integer",
                "number": "Float",
                "boolean": "Boolean",
            }
            return mapping.get(info.get("type"), "Object")
        if variant == "enum":
            return "String"
        if variant == "model":
            return JinjaGenPydantic._ruby_class_name(info["ref"])
        if variant == "array":
            return "Array"
        if variant == "object":
            return "Hash"
        return "Object"

    @staticmethod
    def _get_ruby_default_value(prop: dict, defs: dict | None = None) -> str:
        if prop is None:
            return "nil"

        info = JinjaGenPydantic._analyze_property(prop, defs)
        variant = info["variant"]
        if "default" in prop:
            default_value = prop["default"]
            if default_value is None:
                return "nil"
            if variant == "enum":
                enum_name = JinjaGenPydantic._ruby_enum_name(info["ref"])
                const = to_scream(str(default_value))
                return f"{enum_name}::{const}"
            return JinjaGenPydantic._ruby_literal(default_value)
        if info.get("nullable", False):
            return "nil"
        if variant == "primitive":
            mapping = {
                "string": "''",
                "integer": "0",
                "number": "0.0",
                "boolean": "false",
            }
            return mapping.get(info.get("type"), "nil")
        if variant == "enum":
            enum_name = JinjaGenPydantic._ruby_enum_name(info["ref"])
            values = info.get("values") or []
            default = values[0] if values else None
            if default is None:
                return "nil"
            const = to_scream(default)
            return f"{enum_name}::{const}"
        if variant == "model":
            return f"{JinjaGenPydantic._ruby_class_name(info['ref'])}.new"
        if variant == "array":
            return "[]"
        if variant == "object":
            return "{}"
        return "nil"

    @staticmethod
    def _ruby_from_hash_expr(field_name: str, prop: dict, defs: dict | None = None) -> str:
        info = JinjaGenPydantic._analyze_property(prop, defs)
        key = field_name
        nullable = info.get("nullable", False)
        default_expr = JinjaGenPydantic._get_ruby_default_value(prop, defs)

        if info["variant"] == "enum":
            enum_name = JinjaGenPydantic._ruby_enum_name(info["ref"])
            allow_nil = ", allow_nil: true" if nullable else ""
            if nullable:
                return f"normalized.key?('{key}') ? {enum_name}.coerce(normalized['{key}']{allow_nil}) : {default_expr}"
            return f"{enum_name}.coerce(normalized.fetch('{key}', {default_expr}){allow_nil})"

        if info["variant"] == "model":
            class_name = JinjaGenPydantic._ruby_class_name(info["ref"])
            if nullable:
                return f"normalized.key?('{key}') && normalized['{key}'] ? {class_name}.from_hash(normalized['{key}']) : nil"
            return f"normalized.key?('{key}') && normalized['{key}'] ? {class_name}.from_hash(normalized['{key}']) : {class_name}.new"

        if info["variant"] == "array":
            item_info = info["item"] if isinstance(info["item"], dict) else {}
            if item_info.get("variant") == "model":
                class_name = JinjaGenPydantic._ruby_class_name(item_info["ref"])
                if nullable:
                    return (
                        "begin\n"
                        f"          value = normalized.fetch('{key}', nil)\n"
                        f"          value.nil? ? nil : Array(value).map {{ |item| {class_name}.from_hash(item) }}\n"
                        "        end"
                    )
                return f"Array(normalized.fetch('{key}', [])).map {{ |item| {class_name}.from_hash(item) }}"
            if item_info.get("variant") == "enum":
                enum_name = JinjaGenPydantic._ruby_enum_name(item_info["ref"])
                if nullable:
                    return (
                        "begin\n"
                        f"          value = normalized.fetch('{key}', nil)\n"
                        f"          value.nil? ? nil : Array(value).map {{ |item| {enum_name}.coerce(item) }}\n"
                        "        end"
                    )
                return f"Array(normalized.fetch('{key}', [])).map {{ |item| {enum_name}.coerce(item) }}"
            if nullable:
                return (
                    "begin\n"
                    f"          value = normalized.fetch('{key}', nil)\n"
                    "          value.nil? ? nil : Array(value)\n"
                    "        end"
                )
            return f"Array(normalized.fetch('{key}', []))"

        if info["variant"] == "object":
            if nullable:
                return f"normalized.fetch('{key}', nil)"
            return f"normalized.fetch('{key}', {{}})"

        if info["variant"] == "primitive":
            if nullable:
                return f"normalized.fetch('{key}', nil)"
            return f"normalized.fetch('{key}', {default_expr})"

        if nullable:
            return f"normalized.fetch('{key}', nil)"
        return f"normalized.fetch('{key}', {default_expr})"

    @staticmethod
    def _ruby_to_hash_expr(field_name: str, prop: dict, defs: dict | None = None) -> str:
        info = JinjaGenPydantic._analyze_property(prop, defs)
        attr = JinjaGenPydantic._ruby_attr_name(field_name)
        if info["variant"] == "model":
            return f"@{attr}&.to_hash"
        if info["variant"] == "array":
            item_info = info["item"] if isinstance(info["item"], dict) else {}
            if item_info.get("variant") == "model":
                return f"(@{attr} || []).map {{ |item| item.respond_to?(:to_hash) ? item.to_hash : item }}"
            return f"@{attr}"
        return f"@{attr}"

    def _first_enum_member(enum_cls: Enum) -> str:
        """Return the first member name of an Enum class."""
        return next(iter(enum_cls.__members__.keys()))

    def _first_enum_value(enum_cls: Enum):
        """Return the first enumeration value."""
        return next(iter(enum_cls.__members__.values())).value

    def _rust_ident(name: str) -> str:
        """Escape Rust keywords for identifiers."""
        keywords = {
            "as", "break", "const", "continue", "crate", "else", "enum", "extern",
            "false", "fn", "for", "if", "impl", "in", "let", "loop", "match",
            "mod", "move", "mut", "pub", "ref", "return", "self", "Self",
            "static", "struct", "super", "trait", "true", "type", "unsafe",
            "use", "where", "while", "async", "await", "dyn", "abstract",
            "become", "box", "do", "final", "macro", "override", "priv",
            "typeof", "unsized", "virtual", "yield", "try", "union",
        }
        return f"r#{name}" if name in keywords else name

    def _get_schema_types(schema: dict, name: str = "") -> List[str]:
        """Template helper to return the reference type from teh schema."""
        t_list = [f'{name}'] if name else []
        for _, prop in schema['properties'].items():
            if "type" in prop:
                if prop["type"].find('$ref') == 0:
                    t_list.append(f'{prop["$ref"].split("/")[-1]}[]')
                elif prop["type"] == "array" and "items" in prop:
                    if type(prop["items"]) == dict and '$ref' in prop["items"]:
                        t_list.append(JinjaGenPydantic._get_field_type(prop["items"])[:-5] + '[]')
            elif "anyOf" in prop:
                for option in prop["anyOf"]:
                    if "$ref" in option:
                        t_name = f'{option["$ref"].split("/")[-1]}'
                        if 'enum' not in schema['$defs'][t_name]:
                            t_list.append(t_name)
            elif '$ref' in prop:
                t_name = f'{prop["$ref"].split("/")[-1]}'
                if 'enum' not in schema['$defs'][t_name]:
                    t_list.append(t_name)
        return set(t_list)

    def _is_field_enum(prop: dict | str, schema: dict) -> bool:
        "Templat helper function to "
        ret_val = False
        if "$ref" in prop:
            ref = prop["$ref"].split("/")[-1]
            ret_val = "enum" in schema["$defs"][ref]
        elif "anyOf" in prop:
            for option in prop["anyOf"]:
                if option.get("$ref"):
                    ref = option["$ref"].split("/")[-1]
                    ret_val = "enum" in schema["$defs"][ref]
                    break
        return ret_val
    
    def _list_join(s_list:list[str], sep:str=' ', pre:str="", post:str="", indent=-1, fn:str=None, wrap=80) -> str: 
        """Template helper for comprehend lists (not supported in tempaltes)."""
        ret_val,  join_list, length = [], [], 0
        for field in s_list:
            length += len(pre + field + post) + len(sep)
            if indent > 1 and length > wrap:
                ret_val.append(sep.join(join_list))
                join_list, length = [], 0
            join_list.append(pre + field + post)
        ret_val.append(sep.join(join_list))
        return ("\n" + indent * " " + sep).join(ret_val)

    def _check_props(self, objekt, name) -> bool:
        """Check for missing props and update from references."""
        is_ok = True
        if issubclass(objekt, Enum):
            self.interfaces[name] = objekt
            is_ok = False
        else:
            objekt.model_rebuild()
            self.schemas[name] = self.schema = objekt.model_json_schema()
            self.interfaces[name] = self.schema
            if "properties" not in self.schema:
                try:
                    o_name =  self.schema['$ref'].split('/')[-1]
                    if o_name in self.schema['$defs']:
                        self.schema['properties'] = self.schema['$defs'][o_name]['properties']
                except KeyError:
                    is_ok = False
        return is_ok

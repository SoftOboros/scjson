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
    """A class to render pydntic models using jinja2 templates."""

    def __init__(
        self,
        template_path: str = "",
        input: str = "Scxml",
        output: str = "scjson",
        module: str = "scjson.pydantic",
        lang: str = "typescript",
    ):
        """Initilize with optional config."""
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
        """Render a templat to an output file adding local variables."""
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

    def _first_enum_member(enum_cls: Enum) -> str:
        """Return the first member name of an Enum class."""
        return next(iter(enum_cls.__members__.keys()))

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

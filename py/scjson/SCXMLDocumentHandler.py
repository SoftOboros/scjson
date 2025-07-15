from typing import Optional, Type, Union, Any, get_args, get_origin
from enum import Enum
from decimal import Decimal
import xmlschema
import json
from dataclasses import asdict, fields, is_dataclass
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer
from .dataclasses import Scxml as Scxml

class SCXMLDocumentHandler:
    def __init__(
        self,
        model_class: Type = Scxml,
        schema_path: Optional[str] = None,
        pretty: bool = True,
        omit_empty: bool = True,
    ) -> None:
        self.model_class = model_class
        self.schema_path = schema_path
        self.parser = XmlParser()
        self.serializer = XmlSerializer(
            config=SerializerConfig(
                pretty_print=pretty, encoding="utf-8", xml_declaration=True
            )
        )
        self.schema = xmlschema.XMLSchema(schema_path) if schema_path else None
        self.omit_empty = omit_empty

    def validate(self, xml_path: str) -> bool:
        if not self.schema:
            raise ValueError("No schema path provided for validation.")
        return self.schema.is_valid(xml_path)

    def load(self, xml_path: str):
        with open(xml_path, "rb") as f:
            return self.parser.from_bytes(f.read(), self.model_class)

    def dump(self, instance, output_path: str):
        xml_string = self.serializer.render(instance)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_string)

    def to_string(self, instance) -> str:
        return self.serializer.render(instance)

    def _fix_decimal(obj):
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, dict):
            return {k: SCXMLDocumentHandler._fix_decimal(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [SCXMLDocumentHandler._fix_decimal(v) for v in obj]
        return obj

    @staticmethod
    def _remove_empty(obj: Any):
        """Recursively remove keys with None or empty containers."""
        if isinstance(obj, dict):
            return {
                k: SCXMLDocumentHandler._remove_empty(v)
                for k, v in obj.items()
                if v is not None
                and not (isinstance(v, (list, dict)) and len(v) == 0)
            }
        if isinstance(obj, list):
            return [
                SCXMLDocumentHandler._remove_empty(v)
                for v in obj
                if v is not None
                and not (isinstance(v, (list, dict)) and len(v) == 0)
            ]
        return obj

    def xml_to_json(self, xml_str: str) -> str:
        """Convert SCXML string to canonical JSON."""
        model = self.parser.from_string(xml_str, self.model_class)
        if hasattr(model, "model_dump"):
            data = model.model_dump()
        else:
            data = asdict(model)
        data = SCXMLDocumentHandler._fix_decimal(data)
        if self.omit_empty:
            data = SCXMLDocumentHandler._remove_empty(data)
        return json.dumps(data, indent=2)

    def _to_dataclass(self, cls: type, data: Any):
        """Recursively build dataclass instance from dict."""
        origin = get_origin(cls)
        if origin is list:
            item_type = get_args(cls)[0]
            return [self._to_dataclass(item_type, x) for x in data]
        if origin is Union:
            for arg in get_args(cls):
                if arg is type(None):
                    continue
                try:
                    return self._to_dataclass(arg, data)
                except Exception:
                    pass
            return data
        if is_dataclass(cls):
            kwargs = {}
            post = {}
            for f in fields(cls):
                if f.name not in data:
                    continue
                value = self._to_dataclass(f.type, data[f.name])
                if f.type is Decimal or f.name == "version":
                    try:
                        value = Decimal(str(value))
                    except Exception:
                        pass
                if f.init:
                    # xsdata dataclasses mark some attributes with init=False.
                    # Handle them after instantiation to avoid TypeError.
                    kwargs[f.name] = value
                else:
                    post[f.name] = value
            obj = cls(**kwargs)
            for name, value in post.items():
                setattr(obj, name, value)
            return obj
        if isinstance(cls, type) and issubclass(cls, Enum):
            try:
                return cls(data)
            except Exception:
                return data
        return data

    def json_to_xml(self, json_str: str) -> str:
        """Convert stored JSON string to SCXML."""
        data = json.loads(json_str)
        if hasattr(self.model_class, "model_validate"):
            model = self.model_class.model_validate(data)
        else:
            model = self._to_dataclass(self.model_class, data)
        return self.to_string(model)


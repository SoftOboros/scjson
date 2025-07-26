"""
Agent Name: scxml-document-handler

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Utilities for loading, validating, and converting SCXML documents to and from
their JSON representation.  The underlying :class:`~xsdata.formats.dataclass.parsers.XmlParser`
can enforce strict schema checking.  By default unknown XML elements raise an
exception; set ``fail_on_unknown_properties=False`` when instantiating
:class:`SCXMLDocumentHandler` to ignore and skip unrecognised fields during
parsing.
"""

from typing import Optional, Type, Union, Any, get_args, get_origin, ForwardRef
from enum import Enum
from decimal import Decimal
import xmlschema
import json
from dataclasses import asdict, fields, is_dataclass
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.models.generics import AnyElement
from . import dataclasses as dataclasses_module
from .dataclasses import Scxml as Scxml
from xml.etree import ElementTree as ET

class SCXMLDocumentHandler:
    def __init__(
        self,
        model_class: Type = Scxml,
        schema_path: Optional[str] = None,
        pretty: bool = True,
        omit_empty: bool = True,
        fail_on_unknown_properties: bool = True,
    ) -> None:
        """Create a new document handler.

        Parameters
        ----------
        model_class: Type, optional
            Root dataclass for the SCXML schema.
        schema_path: str | None, optional
            Optional path to an XML Schema document for validation.
        pretty: bool, optional
            Pretty-print output when serialising.
        omit_empty: bool, optional
            Drop ``None`` or empty containers from JSON output.
        fail_on_unknown_properties: bool, optional
            When ``True`` (default) unexpected XML elements raise an exception
            during parsing.  Set ``False`` to ignore them.

        Returns
        -------
        None
        """
        self.model_class = model_class
        self.schema_path = schema_path
        self.parser = XmlParser(
            config=ParserConfig(fail_on_unknown_properties=fail_on_unknown_properties)
        )
        self.serializer = XmlSerializer(
            config=SerializerConfig(
                pretty_print=pretty, encoding="utf-8", xml_declaration=True
            )
        )
        self.schema = xmlschema.XMLSchema(schema_path) if schema_path else None
        self.omit_empty = omit_empty

    @staticmethod
    def _resolve(cls: type) -> type:
        """Resolve forward references to actual classes."""
        if isinstance(cls, ForwardRef):
            return getattr(dataclasses_module, cls.__forward_arg__)
        if isinstance(cls, str):
            return getattr(dataclasses_module, cls)
        return cls

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
        """Convert SCXML string to canonical JSON.

        This method tolerates documents that omit the default SCXML namespace by
        inserting it prior to parsing.  Such files are technically invalid but
        appear in the W3C test suite.
        """
        try:
            root = ET.fromstring(xml_str)
        except Exception:
            # Let the parser raise a more descriptive error later
            root = None
        if root is not None and root.tag == "scxml" and "xmlns" not in root.attrib:
            root.attrib["xmlns"] = "http://www.w3.org/2005/07/scxml"
            xml_str = ET.tostring(root, encoding="unicode")
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
        cls = self._resolve(cls)
        origin = get_origin(cls)
        if origin is list:
            item_type = self._resolve(get_args(cls)[0])
            return [self._to_dataclass(item_type, x) for x in data]
        if origin is Union:
            for arg in get_args(cls):
                if arg is type(None):
                    continue
                try:
                    return self._to_dataclass(self._resolve(arg), data)
                except Exception:
                    pass
            return data
        if cls is object:
            if isinstance(data, dict) and "qname" in data:
                return AnyElement(
                    qname=data.get("qname"),
                    text=data.get("text"),
                    tail=data.get("tail"),
                    attributes=data.get("attributes", {}),
                    children=[
                        self._to_dataclass(object, c) if isinstance(c, dict) else c
                        for c in data.get("children", [])
                    ],
                )
            if isinstance(data, dict):
                try:
                    return self._to_dataclass(Scxml, data)
                except Exception:
                    pass
            if isinstance(data, list):
                return [self._to_dataclass(object, x) for x in data]
            return data
        if cls is object:
            if isinstance(data, dict) and "qname" in data:
                return AnyElement(
                    qname=data.get("qname"),
                    text=data.get("text"),
                    tail=data.get("tail"),
                    attributes=data.get("attributes", {}),
                    children=[
                        self._to_dataclass(object, c) if isinstance(c, dict) else c
                        for c in data.get("children", [])
                    ],
                )
            if isinstance(data, list):
                return [self._to_dataclass(object, x) for x in data]
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


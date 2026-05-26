"""
Agent Name: typed-other-attributes-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Focused tests for typed metadata in generated ``other_attributes`` fields.
"""

from typing import Any, get_type_hints

import pytest

import scjson.dataclasses as dataclass_models
import scjson.dataclasses_strict as strict_dataclass_models
import scjson.pydantic as pydantic_models
import scjson.pydantic_strict as strict_pydantic_models


@pytest.mark.parametrize(
    "model_cls",
    [
        pydantic_models.Data,
        strict_pydantic_models.Data,
    ],
)
def test_pydantic_other_attributes_accept_typed_metadata(model_cls):
    """Pydantic variants preserve integer and object extension metadata."""
    typed_metadata = {
        "priority": 7,
        "options": {"retry": True, "source": "fixture"},
    }

    data = model_cls(id="metadata", other_attributes=typed_metadata)

    assert data.other_attributes == typed_metadata


@pytest.mark.parametrize(
    "model_cls",
    [
        pydantic_models.Data,
        strict_pydantic_models.Data,
    ],
)
def test_pydantic_other_attributes_are_typed_as_any(model_cls):
    """Pydantic variants expose ``dict[str, Any]`` for metadata bags."""
    assert get_type_hints(model_cls)["other_attributes"] == dict[str, Any]


@pytest.mark.parametrize(
    "model_cls",
    [
        dataclass_models.Data,
        strict_dataclass_models.Data,
    ],
)
def test_dataclass_other_attributes_remain_string_typed(model_cls):
    """Dataclass variants intentionally retain XML attribute string typing."""
    assert get_type_hints(model_cls)["other_attributes"] == dict[str, str]

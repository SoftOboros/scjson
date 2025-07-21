"""
CaseStyle.py - A utility module for handling different case styles in text identifiers.

This module provides an enumeration of common case styles, conversion functions between
these styles, and validation utilities to check if a string conforms to a specific style.

Intended for use in Django and FastAPI projects under `core.utils`.

Features:
- Enum `CaseStyle` defining common case styles.
    - `convert(identifier: str, target_style: CaseStyle) -> str` for case conversion.
    - `validate_case_value(value: Union[str, int, CaseStyle]) -> bool` to check valid enum values.
    - `validate_case_string(identifier: str, case_style: CaseStyle) -> bool` to check format validity.
    - `get_validator(case_style: CaseStyle) -> Callable[[str], str]` for FastAPI/Pydantic validation.
    - `get_regex_validator(case_style: CaseStyle) -> str` for schema-level regex validation.
- regex `CASESTYLE_REGEX`: valudates strings as members of the set of CaseStyle names.
- class DynamicCaseStyleModel(BaseModel): A pydantic model to dynamically validate string case.

"""

from enum import Enum, auto
import re
from typing import Union, Callable
from pydantic import BaseModel, Field
from typing import Optional

class CaseStyle(Enum):
    """
    Enumeration of common case styles used in programming and text formatting.
    """
    CAMEL_CASE = auto()             # camelCase
    PASCAL_CASE = auto()            # PascalCase
    SNAKE_CASE = auto()             # snake_case
    SCREAMING_SNAKE_CASE = auto()   # SCREAMING_SNAKE_CASE
    KEBAB_CASE = auto()             # kebab-case (slug style, used in URLs)
    TRAIN_CASE = auto()             # Train-Case
    LOWERCASE = auto()              # lowercase (one-way conversion)
    ANY = auto()                    # Any single-word identifier

    @staticmethod
    def split_identifier(identifier: str) -> list:
        """
        Splits an identifier into words based on known case styles.

        Args:
            identifier (str): The identifier string to split.

        Returns:
            list: A list of words extracted from the identifier.
        """
        if '-' in identifier:
            return identifier.split('-')
        elif '_' in identifier:
            return identifier.split('_')
        elif re.search(r'[A-Z]', identifier[1:]):  # Detect camelCase/PascalCase
            return re.findall(r'[A-Z]?[a-z]+|\d+|[A-Z]+(?![a-z])', identifier)
        else:
            return [identifier]

    @classmethod
    def convert(cls, identifier: str, target_style: "CaseStyle") -> str:
        """
        Converts an identifier into the specified case style.

        Args:
            identifier (str): The input identifier to convert.
            target_style (CaseStyle): The target case style.

        Returns:
            str: The converted identifier in the specified case style.

        Raises:
            ValueError: If the target case style is not supported.
        """
        words = cls.split_identifier(identifier)

        match target_style:
            case cls.CAMEL_CASE:
                return words[0].lower() + ''.join(w.capitalize() for w in words[1:])
            case cls.PASCAL_CASE:
                return ''.join(w.capitalize() for w in words)
            case cls.SNAKE_CASE:
                return '_'.join(w.lower() for w in words)
            case cls.SCREAMING_SNAKE_CASE:
                return '_'.join(w.upper() for w in words)
            case cls.KEBAB_CASE:
                return '-'.join(w.lower() for w in words)  # Slug-style
            case cls.TRAIN_CASE:
                return '-'.join(w.capitalize() for w in words)
            case cls.LOWERCASE:
                return ''.join(words).lower()  # One-way conversion (no separator)
            case cls.ANY:
                if len(words) == 1:
                    return identifier  # Already a single-word identifier
                raise ValueError("ANY case requires a single, undelimited word")
            case _:
                raise ValueError(f"Unsupported target case style: {target_style}")

    @staticmethod
    def validate_case_value(value: Union[str, int, "CaseStyle"]) -> bool:
        """
        Validates whether the input is a valid CaseStyle enum (by name, integer, or enum instance).

        Args:
            value (Union[str, int, CaseStyle]): The value to validate.

        Returns:
            bool: True if the value is a valid CaseStyle enum, else raises an error.

        Raises:
            ValueError: If the value is an invalid CaseStyle name or number.
            TypeError: If the value is not a recognized type.
        """
        if isinstance(value, CaseStyle):
            return True
        elif isinstance(value, str):
            try:
                CaseStyle[value.upper().replace('-', '_')]  # Normalize name
                return True
            except KeyError:
                raise ValueError(f"Invalid CaseStyle string: {value}")
        elif isinstance(value, int):
            if value in {e.value for e in CaseStyle}:
                return True
            else:
                raise ValueError(f"Invalid CaseStyle numeric value: {value}")
        else:
            raise TypeError("CaseStyle must be validated using a string, enum, or numeric value.")

    @classmethod
    def get_regex_validator(cls, case_style: "CaseStyle") -> str:
        """
        Returns a regex pattern string for validating the given case style.
        This allows FastAPI/Pydantic to enforce case rules at the schema level.

        Args:
            case_style (CaseStyle): The case style to enforce.

        Returns:
            str: A regex pattern for the specified case style.

        Raises:
            ValueError: If an unsupported case style is provided.
        """
        match case_style:
            case cls.CAMEL_CASE:
                return r'^[a-z]+(?:[A-Z][a-z\d]*)*$'  # e.g., myVariableName
            case cls.PASCAL_CASE:
                return r'^[A-Z][a-z\d]*(?:[A-Z][a-z\d]*)*$'  # e.g., MyVariableName
            case cls.SNAKE_CASE:
                return r'^[a-z\d]+(?:_[a-z\d]+)*$'  # e.g., my_variable_name
            case cls.SCREAMING_SNAKE_CASE:
                return r'^[A-Z\d]+(?:_[A-Z\d]+)*$'  # e.g., MY_VARIABLE_NAME
            case cls.KEBAB_CASE:
                return r'^[a-z\d]+(?:-[a-z\d]+)*$'  # e.g., my-variable-name
            case cls.TRAIN_CASE:
                return r'^[A-Z][a-z\d]*(?:-[A-Z][a-z\d]*)*$'  # e.g., My-Variable-Name
            case cls.LOWERCASE:
                return r'^[a-z\d]+$'  # e.g., myvariablename
            case cls.ANY:
                return r'^[a-zA-Z\d]+$'  # e.g., simpleword
            case _:
                raise ValueError(f"Unsupported case style: {case_style}")
    
    @classmethod
    def validate_case_string(cls, identifier: str, case_style: "CaseStyle") -> bool:
        """
        Checks if the given identifier conforms to a specific case style.

        Args:
            identifier (str): The identifier to validate.
            case_style (CaseStyle): The case style to check against.

        Returns:
            bool: True if the identifier matches the given case style, False otherwise.

        Raises:
            ValueError: If an unsupported case style is provided.
        """
        regex_pattern = cls.get_regex_validator(case_style)  # Get the regex for the case style
        return bool(re.fullmatch(regex_pattern, identifier))  # Validate against the regex

    @classmethod
    def get_validator(cls, case_style: "CaseStyle") -> Callable[[str], str]:
        """
        Returns a FastAPI/Pydantic validator function that checks if a string conforms
        to the specified case style.

        Args:
            case_style (CaseStyle): The case style to enforce.

        Returns:
            Callable[[str], str]: A validation function for Pydantic.

        Raises:
            ValueError: If an unsupported case style is provided.
        """
        def validator(value: str) -> str:
            if not cls.validate_case_string(value, case_style):
                raise ValueError(f"String '{value}' does not conform to {case_style.name}")
            return value

        return validator

def to_camel(s: str) -> str:
    return CaseStyle.ANY.convert(s, CaseStyle.CAMEL_CASE)

def to_pascal(s: str) -> str:
    return CaseStyle.ANY.convert(s, CaseStyle.PASCAL_CASE)

def to_snake(s: str) -> str:
    return CaseStyle.ANY.convert(s, CaseStyle.SNAKE_CASE)

def to_scream(s: str) -> str:
    return CaseStyle.ANY.convert(s, CaseStyle.SCREAMING_SNAKE_CASE)

def to_kebab(s: str) -> str:
    return CaseStyle.ANY.convert(s, CaseStyle.KEBAB_CASE)

def to_train(s: str) -> str:
    return CaseStyle.ANY.convert(s, CaseStyle.TRAIN_CASE)

# Generate regex dynamically from enum names
CASESTYLE_REGEX = r'^(' + '|'.join(CaseStyle.__members__.keys()) + r')$'

class DynamicCaseStyleModel(BaseModel):
    """FastAPI model with dynamic case validation based on user preferences."""

    case_preference: Optional[CaseStyle] = None  # This can be set dynamically
    value: str = Field(..., pattern="")  # Placeholder, validated in ``__init__``

    def __init__(self, **data):
        super().__init__(**data)

        if self.case_preference:
            regex_pattern = CaseStyle.get_regex_validator(self.case_preference)
            if not re.fullmatch(regex_pattern, self.value):
                raise ValueError(
                    f"value '{self.value}' does not conform to {self.case_preference.name}"
                )

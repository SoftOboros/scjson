"""
Decode character data in SCXML datamodel declarations for execution.

Agent Name: python-datamodel

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

import json


def _reject_constant(token):
    raise ValueError(f"{token} is not a JSON literal")


def inline_data_value(content):
    """Read inline character data without evaluating an expression.

    :param content: Ordered character-data parts of a data declaration.
    :returns: The decoded JSON value or the original text for non-JSON input.
    """
    text = "".join(content)
    try:
        return json.loads(text, parse_constant=_reject_constant)
    except ValueError:
        return text

# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# ------------------------------------------------------------------------------

"""Dictionary front end for keyso.

This module contains the public conversion functions from the dictionary syntax
to the semantic configuration-space model.  Syntax-level constructs such as
``_literal`` and ``_nested`` are handled here and are not part of the public data
model.
"""

from __future__ import annotations

import collections.abc
import functools
import typing

from keyso import constants
from keyso.errors import DictionaryError, ReservedKeywordError
from keyso.model import Configuration, ConfigurationSpace

Dictionary = dict[str, object]
NormalizedDictionary = dict[str, list[dict[str, object]]]


def from_dictionary(dictionary: Dictionary) -> ConfigurationSpace:
    """Build a :class:`ConfigurationSpace` from a keyso dictionary.

    The input must be a Python dictionary using the keyso dictionary syntax.
    The returned object is a semantic configuration space, not a syntax tree.
    """

    _require_mapping(dictionary, "keyso input")
    if len(dictionary) != 1:
        raise DictionaryError(
            "A keyso dictionary must contain exactly one construct. "
            "Use '_product' to combine independent keys."
        )

    key, value = next(iter(dictionary.items()))
    if not isinstance(key, str):
        raise DictionaryError(f"Dictionary keys must be strings, got {key!r}")

    if key in constants.EXPRESSION_KEYWORDS:
        return _from_operator(key, value)

    if key in constants.VALUE_KEYWORDS:
        raise DictionaryError(f"{key!r} is only valid in value position")

    if key in constants.KEYWORDS:
        raise ReservedKeywordError(f"Unknown reserved keyword in expression position: {key!r}")

    return _from_key_value(key, value)


def expand(dictionary: Dictionary) -> list[dict[str, object]]:
    """Expand a keyso dictionary into a list of plain Python dictionaries."""

    return from_dictionary(dictionary).to_dicts()


def normalize(dictionary: Dictionary) -> NormalizedDictionary:
    """Return the normalized ``{"_set": ...}`` representation."""

    return {constants.KEYWORD_SET: expand(dictionary)}


def _from_operator(key: str, value: object) -> ConfigurationSpace:
    if key == constants.KEYWORD_SET:
        return _from_set(value)

    if key == constants.KEYWORD_PRODUCT:
        return _from_product(value)

    if key == constants.KEYWORD_UNION:
        return _from_union(value)

    if key == constants.KEYWORD_INTERSECTION:
        return _from_intersection(value)

    if key == constants.KEYWORD_DIFFERENCE:
        return _from_difference(value)

    raise AssertionError(f"Unhandled keyso operator: {key!r}")


def _from_key_value(key: str, value: object) -> ConfigurationSpace:
    values = _expand_value(value)
    return ConfigurationSpace.from_mappings(({key: item} for item in values), configuration_type={key})


def _from_set(value: object) -> ConfigurationSpace:
    if not isinstance(value, list):
        raise DictionaryError("'_set' must map to a list of concrete configurations")

    configurations: list[Configuration] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise DictionaryError(f"'_set' item {index} must be a dictionary")

        concrete: dict[str, object] = {}
        for key, item_value in item.items():
            if not isinstance(key, str):
                raise DictionaryError(f"'_set' configuration key must be a string, got {key!r}")
            if key in constants.KEYWORDS:
                raise ReservedKeywordError(
                    f"Reserved keyword cannot be used as a configuration key: {key!r}"
                )
            concrete[key] = _unwrap_concrete_value(item_value)

        configurations.append(Configuration.from_mapping(concrete))

    configuration_type = None
    if configurations:
        configuration_type = configurations[0].configuration_type

    return ConfigurationSpace(configurations, configuration_type=configuration_type)


def _from_product(value: object) -> ConfigurationSpace:
    operands = _read_operand_list(value, constants.KEYWORD_PRODUCT)
    return functools.reduce(lambda left, right: left.product(right), operands)


def _from_union(value: object) -> ConfigurationSpace:
    operands = _read_operand_list(value, constants.KEYWORD_UNION)
    return functools.reduce(lambda left, right: left.union(right), operands)


def _from_intersection(value: object) -> ConfigurationSpace:
    operands = _read_operand_list(value, constants.KEYWORD_INTERSECTION)
    return functools.reduce(lambda left, right: left.intersection(right), operands)


def _from_difference(value: object) -> ConfigurationSpace:
    if not isinstance(value, dict):
        raise DictionaryError("'_difference' must map to a dictionary")

    expected = {constants.KEYWORD_MINUEND, constants.KEYWORD_SUBTRAHEND}
    actual = set(value.keys())
    if actual != expected:
        raise DictionaryError(
            "'_difference' must contain exactly '_minuend' and '_subtrahend'"
        )

    minuend = value[constants.KEYWORD_MINUEND]
    subtrahend = value[constants.KEYWORD_SUBTRAHEND]

    _require_mapping(minuend, "'_difference._minuend'")
    _require_mapping(subtrahend, "'_difference._subtrahend'")

    return from_dictionary(typing.cast(Dictionary, minuend)).difference(
        from_dictionary(typing.cast(Dictionary, subtrahend))
    )


def _read_operand_list(value: object, operator: str) -> tuple[ConfigurationSpace, ...]:
    if not isinstance(value, list):
        raise DictionaryError(f"'{operator}' must map to a non-empty list")

    if not value:
        raise DictionaryError(f"'{operator}' must contain at least one operand")

    spaces: list[ConfigurationSpace] = []
    for index, item in enumerate(value):
        _require_mapping(item, f"'{operator}' operand {index}")
        spaces.append(from_dictionary(typing.cast(Dictionary, item)))

    return tuple(spaces)


def _expand_value(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return _expand_value_dictionary(value)

    if isinstance(value, list):
        values: list[object] = []
        for item in value:
            values.extend(_expand_list_item(item))
        return tuple(values)

    return (value,)


def _expand_list_item(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return _expand_value_dictionary(value)
    return (value,)


def _expand_value_dictionary(dictionary: dict[object, object]) -> tuple[object, ...]:
    if len(dictionary) != 1:
        raise DictionaryError(
            "Plain dictionaries are ambiguous in value position. "
            "Use {'_literal': ...} for data or {'_nested': ...} for nested keyso."
        )

    key, value = next(iter(dictionary.items()))
    if key == constants.KEYWORD_LITERAL:
        return (value,)

    if key == constants.KEYWORD_NESTED:
        _require_mapping(value, "'_nested' value")
        return tuple(
            configuration.to_dict()
            for configuration in from_dictionary(typing.cast(Dictionary, value))
        )

    raise DictionaryError(
        "Plain dictionaries are ambiguous in value position. "
        "Use {'_literal': ...} for data or {'_nested': ...} for nested keyso."
    )


def _unwrap_concrete_value(value: object) -> object:
    """Unwrap value directives inside concrete ``_set`` configurations.

    ``_set`` is already a concrete configuration-space representation, so plain
    dictionaries are treated as data there.  A single ``{'_literal': value}`` may
    still be used to disambiguate data copied from non-normalized input.
    """

    if isinstance(value, dict) and set(value.keys()) == {constants.KEYWORD_LITERAL}:
        return value[constants.KEYWORD_LITERAL]

    return value


def _require_mapping(value: object, name: str) -> None:
    if not isinstance(value, dict):
        raise DictionaryError(f"{name} must be a dictionary")

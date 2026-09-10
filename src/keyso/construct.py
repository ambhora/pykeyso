# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# ------------------------------------------------------------------------------

"""Constructors for the keyso dictionary front end.

The top-level :mod:`keyso` namespace exposes the semantic model:
configuration types, configurations, and configuration spaces.  This module is a
separate constructor namespace for building dictionary-form keyso inputs
programmatically.

The constructor classes are syntax helpers, not the semantic model.  Convert them
to plain dictionaries with :meth:`to_dictionary`, or pass them to
:func:`evaluate` in this namespace.
"""

from __future__ import annotations

import dataclasses
import typing

from keyso import constants
from keyso.model import ConfigurationSpace

Dictionary = dict[str, object]
Constructable: typing.TypeAlias = typing.Union[Dictionary, "DictionaryConstructor"]


class DictionaryConstructor(typing.Protocol):
    """Protocol implemented by objects that can produce keyso dictionaries."""

    def to_dictionary(self) -> Dictionary:
        """Return the keyso dictionary represented by this constructor."""


def _to_dictionary(value: Constructable) -> Dictionary:
    if hasattr(value, "to_dictionary"):
        return typing.cast(DictionaryConstructor, value).to_dictionary()

    if isinstance(value, dict):
        return value

    raise TypeError(f"Expected a keyso dictionary constructor or dictionary, got {value!r}")


@dataclasses.dataclass(frozen=True, slots=True)
class Literal:
    """Construct a value-position ``_literal`` dictionary."""

    value: object

    def to_dictionary(self) -> Dictionary:
        return {constants.KEYWORD_LITERAL: self.value}


@dataclasses.dataclass(frozen=True, slots=True)
class Nested:
    """Construct a value-position ``_nested`` dictionary."""

    value: Constructable

    def to_dictionary(self) -> Dictionary:
        return {constants.KEYWORD_NESTED: _to_dictionary(self.value)}


@dataclasses.dataclass(frozen=True, slots=True)
class Interval:
    """Construct a value-position ``_interval`` dictionary.

    ``stop`` is inclusive.  ``step`` must be a positive integer.
    """

    start: int
    stop: int
    step: int = 1

    def to_dictionary(self) -> Dictionary:
        return {
            constants.KEYWORD_INTERVAL: {
                "start": self.start,
                "stop": self.stop,
                "step": self.step,
            }
        }


@dataclasses.dataclass(frozen=True, slots=True)
class Set:
    """Construct an ``_set`` dictionary from concrete configurations."""

    configurations: tuple[Dictionary, ...]

    def __init__(self, *configurations: Dictionary) -> None:
        object.__setattr__(self, "configurations", tuple(configurations))

    def to_dictionary(self) -> Dictionary:
        return {constants.KEYWORD_SET: [dict(configuration) for configuration in self.configurations]}


@dataclasses.dataclass(frozen=True, slots=True)
class Product:
    """Construct a ``_product`` dictionary."""

    operands: tuple[Constructable, ...]

    def __init__(self, *operands: Constructable) -> None:
        object.__setattr__(self, "operands", tuple(operands))

    def to_dictionary(self) -> Dictionary:
        return {constants.KEYWORD_PRODUCT: [_to_dictionary(operand) for operand in self.operands]}


@dataclasses.dataclass(frozen=True, slots=True)
class Union:
    """Construct a ``_union`` dictionary."""

    operands: tuple[Constructable, ...]

    def __init__(self, *operands: Constructable) -> None:
        object.__setattr__(self, "operands", tuple(operands))

    def to_dictionary(self) -> Dictionary:
        return {constants.KEYWORD_UNION: [_to_dictionary(operand) for operand in self.operands]}


@dataclasses.dataclass(frozen=True, slots=True)
class Intersection:
    """Construct an ``_intersection`` dictionary."""

    operands: tuple[Constructable, ...]

    def __init__(self, *operands: Constructable) -> None:
        object.__setattr__(self, "operands", tuple(operands))

    def to_dictionary(self) -> Dictionary:
        return {constants.KEYWORD_INTERSECTION: [_to_dictionary(operand) for operand in self.operands]}


@dataclasses.dataclass(frozen=True, slots=True)
class Difference:
    """Construct a ``_difference`` dictionary."""

    minuend: Constructable
    subtrahend: Constructable

    def to_dictionary(self) -> Dictionary:
        return {
            constants.KEYWORD_DIFFERENCE: {
                constants.KEYWORD_MINUEND: _to_dictionary(self.minuend),
                constants.KEYWORD_SUBTRAHEND: _to_dictionary(self.subtrahend),
            }
        }


def literal(value: object) -> Dictionary:
    """Return ``{"_literal": value}``."""

    return Literal(value).to_dictionary()


def nested(value: Constructable) -> Dictionary:
    """Return ``{"_nested": dictionary}``."""

    return Nested(value).to_dictionary()


def interval(start: int, stop: int, step: int = 1) -> Dictionary:
    """Return an inclusive integer ``_interval`` dictionary."""

    return Interval(start, stop, step).to_dictionary()


def set_(*configurations: Dictionary) -> Dictionary:
    """Return an ``_set`` dictionary."""

    return Set(*configurations).to_dictionary()


def product(*operands: Constructable) -> Dictionary:
    """Return a ``_product`` dictionary."""

    return Product(*operands).to_dictionary()


def union(*operands: Constructable) -> Dictionary:
    """Return a ``_union`` dictionary."""

    return Union(*operands).to_dictionary()


def intersection(*operands: Constructable) -> Dictionary:
    """Return an ``_intersection`` dictionary."""

    return Intersection(*operands).to_dictionary()


def difference(minuend: Constructable, subtrahend: Constructable) -> Dictionary:
    """Return a ``_difference`` dictionary."""

    return Difference(minuend, subtrahend).to_dictionary()


def evaluate(value: Constructable) -> ConfigurationSpace:
    """Evaluate a dictionary constructor or dictionary into a configuration space.

    This function intentionally lives in the constructor namespace.  The preferred
    top-level semantic entry point remains :func:`keyso.from_dictionary`.
    """

    from keyso.dictionary import from_dictionary

    return from_dictionary(_to_dictionary(value))


__all__ = [
    "Set",
    "Constructable",
    "Dictionary",
    "DictionaryConstructor",
    "Difference",
    "Intersection",
    "Interval",
    "Literal",
    "Nested",
    "Product",
    "Union",
    "set_",
    "difference",
    "evaluate",
    "interval",
    "intersection",
    "literal",
    "nested",
    "product",
    "union",
]

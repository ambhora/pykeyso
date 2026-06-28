# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# ------------------------------------------------------------------------------

"""Private helpers for structural hashing of configuration values."""

from __future__ import annotations

import dataclasses
import typing


@dataclasses.dataclass(frozen=True, slots=True)
class _FrozenDict:
    items: tuple[tuple[typing.Hashable, typing.Hashable], ...]


@dataclasses.dataclass(frozen=True, slots=True)
class _FrozenList:
    items: tuple[typing.Hashable, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class _FrozenTuple:
    items: tuple[typing.Hashable, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class _FrozenSet:
    items: frozenset[typing.Hashable]


FrozenValue = typing.Hashable


def freeze_value(value: object) -> FrozenValue:
    """Return a hashable structural representation of *value*.

    The public API returns normal Python values.  Internally, configurations must
    be hashable so they can be members of a finite set.  This function therefore
    freezes common container values recursively while preserving enough
    information to reconstruct them with :func:`thaw_value`.
    """

    if isinstance(value, dict):
        items = tuple(
            sorted(
                ((freeze_value(key), freeze_value(item_value)) for key, item_value in value.items()),
                key=lambda item: repr(item[0]),
            )
        )
        return _FrozenDict(items)

    if isinstance(value, list):
        return _FrozenList(tuple(freeze_value(item) for item in value))

    if isinstance(value, tuple):
        return _FrozenTuple(tuple(freeze_value(item) for item in value))

    if isinstance(value, set):
        return _FrozenSet(frozenset(freeze_value(item) for item in value))

    try:
        hash(value)
    except TypeError as error:
        raise TypeError(f"Value is not structurally freezeable: {value!r}") from error

    return typing.cast(FrozenValue, value)


def thaw_value(value: FrozenValue) -> object:
    """Reconstruct a public Python value from a frozen value."""

    if isinstance(value, _FrozenDict):
        return {thaw_value(key): thaw_value(item_value) for key, item_value in value.items}

    if isinstance(value, _FrozenList):
        return [thaw_value(item) for item in value.items]

    if isinstance(value, _FrozenTuple):
        return tuple(thaw_value(item) for item in value.items)

    if isinstance(value, _FrozenSet):
        return {thaw_value(item) for item in value.items}

    return value

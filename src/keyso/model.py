# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# ------------------------------------------------------------------------------

"""Public semantic data types for keyso.

The dictionary syntax is only a front end.  The public model is the algebraic
model: configuration types, configurations, and configuration spaces.
"""

from __future__ import annotations

import collections.abc
import dataclasses
import typing

from keyso import constants
from keyso._freeze import FrozenValue, freeze_value, thaw_value
from keyso.errors import CoherenceError, ConfigurationError, ReservedKeywordError


@dataclasses.dataclass(frozen=True, slots=True)
class ConfigurationType:
    """The set of keys present in a configuration."""

    keys: frozenset[str] = dataclasses.field(default_factory=frozenset)

    def __post_init__(self) -> None:
        keys = frozenset(self.keys)
        for key in keys:
            _validate_key(key)
        object.__setattr__(self, "keys", keys)

    def __contains__(self, key: object) -> bool:
        return key in self.keys

    def __iter__(self) -> collections.abc.Iterator[str]:
        return iter(sorted(self.keys))

    def __len__(self) -> int:
        return len(self.keys)

    def is_disjoint_with(self, other: ConfigurationType) -> bool:
        """Return whether this type and *other* have no common keys."""

        return self.keys.isdisjoint(other.keys)

    def union(self, other: ConfigurationType) -> ConfigurationType:
        """Return the union of two configuration types."""

        return ConfigurationType(self.keys | other.keys)

    def intersection(self, other: ConfigurationType) -> ConfigurationType:
        """Return the intersection of two configuration types."""

        return ConfigurationType(self.keys & other.keys)

    def to_set(self) -> set[str]:
        """Return this configuration type as a mutable set of strings."""

        return set(self.keys)


@dataclasses.dataclass(frozen=True, slots=True, init=False)
class Configuration:
    """A single configuration, represented by a finite mapping of keys to values."""

    _items: tuple[tuple[str, FrozenValue], ...]

    def __init__(
        self,
        values: collections.abc.Mapping[str, object]
        | collections.abc.Iterable[tuple[str, object]]
        | None = None,
    ) -> None:
        if values is None:
            raw_items: list[tuple[str, object]] = []
        elif isinstance(values, collections.abc.Mapping):
            raw_items = list(values.items())
        else:
            raw_items = list(values)

        seen: set[str] = set()
        frozen_items: list[tuple[str, FrozenValue]] = []

        for key, value in raw_items:
            _validate_key(key)
            if key in seen:
                raise ConfigurationError(f"Duplicate configuration key: {key!r}")
            seen.add(key)
            frozen_items.append((key, freeze_value(value)))

        object.__setattr__(self, "_items", tuple(sorted(frozen_items, key=lambda item: item[0])))

    @classmethod
    def from_mapping(cls, mapping: collections.abc.Mapping[str, object]) -> Configuration:
        """Create a configuration from a mapping."""

        return cls(mapping)

    @property
    def configuration_type(self) -> ConfigurationType:
        """Return the configuration type, i.e. the set of keys."""

        return ConfigurationType(frozenset(key for key, _ in self._items))

    @property
    def type(self) -> ConfigurationType:
        """Alias for :attr:`configuration_type`."""

        return self.configuration_type

    def __contains__(self, key: object) -> bool:
        return any(item_key == key for item_key, _ in self._items)

    def __iter__(self) -> collections.abc.Iterator[str]:
        return iter(key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, key: str) -> object:
        for item_key, value in self._items:
            if item_key == key:
                return thaw_value(value)
        raise KeyError(key)

    def items(self) -> tuple[tuple[str, object], ...]:
        """Return the configuration items with public Python values."""

        return tuple((key, thaw_value(value)) for key, value in self._items)

    def keys(self) -> tuple[str, ...]:
        """Return the configuration keys in deterministic order."""

        return tuple(key for key, _ in self._items)

    def values(self) -> tuple[object, ...]:
        """Return the configuration values in deterministic key order."""

        return tuple(thaw_value(value) for _, value in self._items)

    def to_dict(self) -> dict[str, object]:
        """Return this configuration as a plain Python dictionary."""

        return {key: thaw_value(value) for key, value in self._items}

    def merge(self, other: Configuration) -> Configuration:
        """Merge two configurations with disjoint types."""

        if not self.configuration_type.is_disjoint_with(other.configuration_type):
            overlap = self.configuration_type.keys & other.configuration_type.keys
            raise CoherenceError(
                f"Cannot merge configurations with overlapping keys: {sorted(overlap)!r}"
            )

        return Configuration(tuple((*self.items(), *other.items())))


@dataclasses.dataclass(frozen=True, slots=True, init=False)
class ConfigurationSpace:
    """A finite homogeneous set of configurations."""

    _configuration_type: ConfigurationType
    _configurations: frozenset[Configuration]

    def __init__(
        self,
        configurations: collections.abc.Iterable[Configuration] | None = None,
        configuration_type: ConfigurationType | collections.abc.Iterable[str] | None = None,
    ) -> None:
        config_set = frozenset(configurations or ())

        if configuration_type is None:
            resolved_type = _derive_configuration_type(config_set)
        elif isinstance(configuration_type, ConfigurationType):
            resolved_type = configuration_type
        else:
            resolved_type = ConfigurationType(frozenset(configuration_type))

        for configuration in config_set:
            if configuration.configuration_type != resolved_type:
                raise ConfigurationError(
                    "ConfigurationSpace must contain only configurations of its declared type"
                )

        object.__setattr__(self, "_configuration_type", resolved_type)
        object.__setattr__(self, "_configurations", config_set)

    @classmethod
    def empty(
        cls, configuration_type: ConfigurationType | collections.abc.Iterable[str] | None = None
    ) -> ConfigurationSpace:
        """Return an empty configuration space, preserving the supplied type."""

        return cls((), configuration_type=configuration_type)

    @classmethod
    def singleton(cls, configuration: Configuration) -> ConfigurationSpace:
        """Return a configuration space containing one configuration."""

        return cls((configuration,), configuration_type=configuration.configuration_type)

    @classmethod
    def from_mappings(
        cls,
        mappings: collections.abc.Iterable[collections.abc.Mapping[str, object]],
        configuration_type: ConfigurationType | collections.abc.Iterable[str] | None = None,
    ) -> ConfigurationSpace:
        """Create a configuration space from plain Python mappings."""

        return cls((Configuration.from_mapping(mapping) for mapping in mappings), configuration_type)

    @property
    def configuration_type(self) -> ConfigurationType:
        """Return the homogeneous type of this configuration space."""

        return self._configuration_type

    @property
    def type(self) -> ConfigurationType:
        """Alias for :attr:`configuration_type`."""

        return self.configuration_type

    @property
    def configurations(self) -> frozenset[Configuration]:
        """Return the configurations in this space."""

        return self._configurations

    def __contains__(self, configuration: object) -> bool:
        return configuration in self._configurations

    def __iter__(self) -> collections.abc.Iterator[Configuration]:
        return iter(sorted(self._configurations, key=lambda configuration: repr(configuration.to_dict())))

    def __len__(self) -> int:
        return len(self._configurations)

    def union(self, other: ConfigurationSpace) -> ConfigurationSpace:
        """Return the set union with another coherent configuration space."""

        self._require_same_type(other, "union")
        return ConfigurationSpace(
            self._configurations | other._configurations,
            configuration_type=self.configuration_type,
        )

    def intersection(self, other: ConfigurationSpace) -> ConfigurationSpace:
        """Return the set intersection with another coherent configuration space."""

        self._require_same_type(other, "intersection")
        return ConfigurationSpace(
            self._configurations & other._configurations,
            configuration_type=self.configuration_type,
        )

    def difference(self, other: ConfigurationSpace) -> ConfigurationSpace:
        """Return the set difference with another coherent configuration space."""

        self._require_same_type(other, "difference")
        return ConfigurationSpace(
            self._configurations - other._configurations,
            configuration_type=self.configuration_type,
        )

    def product(self, other: ConfigurationSpace) -> ConfigurationSpace:
        """Return the Cartesian product with another anticoherent configuration space."""

        if not self.configuration_type.is_disjoint_with(other.configuration_type):
            overlap = self.configuration_type.keys & other.configuration_type.keys
            raise CoherenceError(
                f"product requires disjoint configuration types; overlap: {sorted(overlap)!r}"
            )

        result_type = self.configuration_type.union(other.configuration_type)
        configurations = frozenset(
            left.merge(right) for left in self._configurations for right in other._configurations
        )
        return ConfigurationSpace(configurations, configuration_type=result_type)

    def to_dicts(self) -> list[dict[str, object]]:
        """Return configurations as a deterministic list of plain dictionaries."""

        return [configuration.to_dict() for configuration in self]

    def _require_same_type(self, other: ConfigurationSpace, operation: str) -> None:
        if self.configuration_type != other.configuration_type:
            raise CoherenceError(
                f"{operation} requires equal configuration types; "
                f"got {sorted(self.configuration_type.keys)!r} and "
                f"{sorted(other.configuration_type.keys)!r}"
            )


def _validate_key(key: object) -> None:
    if not isinstance(key, str):
        raise ConfigurationError(f"Configuration keys must be strings, got {key!r}")

    if key in constants.KEYWORDS:
        raise ReservedKeywordError(f"Reserved keyword cannot be used as a key: {key!r}")


def _derive_configuration_type(configurations: frozenset[Configuration]) -> ConfigurationType:
    if not configurations:
        return ConfigurationType()

    types = {configuration.configuration_type for configuration in configurations}
    if len(types) != 1:
        raise ConfigurationError(
            "ConfigurationSpace must contain configurations of exactly one type"
        )

    return next(iter(types))

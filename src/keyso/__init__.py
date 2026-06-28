# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# ------------------------------------------------------------------------------

"""keyso: dictionary-based configuration spaces."""

from keyso import construct as construct
from keyso.dictionary import expand, from_dictionary, normalize
from keyso.errors import (
    CoherenceError,
    ConfigurationError,
    DictionaryError,
    KeysoError,
    ReservedKeywordError,
)
from keyso.metadata import __version__
from keyso.model import Configuration, ConfigurationSpace, ConfigurationType

__all__ = [
    "CoherenceError",
    "Configuration",
    "ConfigurationError",
    "ConfigurationSpace",
    "ConfigurationType",
    "DictionaryError",
    "KeysoError",
    "ReservedKeywordError",
    "__version__",
    "construct",
    "expand",
    "from_dictionary",
    "normalize",
]

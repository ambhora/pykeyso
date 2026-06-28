# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# ------------------------------------------------------------------------------

"""Exception hierarchy for keyso."""


class KeysoError(Exception):
    """Base class for all keyso errors."""


class DictionaryError(KeysoError):
    """Raised when an input dictionary is not a valid keyso dictionary."""


class ReservedKeywordError(DictionaryError):
    """Raised when a reserved keyword is used as a configuration key."""


class ConfigurationError(KeysoError):
    """Raised when a configuration object is invalid."""


class CoherenceError(KeysoError):
    """Raised when a set operation is applied to incompatible configuration spaces."""

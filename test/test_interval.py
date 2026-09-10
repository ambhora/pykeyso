# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# ------------------------------------------------------------------------------

"""Tests for the ``_interval`` value-position construct."""

import pytest

import keyso


def test_interval_default_step() -> None:
    assert keyso.expand(
        {"cores": {"_interval": {"start": 16, "stop": 20}}}
    ) == [
        {"cores": 16},
        {"cores": 17},
        {"cores": 18},
        {"cores": 19},
        {"cores": 20},
    ]


def test_interval_explicit_step_and_inclusive_stop() -> None:
    assert keyso.expand(
        {"cores": {"_interval": {"start": 16, "stop": 32, "step": 8}}}
    ) == [
        {"cores": 16},
        {"cores": 24},
        {"cores": 32},
    ]


def test_interval_stop_need_not_lie_on_step() -> None:
    assert keyso.expand(
        {"cores": {"_interval": {"start": 16, "stop": 31, "step": 8}}}
    ) == [
        {"cores": 16},
        {"cores": 24},
    ]


def test_interval_single_value() -> None:
    assert keyso.expand(
        {"cores": {"_interval": {"start": 16, "stop": 16}}}
    ) == [{"cores": 16}]


def test_interval_can_appear_in_multivalue_list() -> None:
    assert keyso.expand(
        {
            "cores": [
                8,
                {"_interval": {"start": 16, "stop": 32, "step": 8}},
            ]
        }
    ) == [
        {"cores": 16},
        {"cores": 24},
        {"cores": 32},
        {"cores": 8},
    ]


def test_interval_can_participate_in_product() -> None:
    assert keyso.expand(
        {
            "_product": [
                {"nodes": [1, 2]},
                {"cores": {"_interval": {"start": 16, "stop": 32, "step": 16}}},
            ]
        }
    ) == [
        {"cores": 16, "nodes": 1},
        {"cores": 16, "nodes": 2},
        {"cores": 32, "nodes": 1},
        {"cores": 32, "nodes": 2},
    ]


def test_interval_constructor_class() -> None:
    dictionary = keyso.construct.Interval(16, 32, 8).to_dictionary()

    assert dictionary == {
        "_interval": {
            "start": 16,
            "stop": 32,
            "step": 8,
        }
    }
    assert keyso.expand({"cores": dictionary}) == [
        {"cores": 16},
        {"cores": 24},
        {"cores": 32},
    ]


def test_interval_constructor_helper() -> None:
    dictionary = keyso.construct.interval(16, 32, 8)

    assert dictionary == {
        "_interval": {
            "start": 16,
            "stop": 32,
            "step": 8,
        }
    }


def test_interval_is_value_position_only() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"_interval": {"start": 16, "stop": 32}})


@pytest.mark.parametrize(
    "value",
    [
        [],
        16,
        "16..32",
    ],
)
def test_interval_requires_dictionary(value: object) -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"cores": {"_interval": value}})


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"start": 16},
        {"stop": 32},
        {"start": 16, "stop": 32, "unknown": 1},
    ],
)
def test_interval_requires_exact_keys(value: dict[str, object]) -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"cores": {"_interval": value}})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("start", 16.0),
        ("start", True),
        ("stop", 32.0),
        ("stop", False),
        ("step", 1.0),
        ("step", True),
    ],
)
def test_interval_fields_must_be_integers(field: str, value: object) -> None:
    interval: dict[str, object] = {"start": 16, "stop": 32, "step": 1}
    interval[field] = value

    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"cores": {"_interval": interval}})


@pytest.mark.parametrize("step", [0, -1, -8])
def test_interval_step_must_be_positive(step: int) -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand(
            {"cores": {"_interval": {"start": 16, "stop": 32, "step": step}}}
        )


def test_interval_rejects_reversed_bounds() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"cores": {"_interval": {"start": 32, "stop": 16}}})

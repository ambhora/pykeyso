# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# ------------------------------------------------------------------------------

from __future__ import annotations

import pytest

import keyso


def test_public_api_exports_semantic_types_only() -> None:
    assert hasattr(keyso, "ConfigurationType")
    assert hasattr(keyso, "Configuration")
    assert hasattr(keyso, "ConfigurationSpace")
    assert hasattr(keyso, "from_dictionary")
    assert hasattr(keyso, "expand")
    assert hasattr(keyso, "normalize")
    assert not hasattr(keyso, "Nested")
    assert not hasattr(keyso, "Literal")
    assert not hasattr(keyso, "Product")
    assert not hasattr(keyso, "evaluate")


def test_configuration_type_validates_keys() -> None:
    configuration_type = keyso.ConfigurationType(frozenset({"b", "a"}))

    assert list(configuration_type) == ["a", "b"]
    assert configuration_type.to_set() == {"a", "b"}
    assert "a" in configuration_type
    assert len(configuration_type) == 2


@pytest.mark.parametrize("bad_key", [1, None, ("a",)])
def test_configuration_type_rejects_non_string_keys(bad_key: object) -> None:
    with pytest.raises(keyso.ConfigurationError):
        keyso.ConfigurationType(frozenset({bad_key}))  # type: ignore[arg-type]


def test_configuration_type_rejects_keywords() -> None:
    with pytest.raises(keyso.ReservedKeywordError):
        keyso.ConfigurationType(frozenset({"_product"}))


def test_configuration_type_operations() -> None:
    left = keyso.ConfigurationType(frozenset({"a"}))
    right = keyso.ConfigurationType(frozenset({"b"}))
    overlapping = keyso.ConfigurationType(frozenset({"a", "c"}))

    assert left.is_disjoint_with(right)
    assert not left.is_disjoint_with(overlapping)
    assert left.union(right).to_set() == {"a", "b"}
    assert left.intersection(overlapping).to_set() == {"a"}


def test_configuration_from_mapping() -> None:
    configuration = keyso.Configuration.from_mapping({"b": 2, "a": 1})

    assert configuration.configuration_type.to_set() == {"a", "b"}
    assert configuration.type == configuration.configuration_type
    assert configuration.to_dict() == {"a": 1, "b": 2}
    assert configuration["a"] == 1
    assert configuration.keys() == ("a", "b")
    assert configuration.values() == (1, 2)
    assert configuration.items() == (("a", 1), ("b", 2))
    assert "a" in configuration
    assert list(configuration) == ["a", "b"]
    assert len(configuration) == 2


def test_configuration_rejects_duplicate_keys_from_iterable() -> None:
    with pytest.raises(keyso.ConfigurationError):
        keyso.Configuration((("a", 1), ("a", 2)))


def test_configuration_getitem_missing_key() -> None:
    configuration = keyso.Configuration.from_mapping({"a": 1})

    with pytest.raises(KeyError):
        _ = configuration["b"]


def test_configuration_merge() -> None:
    left = keyso.Configuration.from_mapping({"a": 1})
    right = keyso.Configuration.from_mapping({"b": 2})

    assert left.merge(right).to_dict() == {"a": 1, "b": 2}


def test_configuration_merge_rejects_overlapping_keys() -> None:
    left = keyso.Configuration.from_mapping({"a": 1})
    right = keyso.Configuration.from_mapping({"a": 2})

    with pytest.raises(keyso.CoherenceError):
        left.merge(right)


def test_configuration_values_can_contain_nested_data() -> None:
    configuration = keyso.Configuration.from_mapping(
        {"params": {"a": [1, 2], "b": {"inner": True}}}
    )

    assert configuration.to_dict() == {"params": {"a": [1, 2], "b": {"inner": True}}}
    assert hash(configuration)


def test_configuration_space_derives_type() -> None:
    space = keyso.ConfigurationSpace.from_mappings([{"a": 1}, {"a": 2}])

    assert space.configuration_type.to_set() == {"a"}
    assert space.type == space.configuration_type
    assert len(space) == 2
    assert {tuple(item.items()) for item in space.to_dicts()} == {
        (("a", 1),),
        (("a", 2),),
    }


def test_configuration_space_preserves_empty_type() -> None:
    space = keyso.ConfigurationSpace.from_mappings([{"a": 1}])
    empty = space.difference(space)

    assert len(empty) == 0
    assert empty.configuration_type.to_set() == {"a"}


def test_configuration_space_rejects_mixed_types() -> None:
    with pytest.raises(keyso.ConfigurationError):
        keyso.ConfigurationSpace.from_mappings([{"a": 1}, {"b": 2}])


def test_configuration_space_rejects_wrong_declared_type() -> None:
    with pytest.raises(keyso.ConfigurationError):
        keyso.ConfigurationSpace.from_mappings([{"a": 1}], configuration_type={"b"})


def test_configuration_space_contains_and_iterates() -> None:
    configuration = keyso.Configuration.from_mapping({"a": 1})
    space = keyso.ConfigurationSpace.singleton(configuration)

    assert configuration in space
    assert list(space) == [configuration]


def test_configuration_space_empty_default_type() -> None:
    space = keyso.ConfigurationSpace.empty()

    assert len(space) == 0
    assert space.configuration_type.to_set() == set()


def test_configuration_space_product() -> None:
    left = keyso.ConfigurationSpace.from_mappings([{"a": 1}, {"a": 2}])
    right = keyso.ConfigurationSpace.from_mappings([{"b": 3}])

    assert left.product(right).to_dicts() == [
        {"a": 1, "b": 3},
        {"a": 2, "b": 3},
    ]


def test_configuration_space_product_of_empty_preserves_union_type() -> None:
    left = keyso.ConfigurationSpace.empty({"a"})
    right = keyso.ConfigurationSpace.from_mappings([{"b": 1}])

    result = left.product(right)

    assert result.to_dicts() == []
    assert result.configuration_type.to_set() == {"a", "b"}


def test_configuration_space_product_rejects_overlapping_types() -> None:
    left = keyso.ConfigurationSpace.from_mappings([{"a": 1}])
    right = keyso.ConfigurationSpace.from_mappings([{"a": 2}])

    with pytest.raises(keyso.CoherenceError):
        left.product(right)


def test_configuration_space_union_intersection_difference() -> None:
    left = keyso.ConfigurationSpace.from_mappings([{"a": 1}, {"a": 2}])
    right = keyso.ConfigurationSpace.from_mappings([{"a": 2}, {"a": 3}])

    assert left.union(right).to_dicts() == [{"a": 1}, {"a": 2}, {"a": 3}]
    assert left.intersection(right).to_dicts() == [{"a": 2}]
    assert left.difference(right).to_dicts() == [{"a": 1}]


@pytest.mark.parametrize("operation", ["union", "intersection", "difference"])
def test_configuration_space_set_operations_reject_incoherent_types(operation: str) -> None:
    left = keyso.ConfigurationSpace.from_mappings([{"a": 1}])
    right = keyso.ConfigurationSpace.from_mappings([{"b": 1}])

    with pytest.raises(keyso.CoherenceError):
        getattr(left, operation)(right)


def test_from_dictionary_key_value_pair() -> None:
    space = keyso.from_dictionary({"compiler": "gcc"})

    assert isinstance(space, keyso.ConfigurationSpace)
    assert space.to_dicts() == [{"compiler": "gcc"}]


def test_expand_key_multivalue_pair() -> None:
    assert keyso.expand({"compiler": ["gcc", "clang"]}) == [
        {"compiler": "clang"},
        {"compiler": "gcc"},
    ]


def test_expand_product_is_required_to_combine_keys() -> None:
    assert keyso.expand(
        {
            "_product": [
                {"compiler": ["gcc", "clang"]},
                {"optimization": ["O2", "O3"]},
            ]
        }
    ) == [
        {"compiler": "clang", "optimization": "O2"},
        {"compiler": "clang", "optimization": "O3"},
        {"compiler": "gcc", "optimization": "O2"},
        {"compiler": "gcc", "optimization": "O3"},
    ]

    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"compiler": ["gcc", "clang"], "optimization": ["O2", "O3"]})


def test_expand_union() -> None:
    assert keyso.expand({"_union": [{"compiler": "gcc"}, {"compiler": "clang"}]}) == [
        {"compiler": "clang"},
        {"compiler": "gcc"},
    ]


def test_expand_intersection() -> None:
    assert keyso.expand(
        {
            "_intersection": [
                {"compiler": ["gcc", "clang"]},
                {"compiler": ["gcc", "intel"]},
            ]
        }
    ) == [{"compiler": "gcc"}]


def test_expand_difference() -> None:
    assert keyso.expand(
        {
            "_difference": {
                "_minuend": {"compiler": ["gcc", "clang", "intel"]},
                "_subtrahend": {"compiler": ["clang"]},
            }
        }
    ) == [{"compiler": "gcc"}, {"compiler": "intel"}]


def test_expand_set() -> None:
    assert keyso.expand(
        {
            "_set": [
                {"compiler": "gcc", "optimization": "O2"},
                {"compiler": "clang", "optimization": "O3"},
            ]
        }
    ) == [
        {"compiler": "clang", "optimization": "O3"},
        {"compiler": "gcc", "optimization": "O2"},
    ]


def test_set_treats_plain_nested_dict_values_as_data() -> None:
    assert keyso.expand({"_set": [{"params": {"nx": 128}}]}) == [{"params": {"nx": 128}}]


def test_set_unwraps_literal_values() -> None:
    assert keyso.expand({"_set": [{"params": {"_literal": {"nx": 128}}}]}) == [
        {"params": {"nx": 128}}
    ]


def test_literal_value() -> None:
    assert keyso.expand({"params": {"_literal": {"nx": 128, "ny": 256}}}) == [
        {"params": {"nx": 128, "ny": 256}}
    ]


def test_nested_value() -> None:
    assert keyso.expand(
        {
            "build": {
                "_nested": {
                    "_product": [
                        {"compiler": ["gcc", "clang"]},
                        {"optimization": ["O2", "O3"]},
                    ]
                }
            }
        }
    ) == [
        {"build": {"compiler": "clang", "optimization": "O2"}},
        {"build": {"compiler": "clang", "optimization": "O3"}},
        {"build": {"compiler": "gcc", "optimization": "O2"}},
        {"build": {"compiler": "gcc", "optimization": "O3"}},
    ]


def test_nested_value_inside_multivalue() -> None:
    assert keyso.expand(
        {
            "build": [
                {"_nested": {"compiler": ["gcc", "clang"]}},
                {"_literal": {"compiler": "custom"}},
            ]
        }
    ) == [
        {"build": {"compiler": "clang"}},
        {"build": {"compiler": "custom"}},
        {"build": {"compiler": "gcc"}},
    ]


def test_plain_dict_in_value_position_is_invalid() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"params": {"nx": 128}})


def test_value_keyword_at_top_level_is_invalid() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"_nested": {"compiler": "gcc"}})


def test_unknown_reserved_keyword_at_top_level_is_invalid() -> None:
    # _minuend is reserved but not a top-level expression operator.
    with pytest.raises(keyso.ReservedKeywordError):
        keyso.expand({"_minuend": {"compiler": "gcc"}})


def test_normalize() -> None:
    assert keyso.normalize({"compiler": ["gcc", "clang"]}) == {
        "_set": [{"compiler": "clang"}, {"compiler": "gcc"}]
    }


@pytest.mark.parametrize("operator", ["_product", "_union", "_intersection"])
def test_operator_requires_non_empty_list(operator: str) -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({operator: []})


@pytest.mark.parametrize("operator", ["_product", "_union", "_intersection"])
def test_operator_requires_list(operator: str) -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({operator: {"compiler": "gcc"}})


def test_operator_operand_must_be_dictionary() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"_product": [{"compiler": "gcc"}, "not a dictionary"]})


def test_difference_requires_dictionary() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"_difference": []})


def test_difference_requires_exact_keys() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"_difference": {"_minuend": {"a": 1}}})


def test_difference_operands_must_be_dictionaries() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand(
            {
                "_difference": {
                    "_minuend": {"a": 1},
                    "_subtrahend": "not a dictionary",
                }
            }
        )


def test_set_requires_list() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"_set": {"a": 1}})


def test_set_items_must_be_dictionaries() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"_set": ["not a dictionary"]})


def test_set_keys_must_be_strings() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"_set": [{1: "bad"}]})  # type: ignore[dict-item]


def test_set_rejects_reserved_configuration_keys() -> None:
    with pytest.raises(keyso.ReservedKeywordError):
        keyso.expand({"_set": [{"_product": "bad"}]})


def test_input_must_be_dictionary() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.from_dictionary(["not", "a", "dict"])  # type: ignore[arg-type]


def test_input_must_have_one_construct() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.from_dictionary({})


def test_top_level_key_must_be_string() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.from_dictionary({1: "bad"})  # type: ignore[dict-item]


def test_nested_requires_dictionary() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"build": {"_nested": "not a dictionary"}})


def test_literal_in_list_value() -> None:
    assert keyso.expand({"params": [{"_literal": {"a": 1}}, {"_literal": {"a": 2}}]}) == [
        {"params": {"a": 1}},
        {"params": {"a": 2}},
    ]


def test_list_value_plain_dict_item_is_invalid() -> None:
    with pytest.raises(keyso.DictionaryError):
        keyso.expand({"params": [{"a": 1}]})


def test_unhashable_custom_object_value_is_rejected() -> None:
    class Unhashable:
        __hash__ = None

    with pytest.raises(TypeError):
        keyso.Configuration.from_mapping({"value": Unhashable()})


def test_constructor_namespace_is_available_but_not_flattened() -> None:
    assert hasattr(keyso, "construct")
    assert hasattr(keyso.construct, "Product")
    assert hasattr(keyso.construct, "Literal")
    assert hasattr(keyso.construct, "Nested")
    assert hasattr(keyso.construct, "evaluate")

    assert not hasattr(keyso, "Product")
    assert not hasattr(keyso, "Literal")
    assert not hasattr(keyso, "Nested")
    assert not hasattr(keyso, "evaluate")


def test_constructor_namespace_product_class() -> None:
    dictionary = keyso.construct.Product(
        {"compiler": ["gcc", "clang"]},
        {"optimization": ["O2", "O3"]},
    ).to_dictionary()

    assert dictionary == {
        "_product": [
            {"compiler": ["gcc", "clang"]},
            {"optimization": ["O2", "O3"]},
        ]
    }
    assert keyso.expand(dictionary) == [
        {"compiler": "clang", "optimization": "O2"},
        {"compiler": "clang", "optimization": "O3"},
        {"compiler": "gcc", "optimization": "O2"},
        {"compiler": "gcc", "optimization": "O3"},
    ]


def test_constructor_namespace_lowercase_helpers_return_dictionaries() -> None:
    dictionary = keyso.construct.product(
        {"compiler": ["gcc", "clang"]},
        {"optimization": ["O2"]},
    )

    assert dictionary == {
        "_product": [
            {"compiler": ["gcc", "clang"]},
            {"optimization": ["O2"]},
        ]
    }
    assert keyso.expand(dictionary) == [
        {"compiler": "clang", "optimization": "O2"},
        {"compiler": "gcc", "optimization": "O2"},
    ]


def test_constructor_namespace_nested_and_literal() -> None:
    dictionary = {
        "build": keyso.construct.nested(
            keyso.construct.Product(
                {"compiler": ["gcc", "clang"]},
                {"params": keyso.construct.literal({"flags": ["-O2", "-Wall"]})},
            )
        )
    }

    assert keyso.expand(dictionary) == [
        {"build": {"compiler": "clang", "params": {"flags": ["-O2", "-Wall"]}}},
        {"build": {"compiler": "gcc", "params": {"flags": ["-O2", "-Wall"]}}},
    ]


def test_constructor_namespace_evaluate() -> None:
    space = keyso.construct.evaluate(
        keyso.construct.Union(
            {"compiler": "gcc"},
            {"compiler": "clang"},
        )
    )

    assert isinstance(space, keyso.ConfigurationSpace)
    assert space.to_dicts() == [{"compiler": "clang"}, {"compiler": "gcc"}]


def test_constructor_namespace_difference_intersection_and_set() -> None:
    dictionary = keyso.construct.difference(
        keyso.construct.intersection(
            {"compiler": ["gcc", "clang", "intel"]},
            {"compiler": ["gcc", "clang"]},
        ),
        keyso.construct.set_({"compiler": "clang"}),
    )

    assert keyso.expand(dictionary) == [{"compiler": "gcc"}]

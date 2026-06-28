# keyso

`keyso` is a small Python library for expanding dictionary-based configuration
spaces.

The input format is plain Python dictionaries.  The public data model is not the
syntax tree.  The public model consists of semantic configuration objects:

- `ConfigurationType`
- `Configuration`
- `ConfigurationSpace`

Syntax constructs such as `_literal`, `_nested`, `_product`, `_union`,
`_intersection`, and `_difference` are handled by the dictionary front end. They
are not exported into the top-level `keyso` namespace as semantic data types.
When users want to construct these dictionaries programmatically, they can use
the separate `keyso.construct` namespace.

## Basic usage

```python
import keyso

space = keyso.from_dictionary(
    {
        "_product": [
            {"compiler": ["gcc", "clang"]},
            {"optimization": ["O2", "O3"]},
        ]
    }
)

assert space.configuration_type.to_set() == {"compiler", "optimization"}

configs = space.to_dicts()
```

`configs` is:

```python
[
    {"compiler": "clang", "optimization": "O2"},
    {"compiler": "clang", "optimization": "O3"},
    {"compiler": "gcc", "optimization": "O2"},
    {"compiler": "gcc", "optimization": "O3"},
]
```

The exact ordering is deterministic but should not be used as part of the
mathematical meaning of a configuration space.

## Public API

Top-level semantic API:

```python
keyso.ConfigurationType
keyso.Configuration
keyso.ConfigurationSpace
keyso.from_dictionary(dictionary) -> ConfigurationSpace
keyso.expand(dictionary) -> list[dict[str, object]]
keyso.normalize(dictionary) -> {"_set": list[dict[str, object]]}
```

Constructor namespace for programmatically building dictionary inputs:

```python
keyso.construct.Literal
keyso.construct.Nested
keyso.construct.Set
keyso.construct.Product
keyso.construct.Union
keyso.construct.Intersection
keyso.construct.Difference
keyso.construct.evaluate(...)
```

These names intentionally live under `keyso.construct`, not directly under
`keyso`.


## Constructor namespace

For code that wants to build keyso dictionaries instead of writing raw dictionary
literals, use `keyso.construct`.

```python
import keyso

space = keyso.construct.evaluate(
    keyso.construct.Product(
        {"compiler": ["gcc", "clang"]},
        {"optimization": ["O2", "O3"]},
    )
)

assert space.to_dicts() == [
    {"compiler": "clang", "optimization": "O2"},
    {"compiler": "clang", "optimization": "O3"},
    {"compiler": "gcc", "optimization": "O2"},
    {"compiler": "gcc", "optimization": "O3"},
]
```

The constructor objects can also be converted to plain dictionaries:

```python
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
```

Lower-case helper functions return dictionaries directly:

```python
dictionary = keyso.construct.product(
    {"compiler": ["gcc", "clang"]},
    {"optimization": ["O2"]},
)

configs = keyso.expand(dictionary)
```

For nested and literal values:

```python
dictionary = {
    "build": keyso.construct.nested(
        keyso.construct.Product(
            {"compiler": ["gcc", "clang"]},
            {"params": keyso.construct.literal({"flags": ["-O2", "-Wall"]})},
        )
    )
}
```

## Combining keys

Multiple independent keys must be combined explicitly with `_product`.

Valid:

```python
{
    "_product": [
        {"compiler": ["gcc", "clang"]},
        {"optimization": ["O2", "O3"]},
    ]
}
```

Invalid:

```python
{
    "compiler": ["gcc", "clang"],
    "optimization": ["O2", "O3"],
}
```

The second form is rejected because it would be an implicit product.

## Nested dictionaries

Use `_nested` when the value of a key should be produced by an independent
keyso dictionary.

```python
keyso.expand(
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
)
```

produces:

```python
[
    {"build": {"compiler": "clang", "optimization": "O2"}},
    {"build": {"compiler": "clang", "optimization": "O3"}},
    {"build": {"compiler": "gcc", "optimization": "O2"}},
    {"build": {"compiler": "gcc", "optimization": "O3"}},
]
```

Use `_literal` when a dictionary is data and should not be interpreted as keyso:

```python
keyso.expand(
    {
        "params": {
            "_literal": {
                "nx": 128,
                "ny": 128,
            }
        }
    }
)
```

## Normalization

`normalize()` returns the normalized `_set` representation:

```python
keyso.normalize({"compiler": ["gcc", "clang"]})
```

returns:

```python
{
    "_set": [
        {"compiler": "clang"},
        {"compiler": "gcc"},
    ]
}
```

## Development

Run tests with:

```bash
hatch run tests:test
```

or directly:

```bash
PYTHONPATH=src pytest
```

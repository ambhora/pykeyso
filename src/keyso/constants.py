# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# ------------------------------------------------------------------------------

"""Constants used by the dictionary front end."""

KEYWORD_LITERAL = "_literal"
KEYWORD_NESTED = "_nested"
KEYWORD_SET = "_set"
KEYWORD_PRODUCT = "_product"
KEYWORD_UNION = "_union"
KEYWORD_INTERSECTION = "_intersection"
KEYWORD_DIFFERENCE = "_difference"
KEYWORD_MINUEND = "_minuend"
KEYWORD_SUBTRAHEND = "_subtrahend"

KEYWORDS = frozenset(
    {
        KEYWORD_LITERAL,
        KEYWORD_NESTED,
        KEYWORD_SET,
        KEYWORD_PRODUCT,
        KEYWORD_UNION,
        KEYWORD_INTERSECTION,
        KEYWORD_DIFFERENCE,
        KEYWORD_MINUEND,
        KEYWORD_SUBTRAHEND,
    }
)

EXPRESSION_KEYWORDS = frozenset(
    {
        KEYWORD_SET,
        KEYWORD_PRODUCT,
        KEYWORD_UNION,
        KEYWORD_INTERSECTION,
        KEYWORD_DIFFERENCE,
    }
)

VALUE_KEYWORDS = frozenset({KEYWORD_LITERAL, KEYWORD_NESTED})

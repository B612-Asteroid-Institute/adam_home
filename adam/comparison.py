from enum import IntEnum


class Comparison(IntEnum):
    """Comparison class.

    A comparison utility library that can be used as a way of configuring comparison functions as method arguments
    """

    Equals = 0
    GreaterThan = 1
    GreaterThanEquals = 2
    LessThan = 3
    LessThanEquals = 4

    def compare(self, test_value, actual):
        if self == Comparison.Equals:
            return actual == test_value

        if self == Comparison.GreaterThan:
            return actual > test_value

        if self == Comparison.GreaterThanEquals:
            return actual >= test_value

        if self == Comparison.LessThan:
            return actual < test_value

        if self == Comparison.LessThanEquals:
            return actual <= test_value

        raise ValueError(f"Unknown comparison type: {self}")

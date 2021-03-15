from enum import IntEnum


class Comparison(IntEnum):
    """Comparison class.

    A comparison utility library that can be used as a way of configuring
    comparison functions as method arguments
    """

    Equals = 0
    GreaterThan = 1
    GreaterThanOrEquals = 2
    LessThan = 3
    LessThanOrEquals = 4

    def compare(self, test_value, actual):
        if self == Comparison.Equals:
            return actual == test_value

        if self == Comparison.GreaterThan:
            return actual > test_value

        if self == Comparison.GreaterThanOrEquals:
            return actual >= test_value

        if self == Comparison.LessThan:
            return actual < test_value

        if self == Comparison.LessThanOrEquals:
            return actual <= test_value

        raise ValueError(f"Unknown comparison type: {self}")

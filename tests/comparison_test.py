from adam import Comparison
import unittest


class ComparisonTest(unittest.TestCase):
    """Unit tests for Comparison type

    """

    def test_equality(self):
        self.assertTrue(Comparison.Equals.compare(1, 1))
        self.assertTrue(Comparison.Equals.compare(1.0, 1.0))
        self.assertTrue(Comparison.Equals.compare("MyValue", "MyValue"))

        self.assertFalse(Comparison.Equals.compare(1, 2))
        self.assertFalse(Comparison.Equals.compare(1.0, 2.0))
        self.assertFalse(Comparison.Equals.compare("MyValue", "OtherValue"))

    def test_greater_than(self):
        self.assertTrue(Comparison.GreaterThan.compare(1, 2))
        self.assertTrue(Comparison.GreaterThan.compare(1.0, 2.0))

        self.assertFalse(Comparison.GreaterThan.compare(1, 1))
        self.assertFalse(Comparison.GreaterThan.compare(1, 0))
        self.assertFalse(Comparison.GreaterThan.compare(1, -1))
        self.assertFalse(Comparison.GreaterThan.compare(1.0, 1.0))
        self.assertFalse(Comparison.GreaterThan.compare(1.0, 0.0))
        self.assertFalse(Comparison.GreaterThan.compare(1.0, -1.0))

    def test_greater_than_equal(self):
        self.assertTrue(Comparison.GreaterThanOrEquals.compare(1, 2))
        self.assertTrue(Comparison.GreaterThanOrEquals.compare(1.0, 2.0))
        self.assertTrue(Comparison.GreaterThanOrEquals.compare(1, 1))
        self.assertTrue(Comparison.GreaterThanOrEquals.compare(1.0, 1.0))

        self.assertFalse(Comparison.GreaterThanOrEquals.compare(1, 0))
        self.assertFalse(Comparison.GreaterThanOrEquals.compare(1, -1))
        self.assertFalse(Comparison.GreaterThanOrEquals.compare(1.0, 0.0))
        self.assertFalse(Comparison.GreaterThanOrEquals.compare(1.0, -1.0))

    def test_less_than(self):
        self.assertTrue(Comparison.LessThan.compare(10, 2))
        self.assertTrue(Comparison.LessThan.compare(10.0, 2.0))

        self.assertFalse(Comparison.LessThan.compare(1, 1))
        self.assertFalse(Comparison.LessThan.compare(0, 1))
        self.assertFalse(Comparison.LessThan.compare(-1, 1))
        self.assertFalse(Comparison.LessThan.compare(1.0, 1.0))
        self.assertFalse(Comparison.LessThan.compare(0.0, 1.0))
        self.assertFalse(Comparison.LessThan.compare(-1.0, 1.0))

    def test_less_than_equal(self):
        self.assertTrue(Comparison.LessThanOrEquals.compare(10, 2))
        self.assertTrue(Comparison.LessThanOrEquals.compare(10.0, 2.0))
        self.assertTrue(Comparison.LessThanOrEquals.compare(10, 10))
        self.assertTrue(Comparison.LessThanOrEquals.compare(10.0, 10.0))

        self.assertFalse(Comparison.LessThanOrEquals.compare(0, 1))
        self.assertFalse(Comparison.LessThanOrEquals.compare(-1, 1))
        self.assertFalse(Comparison.LessThanOrEquals.compare(0.0, 1.0))
        self.assertFalse(Comparison.LessThanOrEquals.compare(-1.0, 1.0))

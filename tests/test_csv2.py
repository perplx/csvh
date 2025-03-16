#!/usr/bin/env python3

# standard imports
import copy
import csv
import unittest

# local imports
import csv2


class TestDialect(unittest.TestCase):
    """Test dialect functions."""

    def test_init_dialect(self):
        """Test init_dialect()"""
        self.assertIsInstance(csv2.init_dialect(), csv.excel)
        self.assertIsInstance(csv2.init_dialect("excel"), csv.excel)
        self.assertIsInstance(csv2.init_dialect("excel_tab"), csv.excel_tab)
        self.assertIsInstance(csv2.init_dialect("unix"), csv.unix_dialect)
        with self.assertRaises(ValueError):
            _ = csv2.init_dialect("BOGUS")

    def test_read_dialect(self):
        """Test read_dialect()"""

        # Dialect before and after test
        dialect_base = csv.excel()
        dialect_test = copy.copy(dialect_base)

        # test which fields are modified
        dialect_test = csv2.read_dialect(dialect_test, delimiter="\t", quoting=csv.QUOTE_NONE)
        self.assertEqual(dialect_test.delimiter, "\t")
        self.assertNotEqual(dialect_test.delimiter, dialect_base.delimiter)
        self.assertEqual(dialect_test.quoting, csv.QUOTE_NONE)
        self.assertNotEqual(dialect_test.quoting, dialect_base.quoting)
        self.assertEqual(dialect_test.quotechar, dialect_base.quotechar)
        self.assertEqual(dialect_test.escapechar , dialect_base.escapechar)
        self.assertEqual(dialect_test.lineterminator, dialect_base.lineterminator)
        self.assertEqual(dialect_test.skipinitialspace, dialect_base.skipinitialspace)


class TestProlog(unittest.TestCase):
    """Test prolog functions."""

    def test_filter_prolog(self):
        raise NotImplementedError


class TestFilterCols(unittest.TestCase):
    """Test column-filtering functions."""

    def test_read_cols(self):
        """Test read_cols()"""
        input_cols = ["a", "b", "c", "d"]
        self.assertEqual(csv2.read_cols(input_cols, [], []), input_cols)
        self.assertEqual(csv2.read_cols(input_cols, ["a", "c"], []), ["a", "c"])
        self.assertEqual(csv2.read_cols(input_cols, [], ["a", "c"]), ["b", "d"])
        self.assertEqual(csv2.read_cols(input_cols, ["a", "c"], ["c"]), ["a"])
        with self.assertRaises(KeyError):
            _ = csv2.read_cols(input_cols, ["BOGUS!"], [])
        with self.assertRaises(KeyError):
            _ = csv2.read_cols(input_cols, [], ["BOGUS!"])

    def test_filter_cols(self):
        """Test filter_cols()"""
        input_row = {"a": "1", "b": "2", "c": "3", "d": "4"}
        self.assertEqual(csv2.filter_cols({}, []), {})
        self.assertEqual(csv2.filter_cols(input_row, []), input_row)
        self.assertEqual(csv2.filter_cols(input_row, ["b", "d"]), {"b": "2", "d": "4"})
        with self.assertRaises(KeyError):
            _ = csv2.filter_cols(input_row, ["BOGUS!"])

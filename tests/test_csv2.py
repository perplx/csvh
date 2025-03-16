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
        """Test `init_dialect()`."""
        self.assertIsInstance(csv2.init_dialect(), csv.excel)
        self.assertIsInstance(csv2.init_dialect("excel"), csv.excel)
        self.assertIsInstance(csv2.init_dialect("excel_tab"), csv.excel_tab)
        self.assertIsInstance(csv2.init_dialect("unix"), csv.unix_dialect)
        with self.assertRaises(ValueError):
            _ = csv2.init_dialect("BOGUS")

    def test_read_dialect(self):
        """Test `read_dialect()`."""

        # Dialect before and after test
        dialect_base = csv.excel()
        dialect_copy = copy.copy(dialect_base)
        dialect_test = csv2.read_dialect(dialect_copy, delimiter="\t", quoting=csv.QUOTE_NONE)

        # test which fields are modified
        self.assertEqual(dialect_test.delimiter, "\t")
        self.assertNotEqual(dialect_test.delimiter, dialect_base.delimiter)
        self.assertEqual(dialect_test.quoting, csv.QUOTE_NONE)
        self.assertNotEqual(dialect_test.quoting, dialect_base.quoting)

        # test which fields are unchanged
        self.assertEqual(dialect_test.quotechar, dialect_base.quotechar)
        self.assertEqual(dialect_test.escapechar , dialect_base.escapechar)
        self.assertEqual(dialect_test.lineterminator, dialect_base.lineterminator)
        self.assertEqual(dialect_test.skipinitialspace, dialect_base.skipinitialspace)


class TestProlog(unittest.TestCase):
    """Test prolog functions."""

    PROLOG_LINES = ["BOGUS BOGUS BOGUS\n"]

    def setUp(self):
        """Open test-files. `self._prolog_file` has the prolog, `self._test_file` has no prolog, otherwise identical."""
        self._prolog_file = open("data/tess_01.csv", "rt")
        self._test_file = open("data/tess_00.csv", "rt")

    def tearDown(self):
        """Close test-files."""
        self._prolog_file.close()
        self._test_file.close()

    def test_filter_prolog_keep(self):
        """Test `filter_prolog(keep_prolog=1)`."""

        # ensure the prolog lines are kept
        prolog_lines = csv2.filter_prolog(self._prolog_file, 1, 0)
        self.assertEqual(prolog_lines, self.PROLOG_LINES)

        # ensure the prolog was skipped
        prolog_text = self._prolog_file.read()
        test_text = self._test_file.read()
        self.assertEqual(prolog_text, test_text)

    def test_filter_prolog_skip(self):
        """Test `filter_prolog(skip_prolog=1)`."""

        # ensure the prolog lines are skipped
        prolog_lines = csv2.filter_prolog(self._prolog_file, 0, 1)
        self.assertEqual(prolog_lines, [])

        # ensure the prolog was skipped
        prolog_text = self._prolog_file.read()
        test_text = self._test_file.read()
        self.assertEqual(prolog_text, test_text)

    # keep overrides skip
    def test_filter_prolog_both(self):
        """Test `filter_prolog(keep_prolog=1, skip_prolog=1)`.
        As implemented, `keep_prolog` overrides `skip_prolog`.
        """

        # ensure the prolog lines are kept
        prolog_lines = csv2.filter_prolog(self._prolog_file, 1, 1)
        self.assertEqual(prolog_lines, self.PROLOG_LINES)

        # ensure the prolog was skipped
        prolog_text = self._prolog_file.read()
        test_text = self._test_file.read()
        self.assertEqual(prolog_text, test_text)


class TestFilterCols(unittest.TestCase):
    """Test column-filtering functions."""

    def test_read_cols(self):
        """Test `read_cols()`."""
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
        """Test `filter_cols()`."""
        input_row = {"a": "1", "b": "2", "c": "3", "d": "4"}
        self.assertEqual(csv2.filter_cols({}, []), {})
        self.assertEqual(csv2.filter_cols(input_row, []), input_row)
        self.assertEqual(csv2.filter_cols(input_row, ["b", "d"]), {"b": "2", "d": "4"})
        with self.assertRaises(KeyError):
            _ = csv2.filter_cols(input_row, ["BOGUS!"])


class TestFilterRows(unittest.TestCase):
    """Test row-filtering functions."""

    def test_read_cols(self):
        """Test `read_row_filters()`."""
        row_args = [["a", "a1", "a2"], ["b", "b2", "b4"]]
        row_filters = {"a": ["a1", "a2"], "b": ["b2", "b4"]}
        self.assertEqual(csv2.read_row_filters(row_args), row_filters)

    def test_keep_row(self):
        """Test `keep_row()`."""
        row_filters = {"a": ["a1", "a2"], "b": ["b2", "b4"]}

        # test all filters are satisfied
        self.assertEqual(csv2.keep_row({"a": "a1", "b": "b1"}, row_filters), False)  # one match
        self.assertEqual(csv2.keep_row({"a": "a2", "b": "b2"}, row_filters), True)  # both match
        self.assertEqual(csv2.keep_row({"a": "a3", "b": "b3"}, row_filters), False)  # no match
        self.assertEqual(csv2.keep_row({"a": "a4", "b": "b4"}, row_filters), False)  # one match

        # test missing key in filters
        with self.assertRaises(KeyError):
            _ = csv2.keep_row({}, row_filters)
        with self.assertRaises(KeyError):
            _ = csv2.keep_row({"a": "a0"}, row_filters)

    def test_skip_row(self):
        """Test `skip_row()`."""
        row_filters = {"a": ["a1", "a2"], "b": ["b2", "b4"]}

        # test all filters are satisfied
        self.assertEqual(csv2.skip_row({"a": "a1", "b": "b1"}, row_filters), False)  # one match
        self.assertEqual(csv2.skip_row({"a": "a2", "b": "b2"}, row_filters), False)  # both match
        self.assertEqual(csv2.skip_row({"a": "a3", "b": "b3"}, row_filters), True)  # no match
        self.assertEqual(csv2.skip_row({"a": "a4", "b": "b4"}, row_filters), False)  # one match

        # test missing key in filters
        with self.assertRaises(KeyError):
            _ = csv2.skip_row({}, row_filters)
        with self.assertRaises(KeyError):
            _ = csv2.skip_row({"a": "a0"}, row_filters)

    def test_filter_rows(self):
        """Test `filter_rows()`."""

        input_rows = [
            {"a": "a1", "b": "b1"},
            {"a": "a2", "b": "b2"},
            {"a": "a3", "b": "b3"},
            {"a": "a4", "b": "b4"},
        ]

        test_rows = list(csv2.filter_rows(input_rows, {}, {}))
        self.assertEqual(test_rows, input_rows)

        keep_rows = {"a": ["a1", "a2"]}
        skip_rows = {"b": ["b2", "b4"]}
        test_rows = list(csv2.filter_rows(input_rows, keep_rows, skip_rows))
        self.assertEqual(test_rows, [{"a": "a1", "b": "b1"}])

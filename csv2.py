#!/usr/bin/env python

import argparse
import csv
import logging
from typing import Iterable, Optional, Sequence, TextIO


# global constants
# DEFAULT_QUOTING = csv.QUOTE_ALL
# DEFAULT_QUOTING = csv.QUOTE_MINIMAL
DEFAULT_QUOTING = csv.QUOTE_NONE
# DEFAULT_QUOTING = csv.QUOTE_NONNUMERIC
DEFAULT_QUOTECHAR = '"'
DEFAULT_ESCAPECHAR = "\\"

# prepare global logger
logger = logging.getLogger(__name__)


# dialect
def read_dialect(delimiter: Optional[str], quoting: int, quotechar: str, escapechar: str) -> csv.Dialect:

    dialect: csv.Dialect = csv.excel()  # default in std lib
    logger.debug("starting dialect: %s", dialect)
    if delimiter:
        dialect.delimiter = delimiter
    if quoting:
        dialect.quoting = quoting
    if quotechar:
        dialect.quotechar = quotechar
    if escapechar:
        dialect.escapechar = escapechar

    logger.debug("returning dialect: %s", dialect)
    return dialect


DIALECT_ATTRS = [
    "delimiter",
    "lineterminator",
    "quoting",
    "quotechar",
    "escapechar",
]


def log_dialect(log_level: int, dialect: csv.Dialect) -> None:
    logger.log(log_level, "Dialect:")
    for attr in DIALECT_ATTRS:  # FIXME add more fields
        logger.log(log_level, "\t%s = %r", attr, getattr(dialect, attr))


# prolog-filtering


def filter_prolog(input_file: TextIO, keep_prolog: int, skip_prolog: int) -> list[str]:
    """Filter the first lines in the file."""
    prolog_lines = []
    num_prolog_lines = max(keep_prolog, skip_prolog)
    for i in range(1, num_prolog_lines + 1):
        line = input_file.readline()
        if keep_prolog:
            logger.debug("keeping prolog line %d / %d : %r", i, num_prolog_lines, line)
            prolog_lines.append(line)
        elif skip_prolog:
            logger.debug("skipping prolog line %d / %d : %r", i, num_prolog_lines, line)
    return prolog_lines


# column-filtering


# TODO order by keep_cols? repeats?
def keep_fields(input_cols: Sequence[str], keep_cols: list[str], skip_cols: list[str]) -> list[str]:
    """List the columns to keep from the input-file based on lists of columns to keep and skip."""
    kept_cols = list(input_cols)
    if keep_cols:
        kept_cols = [c for c in kept_cols if c in keep_cols]
    if skip_cols:
        kept_cols = [c for c in kept_cols if c not in skip_cols]
    return kept_cols


# fixme modify input row instead?
def filter_cols(row: dict[str, str], keep_cols: list[str]) -> dict[str, str]:
    """Return trow with only the columns in ``keep_cols``."""
    if keep_cols:
        return {c: row[c] for c in keep_cols}
    return row


# row-filtering


# FIXME make this a type= for ArgumentParser?
def read_row_filters(row_args: list[list[str]]) -> dict[str, list[str]]:
    """Parse row-filter command-line parameters."""
    return {r[0]: r[1:] for r in row_args}


def keep_row(row, keep_rows: dict[str, list[str]]) -> bool:
    """Whether to keep a row based on the row-filters for rows to keep."""
    if keep_rows:
        for col, values in keep_rows.items():
            if row[col] not in values:
                return False
    return True


def skip_row(row, skip_rows: dict[str, list[str]]) -> bool:
    """Whether to keep a row based on the row-filters for rows to skip."""
    if skip_rows:
        for col, values in skip_rows.items():
            if row[col] in values:
                return False
    return True


def filter_rows(input_rows: Iterable[dict[str, str]], keep_rows: dict[str, list[str]], skip_rows: dict[str, list[str]]):
    """Keep rows that match the row-filters."""
    for row in input_rows:
        if keep_row(row, keep_rows) and skip_row(row, skip_rows):
            yield row


# csv-processing


def process_csv(
    # files
    input_file: TextIO,
    output_file: TextIO,
    # dialect
    input_dialect: csv.Dialect,
    output_dialect: csv.Dialect,
    # prolog
    keep_prolog: int,
    skip_prolog: int,
    # filter
    keep_cols: list[str],
    skip_cols: list[str],
    keep_rows: dict[str, list[str]],
    skip_rows: dict[str, list[str]],
) -> None:
    """Process CSV from ``input_file``, write to ``output_file``."""

    # prepare to read from to input-file
    logger.debug("reading from file: %s", input_file.name)

    # filter prolog-lines
    prolog_lines = filter_prolog(input_file, keep_prolog, skip_prolog)

    logger.debug("input csv dialect: %s", input_dialect)
    csv_reader = csv.DictReader(input_file, dialect=input_dialect)
    csv_fields = csv_reader.fieldnames
    if csv_fields is None:
        csv_fields = []

    # which fields to keep
    kept_cols = keep_fields(csv_fields, keep_cols, skip_cols)
    logger.debug("keeping columns: %s", kept_cols)

    # prepare to write to output-file
    logger.debug("writing to file: %s", output_file.name)
    csv_writer = csv.DictWriter(output_file, kept_cols)

    # write prolog lines that were kept
    for i, line in enumerate(prolog_lines, start=1):
        logger.debug("writing prolog line %d / %d : %r", i, len(prolog_lines), line)
        output_file.write(line)

    # write filtered rows
    csv_writer.writeheader()
    for row in filter_rows(csv_reader, keep_rows, skip_rows):
        row = filter_cols(row, kept_cols)
        csv_writer.writerow(row)


# main


def parse_args():
    """Specify command-line parameters"""

    # define command-line paramerters
    arg_parser = argparse.ArgumentParser(description=__doc__)
    file_group = arg_parser.add_argument_group("file")
    file_group.add_argument("input_file", type=argparse.FileType("rt"))
    file_group.add_argument("output_file", type=argparse.FileType("wt"))

    # FIXME dialect names
    dialect_group = arg_parser.add_argument_group("dialect")
    dialect_group.add_argument("--input-delimiter")
    dialect_group.add_argument("--input-quoting")
    dialect_group.add_argument("--input-quotechar")
    dialect_group.add_argument("--input-escapechar")
    dialect_group.add_argument("--output-delimiter")
    dialect_group.add_argument("--output-quoting")
    dialect_group.add_argument("--output-quotechar")
    dialect_group.add_argument("--output-escapechar")

    prolog_group = arg_parser.add_mutually_exclusive_group()
    prolog_group.add_argument(
        "--keep-prolog", type=int, default=0,
        help="number of header lines to skip, they will be reproduced in the output"
    )
    prolog_group.add_argument(
        "--skip-prolog", type=int, default=0,
        help="number of header lines to skip, they will be omitted in the output"
    )

    filter_group = arg_parser.add_argument_group("filter")
    filter_group.add_argument(
        "--keep-cols", type=str, nargs="+", help="list of column-names to keep, in the order to be kept"
    )
    filter_group.add_argument(
        "--skip-cols", type=str, nargs="+", help="list of column-names to skip, in the order to be kept"
    )
    filter_group.add_argument("--keep-rows", type=str, nargs="+", action="append", default=[])
    filter_group.add_argument("--skip-rows", type=str, nargs="+", action="append", default=[])

    # read command-line paramerters
    args = arg_parser.parse_args()
    return args


def main():
    """Process CSV."""

    # read command-line parameters
    args = parse_args()

    # prepare logging
    logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.NOTSET)
    logger.debug("args: %s", args)

    # dialects
    input_dialect = read_dialect(
        args.input_delimiter,
        args.input_quoting,
        args.input_quotechar,
        args.input_escapechar,
    )
    logger.debug("input dialect:")
    log_dialect(logging.DEBUG, input_dialect)
    output_dialect = read_dialect(
        args.output_delimiter,
        args.output_quoting,
        args.output_quotechar,
        args.output_escapechar,
    )
    logger.debug("output dialect:")
    log_dialect(logging.DEBUG, output_dialect)

    # row-filters
    keep_rows = read_row_filters(args.keep_rows),
    skip_rows = read_row_filters(args.skip_rows),

    # process CSV
    process_csv(
        # files
        args.input_file,
        args.output_file,
        # dialect
        input_dialect,
        output_dialect,
        # prolog
        args.keep_prolog,
        args.skip_prolog,
        # filer columns
        args.keep_cols,
        args.skip_cols,
        # filter rows
        keep_rows,
        skip_rows,
    )


if __name__ == "__main__":
    main()

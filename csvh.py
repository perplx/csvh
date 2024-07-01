#!/usr/bin/env python

"""CSV processor tool"""

# standard imports
import argparse
import dataclasses
import csv
import logging
from typing import Mapping, TextIO


# global logger
logger = logging.getLogger("csvh")

DELIMITER_ATTRS = [
    "delimiter",
    "lineterminator",
    "quoting",
    "quotechar",
    "escapechar",
]


def log_dialect(log_level: int, dialect: csv.Dialect) -> None:
    logger.log(log_level, "Dialect:")
    for attr in DELIMITER_ATTRS:  # FIXME add more fields
        logger.log(log_level, "\t%s = %r", attr, getattr(dialect, attr))


def process_csv(
        input_file: TextIO,
        output_file: TextIO,
        keep_prolog: int,
        skip_prolog: int,
        dialect: str | csv.Dialect,
        keep_cols: Mapping[str,str],
    ) -> None:
    """Read CSV data from `input_file`, process, write to `output_file`"""

    # prepare to read from input-file
    logger.debug("reading from file %s", input_file.name)

    # skip prolog
    num_prolog_lines = max(keep_prolog, skip_prolog)
    if keep_prolog or skip_prolog:
        prolog_lines = []
        for i in range(1, num_prolog_lines + 1):
            line = input_file.readline()
            if keep_prolog:
                logger.debug("keeping prolog line %d / %s : %r", i, num_prolog_lines, line)
                prolog_lines.append(line)
            elif skip_prolog:
                logger.debug("skipping prolog line %d / %s : %r", i, num_prolog_lines, line)

    # determine dialect
    logger.debug("dialect in: %r", dialect)
    if dialect == "sniff":
        start_offset = input_file.tell()
        csv_sniffer = csv.Sniffer()
        dialect: csv.Dialect = csv_sniffer.sniff(input_file.read(1024))
        input_file.seek(start_offset)
    elif isinstance(dialect, str):
        if dialect in csv.list_dialects():
            logger.debug("using dialect: %r", dialect)
        else:
            logger.error("unrecognized dialect: %r", dialect)
    elif isinstance(dialect, csv.Dialect):
        logger.debug("using dialect: %s", dialect)
        log_dialect(logging.DEBUG, dialect)
    else:
        raise ValueError(f"incorrect {csv.Dialect} : {dialect}")

    # open input-file
    csv_reader = csv.DictReader(input_file, dialect=dialect)

    # read column-names
    input_columns = csv_reader.fieldnames
    logger.debug("reading %d columns: %s", len(input_columns), input_columns)

    # if `--keep-cols` was given, filter the column-names
    if keep_cols:
        output_columns = [c for c in keep_cols]
    else:
        output_columns = input_columns
    logger.debug("writing %d columns: %s", len(output_columns), output_columns)

    # prepare to write to output-file
    logger.debug("writing to file %s", output_file.name)

    # write prolog lines that were kept
    for i, line in enumerate(prolog_lines, start=1):
        logger.debug("writing prolog line %d / %s : %r", i, num_prolog_lines, line)
        output_file.write(line)

    # read from input-file, write to output-file
    csv_writer = csv.DictWriter(output_file, output_columns, dialect=dialect)
    csv_writer.writeheader()
    for input_row in csv_reader:
        logger.debug("input_row: %s", input_row)  # FIXME use restkey to warn when restkey is set!
        output_row = dict((k, v) for (k, v) in input_row.items() if k in output_columns)
        logger.debug("output_row: %s", output_row)
        csv_writer.writerow(output_row)


def dialect_args(args: argparse.Namespace) -> csv.Dialect:
    """"""

    dialect: csv.Dialect = csv.excel()  # default in std lib

    for attr in DELIMITER_ATTRS:
        value = getattr(args, attr)
        if value is not None:
            logger.debug("arg %r: %r", attr, value)
            setattr(dialect, attr, value)

    logger.debug("dialect: %s", dialect)
    log_dialect(logging.DEBUG, dialect)

    return dialect


def main():
    # define command-line paramerters
    arg_parser = argparse.ArgumentParser(description=__doc__)
    file_group = arg_parser.add_argument_group("file")
    file_group.add_argument("input_file", type=argparse.FileType("rt"))
    file_group.add_argument("output_file", type=argparse.FileType("wt"))

    dialect_group = arg_parser.add_argument_group("dialect")
    dialect_name_group = dialect_group.add_mutually_exclusive_group()
    dialect_name_group.add_argument("--sniff", action="store_true")
    dialect_name_group.add_argument("--dialect", choices=csv.list_dialects())
    dialect_group.add_argument("--delimiter")
    dialect_group.add_argument("--lineterminator")

    # FIXME separate input, output dialects
    quoting_group = arg_parser.add_argument_group("quoting")
    quoting_group.add_argument("--quoting")
    quoting_group.add_argument("--quotechar")
    quoting_group.add_argument("--escapechar")

    prolog_group = arg_parser.add_mutually_exclusive_group()
    prolog_group.add_argument("--keep-prolog", type=int, default=0, help="number of header lines to skip, they will be reproduced in the output")
    prolog_group.add_argument("--skip-prolog", type=int, default=0, help="number of header lines to skip, they will be omitted in the output")

    filter_group = arg_parser.add_argument_group("filter")
    filter_group.add_argument("--keep-cols", type=str, nargs="+", help="list of column-names to keep, in the order to be kept")

    # read command-line paramerters
    args = arg_parser.parse_args()

    # prepare logging
    logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.NOTSET)

    if args.sniff:
        logger.debug("sniff")
        dialect = "sniff"
    elif args.dialect:
        dialect = args.dialect
        logger.debug("name %s", dialect)
    else:
        logger.debug("args")
        dialect = dialect_args(args)

    process_csv(
        args.input_file,
        args.output_file,
        args.keep_prolog,
        args.skip_prolog,
        dialect,
        args.keep_cols,
    )


if __name__ == "__main__":
    main()

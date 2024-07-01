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


def log_dialect(log_level: int, dialect: csv.Dialect) -> None:
    for attr in ["delimiter", "lineterminator", "quotechar"]:
        logger.log(log_level, "%s = %r", attr, getattr(dialect, attr))


def process_csv(
        input_file: TextIO,
        output_file: TextIO,
        keep_prolog: int,
        skip_prolog: int,
        dialect_name: str,
        keep_cols: Mapping[str,str],
    ) -> None:
    """Read CSV data from `input_file`, process, write to `output_file`"""

    logger.debug("reading from file %s", input_file.name)

    # skip prolog
    num_prolog_lines = max(keep_prolog, skip_prolog)
    if keep_prolog or skip_prolog:
        prolog_lines = []
        for i in range(num_prolog_lines):
            line = input_file.readline()
            logger.debug("keeping prolog line %d / %s : %r", i+1, num_prolog_lines, line)
            if keep_prolog:
                prolog_lines.append(line)
    elif skip_prolog:
        for i in range(num_prolog_lines):
            line = input_file.readline()
            logger.debug("skipping prolog line %d / %s : %r", i+1, num_prolog_lines, line)


    if dialect_name:
        logger.debug("using dialect: %r", dialect_name)
        dialect = dialect_name
    else:
        start_offset = input_file.tell()
        csv_sniffer = csv.Sniffer()
        dialect = csv_sniffer.sniff(input_file.read(1024))
        input_file.seek(start_offset)

        logger.debug("detected dialect: %s", dialect)
        log_dialect(logging.DEBUG, dialect)

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

    logger.debug("writing to file %s", output_file.name)

    # write prolog lines that were kept
    for i, line in enumerate(prolog_lines):
        logger.debug("writing prolog line %d / %s : %r", i+1, num_prolog_lines, line)
        output_file.write(line)

    # read from input-file, write to output-file
    csv_writer = csv.DictWriter(output_file, output_columns, dialect=dialect)
    csv_writer.writeheader()
    for input_row in csv_reader:
        output_row = dict((k, v) for (k, v) in input_row.items() if k in output_columns)
        csv_writer.writerow(output_row)

    pass

def main():
    # define command-line paramerters
    arg_parser = argparse.ArgumentParser(description=__doc__)
    file_group = arg_parser.add_argument_group("file")
    file_group.add_argument("input_file", type=argparse.FileType("rt"))
    file_group.add_argument("output_file", type=argparse.FileType("wt"))

    # dialect options
    dialect_group = arg_parser.add_argument_group("dialect")
    dialect_group.add_argument("--dialect", choices=csv.list_dialects())
    dialect_group.add_argument("--delimiter")

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

    dialect_names = csv.list_dialects()
    logger.debug("dialects: %s", dialect_names)

    process_csv(
        args.input_file,
        args.output_file,
        args.keep_prolog,
        args.skip_prolog,
        args.dialect,
        args.keep_cols,
    )


if __name__ == "__main__":
    main()

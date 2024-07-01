#!/usr/bin/env python

"""CSV processor tool"""

# standard imports
import argparse

def main():
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument("input_file", type=argparse.FileType("rt"))
    arg_parser.add_argument("output_file", type=argparse.FileType("wt"))

    quoting_group = arg_parser.add_argument_group("quoting")
    quoting_group.add_argument("--quoting")
    quoting_group.add_argument("--quotechar")
    quoting_group.add_argument("--escapechar")

    args = arg_parser.parse_args()


if __name__ == "__main__":
    main()
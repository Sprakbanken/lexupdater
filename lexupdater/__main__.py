#!/usr/bin/env python
# coding=utf-8

"""Parse input arguments and run lexupdater.main."""

import argparse
import logging

from .config import DIALECTS
from .lexupdater import main


# Argument parser
parser = argparse.ArgumentParser()

parser.add_argument(
    "--dialects",
    "-d",
    action="store",
    type=str,
    nargs="+",
    default=DIALECTS,
    help="Apply replacement rules on one or more specified dialects.",
)
parser.add_argument(
    "--write_base",
    "-b",
    action="store_true",
    help=(
        "Generate a base lexicon file, containing the state of the lexicon "
        "prior to updates."
    )
)
parser.add_argument(
    "--match_words",
    "-m",
    action="store_true",
    help=(
        "Print list of the words that will be affected by update rules for the "
        "given dialects"
    )
)
parser.add_argument(
    "--verbose",
    "-v",
    action="store_true",
    help=(
        "Print logging messages at the debugging level. "
        "See https://docs.python.org/3/library/logging.html#logging.debug"
    )
)
args = parser.parse_args()

if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

main(args.dialects, args.write_base, args.match_words)

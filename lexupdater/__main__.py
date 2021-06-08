#!/usr/bin/env python
# coding=utf-8

"""Parse input arguments and run lexupdater.main."""

import argparse
import logging

from config import DIALECTS, OUTPUT_DIR
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
        "Print list of the words that will be affected by update rules "
        "for the given dialects"
    )
)
parser.add_argument(
    "--verbose",
    "-v",
    action="store_true",
    help=(
        "Print logging messages at the debugging level. "
        "See python documentation on logging for more info."
    )
)
parser.add_argument(
    "--log_file",
    "-l",
    action="store",
    type=str,
    nargs="?",
    help="Save all logging messages to the given file. ",
)
args = parser.parse_args()

if args.verbose:
    LOGGING_LEVEL = logging.DEBUG
else:
    LOGGING_LEVEL = logging.INFO

logging.basicConfig(
    filename=(OUTPUT_DIR / args.log_file) if args.log_file else None,
    level=LOGGING_LEVEL,
    format='%(asctime)s | %(levelname)s | %(module)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M')

main(args.dialects, args.write_base, args.match_words)

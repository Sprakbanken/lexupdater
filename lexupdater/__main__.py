#!/usr/bin/env python
# coding=utf-8

"""Parse input arguments and run lexupdater.main."""

import argparse

from .config import DIALECTS
from .lexupdater import main

# Argument parser
parser = argparse.ArgumentParser()

parser.add_argument(
    "--print_dialects",
    "-d",
    action="store",
    type=str,
    nargs="+",
    default=DIALECTS,
    help="Generate lexicon files for one or more specified dialects.",
)
parser.add_argument(
    "--print_base",
    "-b",
    action="store_true",
    help=(
        "Generate a base lexicon file, containing the state of the lexicon "
        "prior to updates."
    ),
)
args = parser.parse_args()

main(args.print_dialects, args.print_base)

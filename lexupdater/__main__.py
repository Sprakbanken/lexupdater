#!/usr/bin/env python
# coding=utf-8

import argparse

from .config import dialects
from .lexupdater import main


# Argument parser
parser = argparse.ArgumentParser()

parser.add_argument(
    "--print_dialects",
    "-d",
    action="store",
    type=str,
    nargs="*",
    default=dialects,
    help="Generate lexicon files for one or more specified dialects.",
)
parser.add_argument(
    "--print_base",
    "-b",
    action="store_true",
    help="Generate a base lexicon file, containing the state of the lexicon "
         "prior to updates."
)
args = parser.parse_args()
args.print_dialects = dialects if args.print_dialects is None \
    else args.print_dialects

main(args.print_dialects, args.print_base)

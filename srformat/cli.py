"""Command-line entry point: read raw schedule lines, write normalized CSV."""

from __future__ import annotations

import argparse
import csv
import sys
from typing import Iterable, TextIO

from .normalize import ParseError, normalize_record

HEADER = ("due", "interval_days", "ease", "rating")


def process(lines: Iterable[str], out: TextIO, skip_errors: bool) -> int:
    writer = csv.writer(out)
    writer.writerow(HEADER)
    error_count = 0
    for lineno, raw in enumerate(lines, start=1):
        raw = raw.rstrip("\n")
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        try:
            record = normalize_record(raw)
        except ParseError as exc:
            error_count += 1
            print(f"line {lineno}: {exc}", file=sys.stderr)
            if not skip_errors:
                return 1
            continue
        writer.writerow(record.as_row())
    return 1 if error_count and not skip_errors else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="srformat",
        description="Normalize messy spaced-repetition schedule records into a fixed CSV shape.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="path to a file of raw records, one per line (default: stdin)",
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="skip lines that fail to parse instead of stopping",
    )
    args = parser.parse_args(argv)

    if args.input:
        with open(args.input, encoding="utf-8") as handle:
            return process(handle, sys.stdout, args.skip_errors)
    return process(sys.stdin, sys.stdout, args.skip_errors)


if __name__ == "__main__":
    raise SystemExit(main())

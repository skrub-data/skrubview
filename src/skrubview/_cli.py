import argparse
from pathlib import Path

from rich import print as rprint

from ._report import Report


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str)
    parser.add_argument("--order_by", type=str, default=None)
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument("--html", action="store_true")
    format_group.add_argument("--open", action="store_true")
    format_group.add_argument("--json", action="store_true")
    format_group.add_argument("--dict", action="store_true")
    format_group.add_argument("--text", action="store_true")
    args = parser.parse_args()

    input_file = Path(args.input_file).resolve()
    report = Report(input_file, order_by=args.order_by)
    if args.open:
        report.open_html()
    elif args.dict:
        rprint(report.summary_without_plots)
    elif args.json:
        print(report.json)
    elif args.html:
        print(report.html)
    elif args.text:
        print(report.text)
    else:
        print(report.text)

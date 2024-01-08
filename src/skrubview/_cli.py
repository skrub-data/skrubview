import argparse
from pathlib import Path

from rich import print as rprint

from ._report import Report


def run():
    parser = argparse.ArgumentParser(
        description="Generate a report about a CSV or Parquet file."
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="CSV or Parquet file for which a report will be generated. "
        "The filename extension must be '.csv' or '.parquet' . "
        "CSV files will be parsed with Polars' default configuration.",
    )
    parser.add_argument(
        "--order_by",
        type=str,
        default=None,
        help="Sort by this column. "
        "Other numerical columns will be plotted as function of the sorting column. "
        "Must be of numerical or datetime type.",
    )
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "--html", action="store_true", help="Generate HTML report."
    )
    format_group.add_argument(
        "--open", action="store_true", help="Open HTML report in webbrowser."
    )
    format_group.add_argument(
        "--json", action="store_true", help="Generate JSON report."
    )
    format_group.add_argument(
        "--text",
        action="store_true",
        help="Generate text report (this is the default).",
    )
    format_group.add_argument(
        "--dict",
        action="store_true",
        help="Generate detailed text representation of the report's contents "
        "(mostly for debugging).",
    )
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

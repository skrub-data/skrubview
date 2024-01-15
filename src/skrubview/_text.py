from rich.console import Group, Console
from rich.panel import Panel
from rich.table import Table

from . import _utils


_COLORS = {"ok": "green", "warning": "yellow", "critical": "red"}


def to_text(summary):
    # note: another way would be to set output to a file object. But this
    # doesn't seem to work with jupyter notebooks; console's output still goes
    # to stdout instead of the stringio:
    #
    # out_stream = io.StringIO()
    # console = Console(file=out_stream, force_terminal=True)
    # return out_stream.getvalue()
    #
    # also capture lets rich decide whether to include codes or not
    console = Console()
    with console.capture() as capture:
        _print_summary(summary, console)
    return capture.get()


def _print_summary(summary, console):
    if summary.get("title") is not None:
        console.rule(f"[bold blue]{summary['title']}[/bold blue]")
    overview = (
        f"Dataframe with [blue]{summary['n_rows']} rows[/blue] "
        f"and [blue]{summary['n_columns']} columns[/blue]."
    )
    if "file_path" in summary:
        overview += f"\nFile: {summary['file_path']}"
    console.print(overview)
    _print_first_row(summary, console)
    _print_constant_columns(summary, console)
    for column in summary["columns"]:
        _print_column_summary(column, console)
    console.print(overview)


def _print_first_row(summary, console):
    console.print("First row:")
    console.print(
        {k: _utils.ellide_string(v) for (k, v) in summary["first_row_dict"].items()}
    )


def _print_constant_columns(summary, console):
    cols = [col for col in summary["columns"] if col.get("value_is_constant")]
    if not cols:
        return
    text = "\n".join(
        f"[bold]{col['name']}:[/bold] {_utils.ellide_string(col['constant_value'])!r}"
        for col in cols
    )
    panel = Panel(
        text,
        title=f"[bold]Constant columns[/bold]",
        title_align="left",
        highlight=True,
    )
    console.print(panel)


def _print_column_summary(summary, console):
    if summary.get("value_is_constant"):
        return
    # we use a raw string rather than rich.text.Text() to keep the default
    # highlighting
    text = []
    text.append(f"[bold]{summary['dtype']}[/bold]\n")
    text.append("Null values: ")
    color = _COLORS[summary["nulls_level"]]
    text.append(
        f"[{color}]{summary['null_count']} "
        f"({summary['null_proportion']:0.2%})[/{color}]\n"
    )
    if "n_zeros" in summary:
        text.append(
            f"Zeros: {summary['n_zeros']} ({summary['zeros_proportion']:0.2%})\n"
        )
    if "n_unique" in summary:
        text.append(f"Unique values: {summary['n_unique']}\n")
    if "value_counts" in summary:
        # TODO in theory ellide_string could create collisions
        ellided = {
            _utils.ellide_string(k): v for (k, v) in summary["value_counts"].items()
        }
        text.append(f"Most frequent value counts: {ellided}\n")
    if "mean" in summary:
        text.append(
            f"Mean: {summary['mean']:#0.3g} "
            f"Standard deviation: {summary['standard_deviation']:#0.3g}\n"
        )
    if "min" in summary:
        text.append(
            f"Min: {_utils.format_number(summary['min'])} "
            f"Max: {_utils.format_number(summary['max'])}\n"
        )
    if summary.get("string_length_is_constant", False):
        text.append(
            f"All strings have the same length: {summary['constant_string_length']}\n"
        )
    text = "".join(text).rstrip()
    content = [text]
    quantiles_to_display = ["quantiles"]
    if not summary.get("string_length_is_constant", False):
        quantiles_to_display.append("string_length_quantiles")
    for quantiles_name in quantiles_to_display:
        if quantiles_name in summary:
            content.append(
                _prepare_quantiles_table(
                    summary[quantiles_name],
                    quantiles_name.capitalize().replace("_", " "),
                )
            )

    panel = Panel(
        Group(*content),
        title=f"[bold]{summary['name']}[/bold]",
        title_align="left",
        highlight=True,
    )
    console.print(panel)


def _prepare_quantiles_table(quantiles, name):
    table = Table(title=name, title_style="bold")
    for q in quantiles:
        table.add_column({0.0: "min", 1.0: "max"}.get(q, f"{q:.0%}"))
    table.add_row(*map(str, quantiles.values()))
    return table

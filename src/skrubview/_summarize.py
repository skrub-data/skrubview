from pathlib import Path

import numpy as np
import polars as pl

from . import _plotting, _utils

_HIGH_CARDINALITY_THRESHOLD = 10


def summarize_dataframe(
    dataframe, *, order_by=None, file_path=None, with_plots=False, title=None
):
    # TODO: pandas support
    if not isinstance(dataframe, pl.DataFrame):
        dataframe = pl.DataFrame(dataframe)
    if file_path is not None:
        file_path = Path(file_path)
    df = dataframe.__dataframe_consortium_standard__()
    df = df.persist()
    shape = df.shape()
    summary = {
        "n_rows": int(shape[0]),
        "n_columns": int(shape[1]),
        "columns": [],
        "head_html": _utils.to_html(df.slice_rows(0, 5, 1)),
        "tail_html": _utils.to_html(df.slice_rows(-5, None, 1)),
        "first_row_dict": _utils.first_row_dict(df),
    }
    if title is not None:
        summary["title"] = title
    if file_path is not None:
        summary["file_path"] = str(file_path.resolve())
        summary["file_name"] = file_path.name
    if order_by is not None:
        df = df.sort(order_by)
        summary["order_by"] = order_by
    for position, column_name in enumerate(df.column_names):
        summary["columns"].append(
            _summarize_column(
                df.col(column_name),
                position,
                dataframe_summary=summary,
                with_plots=with_plots,
                order_by_column=None if order_by is None else df.col(order_by),
            )
        )
    summary["n_constant_columns"] = sum(
        c["value_is_constant"] for c in summary["columns"]
    )
    return summary


def _summarize_column(
    column, position, dataframe_summary, *, with_plots, order_by_column
):
    summary = {
        "position": position,
        "name": column.name,
        "dtype": _utils.get_dtype_name(column),
        "value_is_constant": False,
    }
    _add_nulls_summary(summary, column, dataframe_summary=dataframe_summary)
    _add_sample_values(summary, column)
    _add_value_counts(
        summary, column, dataframe_summary=dataframe_summary, with_plots=with_plots
    )
    _add_numeric_summary(
        summary, column, with_plots=with_plots, order_by_column=order_by_column
    )
    _add_datetime_summary(summary, column, with_plots=with_plots)
    summary["plot_names"] = [k for k in summary.keys() if k.endswith("_plot")]
    return summary


def _add_nulls_summary(summary, column, dataframe_summary):
    null_count = int(column.is_null().sum())
    summary["null_count"] = null_count
    null_proportion = null_count / dataframe_summary["n_rows"]
    summary["null_proportion"] = null_proportion
    if summary["null_proportion"] == 0.0:
        summary["nulls_level"] = "ok"
    elif summary["null_proportion"] == 1.0:
        summary["nulls_level"] = "critical"
    else:
        summary["nulls_level"] = "warning"


def _add_sample_values(summary, column):
    rng = np.random.default_rng(0)
    non_missing = column.filter(~column.is_null())
    n_non_missing = int(non_missing.len())
    if n_non_missing == 0:
        return
    size = min(n_non_missing, 5)
    sample_indices = sorted(rng.choice(range(n_non_missing), replace=False, size=size))
    ns = column.__column_namespace__()
    sample_indices = ns.column_from_sequence(sample_indices)
    sample_values = np.asarray(non_missing.take(sample_indices).to_array()).tolist()
    summary["sample_values"] = list(map(_utils.ellide_string, sample_values))


def _add_value_counts(summary, column, *, dataframe_summary, with_plots):
    ns = column.__column_namespace__()
    dtype = _utils.get_dtype(column)
    if ns.is_dtype(dtype, "numeric") or isinstance(dtype, ns.Datetime):
        summary["high_cardinality"] = True
        return
    n_unique, value_counts = _utils.value_counts(
        column.filter(~column.is_null()),
        high_cardinality_threshold=_HIGH_CARDINALITY_THRESHOLD,
    )
    summary["n_unique"] = n_unique
    summary["unique_proportion"] = n_unique / dataframe_summary["n_rows"]
    summary["high_cardinality"] = n_unique >= _HIGH_CARDINALITY_THRESHOLD
    summary["value_counts"] = value_counts
    if n_unique == 0:
        return
    if n_unique == 1:
        summary["value_is_constant"] = True
        summary["constant_value"] = _utils.ellide_string(
            next(iter(value_counts.keys()))
        )
    else:
        summary["value_is_constant"] = False
        if with_plots:
            summary["value_counts_plot"] = _plotting.value_counts(
                value_counts, n_unique, color=_plotting.COLORS[1]
            )


def _add_datetime_summary(summary, column, with_plots):
    ns = column.__column_namespace__()
    if not isinstance(_utils.get_dtype(column), ns.Datetime):
        return
    min_date = column.min().scalar
    max_date = column.max().scalar
    if min_date == max_date:
        summary["value_is_constant"] = True
        summary["constant_value"] = min_date.isoformat()
        return
    summary["value_is_constant"] = False
    summary["min"] = min_date.isoformat()
    summary["max"] = max_date.isoformat()
    if with_plots:
        summary["histogram_plot"] = _plotting.histogram(
            column, None, color=_plotting.COLORS[0]
        )


def _add_numeric_summary(summary, column, with_plots, order_by_column):
    ns = column.__column_namespace__()
    if not ns.is_dtype(_utils.get_dtype(column), "numeric"):
        return
    if not summary["high_cardinality"]:
        return
    summary["standard_deviation"] = float(column.std())
    summary["mean"] = float(column.mean())
    quantiles = _utils.quantiles(column)
    if quantiles[0.0] == quantiles[1.0]:
        summary["value_is_constant"] = True
        summary["constant_value"] = quantiles[0.0]
        return
    summary["value_is_constant"] = False
    summary["quantiles"] = quantiles
    if not with_plots:
        return
    if order_by_column is None:
        summary["histogram_plot"] = _plotting.histogram(
            column, "Value distribution", color=_plotting.COLORS[0]
        )
    else:
        summary["line_plot"] = _plotting.line(order_by_column, column)

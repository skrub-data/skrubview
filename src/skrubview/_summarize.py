from pathlib import Path

import polars as pl

from . import _plotting, _utils, _interactions

_HIGH_CARDINALITY_THRESHOLD = 10
_SUBSAMPLE_SIZE = 3000
_ASSOCIATION_THRESHOLD = 0.2


def summarize_dataframe(
    dataframe, *, order_by=None, file_path=None, with_plots=False, title=None
):
    dataframe_module_name = dataframe.__class__.__module__.split(".")[0]
    # TODO: pandas support
    if not isinstance(dataframe, pl.DataFrame):
        dataframe = pl.DataFrame(dataframe)
    if file_path is not None:
        file_path = Path(file_path)
    df = dataframe.__dataframe_consortium_standard__()
    df = df.persist()
    shape = df.shape()
    summary = {
        "dataframe_module": dataframe_module_name,
        "n_rows": int(shape[0]),
        "n_columns": int(shape[1]),
        "columns": [],
        "head": _utils.to_row_list(df.slice_rows(0, 5, 1)),
        "tail": _utils.to_row_list(df.slice_rows(-5, None, 1)),
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
    _add_interactions(df, summary)
    return summary


def _add_interactions(df, dataframe_summary):
    df = _utils.sample(df.dataframe, n=_SUBSAMPLE_SIZE)
    associations = _interactions.stack_symmetric_associations(
        _interactions.cramer_v(df),
        df.__dataframe_consortium_standard__().column_names,
    )[:20]
    dataframe_summary["top_associations"] = [
        dict(zip(("left_column", "right_column", "cramer_v"), a))
        for a in associations
        if a[2] > _ASSOCIATION_THRESHOLD
    ]


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
    _add_value_counts(
        summary, column, dataframe_summary=dataframe_summary, with_plots=with_plots
    )
    _add_numeric_summary(
        summary,
        column,
        dataframe_summary=dataframe_summary,
        with_plots=with_plots,
        order_by_column=order_by_column,
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
        summary["constant_value"] = next(iter(value_counts.keys()))
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


def _add_numeric_summary(
    summary, column, dataframe_summary, with_plots, order_by_column
):
    del dataframe_summary
    ns = column.__column_namespace__()
    if not ns.is_dtype(_utils.get_dtype(column), "numeric"):
        return
    if not summary["high_cardinality"]:
        return
    std = column.std().scalar
    summary["standard_deviation"] = float("nan") if std is None else float(std)
    summary["mean"] = float(column.mean())
    quantiles = _utils.quantiles(column)
    summary["inter_quartile_range"] = quantiles[0.75] - quantiles[0.25]
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
            column, title=None, color=_plotting.COLORS[0]
        )
    else:
        summary["line_plot"] = _plotting.line(order_by_column, column)

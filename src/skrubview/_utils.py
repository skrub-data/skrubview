import base64
import re
from pathlib import Path

import polars as pl


def read(file_path):
    if file_path is not None:
        file_path = Path(file_path)
    suffix = file_path.suffix
    if suffix == ".parquet":
        return pl.read_parquet(file_path)
    if suffix == ".csv":
        return pl.read_csv(file_path)
    raise ValueError(f"Cannot process file extension: {suffix}")


def get_dtype(column):
    """Workaround for dtypes missing from the dataframe API.

    The dataframe API does not support many dtypes such as Categorical;
    accessing .dtype on dataframes that contain them raises an exception.
    """
    try:
        return column.dtype
    except Exception:
        return column.column.dtype


def get_dtype_name(column):
    """Workaround for dtypes missing from the dataframe API.

    The dataframe API does not support many dtypes such as Categorical;
    accessing .dtype on dataframes that contain them raises an exception.
    """
    try:
        return column.dtype.__class__.__name__
    except Exception:
        return str(column.column.dtype)


def _to_html_via_pandas(df):
    return df.to_pandas().to_html(index=False)


def _to_html_polars_native(df):
    html = df._repr_html_()
    start = re.search("<table", html).start()
    end = re.search("</table>", html).end()
    html = html[start:end]
    return html


def to_html(dataframe):
    try:
        html = _to_html_via_pandas(dataframe.dataframe)
    except Exception:
        # TODO more precise exception list
        # - pandas not installed
        # - pyarrow casting µs to ns
        html = _to_html_polars_native(dataframe.dataframe)
    html = html.replace('class="dataframe"', 'class="pure-table-striped pure-table"')
    return html


def first_row_dict(dataframe):
    first_row = dataframe.slice_rows(0, 1, 1)
    return {c: first_row.col(c).to_array().tolist()[0] for c in first_row.column_names}


def value_counts(column, high_cardinality_threshold):
    series = column.column
    value_counts = series.value_counts()
    col_1, col_2 = value_counts.columns
    n_unique = len(value_counts)
    value_counts = value_counts.sort(by=col_2, descending=True)[
        :high_cardinality_threshold
    ]
    return n_unique, dict(
        zip(
            value_counts[col_1].to_numpy().tolist(),
            value_counts[col_2].to_numpy().tolist(),
        )
    )


def quantiles(column):
    series = column.column
    return {q: series.quantile(q) for q in [0.0, 0.25, 0.5, 0.75, 1.0]}


def string_lengths(column):
    return column.column.str.len_bytes().__column_consortium_standard__()


def ellide_string(s, max_len=100):
    if not isinstance(s, str):
        return s
    if len(s) <= max_len:
        return s
    if max_len > 30:
        truncated = len(s) - max_len
        return s[: (max_len - 30)] + f"[… {truncated} more chars]"
    return s[:max_len] + "…"


def format_number(number):
    if not isinstance(number, float):
        return str(number)
    return f"{number:#.3g}"


def format_percent(proportion):
    if 0.0 < proportion < 0.001:
        return "< 0.1%"
    return f"{proportion:0.1%}"

def svg_to_img_src(svg):
    encoded_svg = base64.b64encode(svg.encode("UTF-8")).decode("UTF-8")
    return f"data:image/svg+xml;base64,{encoded_svg}"

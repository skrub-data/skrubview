import pathlib
import re
import secrets

import jinja2
from polars import dataframe

from skrub import _selectors as s
from skrub import _dataframe as sbd

from . import _utils


def _get_jinja_env():
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            pathlib.Path(__file__).resolve().parent / "_data" / "templates",
            encoding="UTF-8",
        ),
        autoescape=True,
    )
    for function_name in [
        "format_number",
        "format_percent",
        "svg_to_img_src",
        "filter_equal_snippet",
        "filter_isin_snippet",
    ]:
        env.filters[function_name] = getattr(_utils, function_name)
    return env


def _get_column_filters(dataframe):
    first_10 = sbd.column_names(dataframe)[:10]
    filters = {f"First {len(first_10)}": first_10}
    for selector in [
        s.all(),
        s.numeric(),
        ~s.numeric(),
        s.string(),
        ~s.string(),
        s.categorical(),
        ~s.categorical(),
    ]:
        filters[re.sub(r"^\((.*)\)$", r"\1", repr(selector))] = selector.expand(
            dataframe
        )
    return filters


def to_html(summary, standalone=True, column_filters=None):
    column_filters = column_filters if column_filters is not None else {}
    jinja_env = _get_jinja_env()
    if standalone:
        template = jinja_env.get_template("standalone-report.html")
    else:
        template = jinja_env.get_template("inline-report.html")
    return template.render(
        {
            "summary": summary,
            "column_filters": _get_column_filters(summary["dataframe"])
            | column_filters,
            "report_id": f"report_{secrets.token_hex()[:8]}",
        }
    )

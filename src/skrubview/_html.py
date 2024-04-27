import pathlib
import re
import secrets

import jinja2

try:
    from skrub import _selectors as s

    _SELECTORS_AVAILABLE = True
except ImportError:
    _SELECTORS_AVAILABLE = False

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
    if not _SELECTORS_AVAILABLE:
        return _get_column_filters_no_selectors(dataframe)
    filters = {}
    if sbd.shape(dataframe)[1] > 10:
        filters["First 10"] = sbd.column_names(dataframe)[:10]
    for selector in [
        s.all(),
        s.numeric(),
        ~s.numeric(),
        s.string(),
        ~s.string(),
        s.categorical(),
        ~s.categorical(),
        s.any_date(),
        ~s.any_date(),
    ]:
        filters[re.sub(r"^\((.*)\)$", r"\1", repr(selector))] = selector.expand(
            dataframe
        )
    return filters


def _get_column_filters_no_selectors(dataframe):
    # temporary manual filtering until selectors PR is merged
    first_10 = sbd.column_names(dataframe)[:10]
    filters = {f"First {len(first_10)}": first_10}
    col_names = sbd.column_names(dataframe)
    filters["all()"] = col_names

    def add_filt(f, name):
        filters[name] = [c for c in col_names if f(sbd.col(dataframe, c))]
        filters[f"~{name}"] = [c for c in col_names if c not in filters[name]]

    add_filt(sbd.is_numeric, "numeric()")
    add_filt(sbd.is_string, "string()")
    add_filt(sbd.is_categorical, "categorical()")
    add_filt(sbd.is_any_date, "any_date()")
    return filters


def to_html(summary, standalone=True, column_filters=None):
    column_filters = column_filters if column_filters is not None else {}
    jinja_env = _get_jinja_env()
    if standalone:
        template = jinja_env.get_template("standalone-report.html")
    else:
        template = jinja_env.get_template("inline-report.html")
    default_filters = _get_column_filters(summary["dataframe"])
    return template.render(
        {
            "summary": summary,
            # prioritize user-provided filters and keep them at the beginning
            "column_filters": column_filters
            | {k: v for (k, v) in default_filters.items() if k not in column_filters},
            "report_id": f"report_{secrets.token_hex()[:8]}",
        }
    )

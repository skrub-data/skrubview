import pathlib
import secrets

import jinja2

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
    ]:
        env.filters[function_name] = getattr(_utils, function_name)
    return env


def to_html(summary, standalone=True):
    jinja_env = _get_jinja_env()
    if standalone:
        template = jinja_env.get_template("standalone-report.html")
    else:
        template = jinja_env.get_template("inline-report.html")
    return template.render(
        {
            "summary": summary,
            "report_id": f"report_{secrets.token_hex()[:8]}",
        }
    )

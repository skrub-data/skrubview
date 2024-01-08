from pathlib import Path
import functools
import json

from ._summarize import summarize_dataframe
from ._html import to_html
from ._text import to_text
from ._utils import read
from ._serve import open_html_in_browser, open_file_in_browser


class Report:
    def __init__(self, data, order_by=None):
        self._summary_kwargs = {"order_by": order_by}
        if hasattr(data, "__dataframe__"):
            self.dataframe = data
        else:
            self._file_path = Path(data)
            self.dataframe = read(self._file_path)
            self._summary_kwargs["file_path"] = self._file_path

    @functools.cached_property
    def summary_with_plots(self):
        return summarize_dataframe(
            self.dataframe, with_plots=True, **self._summary_kwargs
        )

    @functools.cached_property
    def summary_without_plots(self):
        return summarize_dataframe(
            self.dataframe, with_plots=False, **self._summary_kwargs
        )

    @property
    def any_summary(self):
        if "_summary_with_plots" in self.__dict__:
            return self.summary_with_plots
        return self.summary_without_plots

    @functools.cached_property
    def text(self):
        return to_text(self.any_summary)

    @functools.cached_property
    def html(self):
        return to_html(self.summary_with_plots, standalone=True)

    @functools.cached_property
    def html_snippet(self):
        return to_html(self.summary_with_plots, standalone=False)

    @functools.cached_property
    def json(self):
        return json.dumps(self.summary_without_plots)

    def _repr_mimebundle_(self, include=None, exclude=None):
        del include, exclude
        return {"text/html": self.html_snippet, "text/plain": self.text}

    def open_html(self, file_path=None):
        if file_path is None:
            html = to_html(self.summary_with_plots, standalone=True)
            open_html_in_browser(html)
            return
        file_path = Path(file_path).resolve()
        file_path.write_text(self.html, "UTF-8")
        open_file_in_browser(file_path)

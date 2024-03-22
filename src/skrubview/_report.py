from pathlib import Path
import functools
import json

from skrub import _dataframe as sbd

from ._summarize import summarize_dataframe
from ._html import to_html
from ._text import to_text
from ._utils import read
from ._serve import open_html_in_browser, open_file_in_browser


class Report:
    """Summarize the contents of a dataframe.

    This class summarizes a dataframe, providing information such as the type
    and summary statistics (mean, number of missing values, etc.) for each
    column.

    Parameters
    ----------
    data : pandas or polars DataFrame or file path.
        The dataframe to summarize. If a ``str`` or ``pathlib.Path`` is
        provided, it must be the path to a CSV or Parquet file containing the
        dataframe. The filename extension must be ``.csv`` or ``.parquet``. CSV
        files will be parsed with Polars' default configuration; providing a
        dataframe or a parquet file instead is recommended.
    order_by : str
        Column name to use for sorting. Other numerical columns will be plotted
        as function of the sorting column. Must be of numerical or datetime
        type.
    title : str
        Title for the report.

    Attributes
    ----------
    html : str
        Report as an HTML page.
    html_snippet : str
        Report as an HTML snippet containing a single '<div>' element. Useful
        to embed the report in an HTML page or displaying it in a Jupyter
        notebook.
    text : str
        Report in text format.
    json : str
        Report in JSON format.
    summary_with_plots : dict
        Dictionary containing information about the dataframe, used to generate
        the reports. Plots such as histograms are stored as SVG strings.
    summary_without_plots : dict
        Same as ``summary_with_plots`` without the plots.
    """

    def __init__(self, data, order_by=None, title=None):
        self._summary_kwargs = {"order_by": order_by}
        self.title = title
        if sbd.is_dataframe(data):
            self.dataframe = data
        else:
            self._file_path = Path(data)
            self.dataframe = read(self._file_path)
            self._summary_kwargs["file_path"] = self._file_path

    @functools.cached_property
    def summary_with_plots(self):
        return summarize_dataframe(
            self.dataframe, with_plots=True, title=self.title, **self._summary_kwargs
        )

    @functools.cached_property
    def summary_without_plots(self):
        return summarize_dataframe(
            self.dataframe, with_plots=False, title=self.title, **self._summary_kwargs
        )

    @property
    def _any_summary(self):
        if "_summary_with_plots" in self.__dict__:
            return self.summary_with_plots
        return self.summary_without_plots

    @functools.cached_property
    def text(self):
        return to_text(self._any_summary)

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
        """Open the HTML report in a web browser.

        Parameters
        ----------
        file_path : str or pathlib.Path
            If provided, the report is saved at the specified location and the
            file is opened in the browser. If ``None``, nothing is written to
            disk. A server is started to send the report to the browser and
            shut down immediately afterwards; refreshing the page will result
            in a "Not found" error.
        """
        if file_path is None:
            open_html_in_browser(self.html)
            return
        file_path = Path(file_path).resolve()
        file_path.write_text(self.html, "UTF-8")
        open_file_in_browser(file_path)

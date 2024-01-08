"""Summarize the contents of a dataframe and generate an HTML or text report."""

from ._cli import run
from ._report import Report

__version__ = "0.0.1"
__all__ = ["run", "Report", "__version__"]

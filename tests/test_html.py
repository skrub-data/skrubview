from bs4 import BeautifulSoup

from skrubview._summarize import summarize_dataframe
from skrubview._html import to_html


def test_to_html(make_dataframe):
    df = make_dataframe()
    summary = summarize_dataframe(df)
    html = to_html(summary)
    doc = BeautifulSoup(html, "html.parser")
    # * 2 bc they appear in the 'sample' and in the 'columns' sections
    assert len(doc.select(".skrubview-column-summary")) == df.shape[1] * 2

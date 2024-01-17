from polars import selectors as cs

from skrubview._summarize import summarize_dataframe


def test_summarize(make_dataframe):
    df = make_dataframe()
    # polars uses µs by default, pandas ns
    df = df.with_columns(cs.datetime().dt.cast_time_unit("ns"))
    summary = summarize_dataframe(df)
    pandas_summary = summarize_dataframe(df.to_pandas())
    assert summary.pop("dataframe_module") == "polars"
    assert pandas_summary.pop("dataframe_module") == "pandas"
    assert summary == pandas_summary

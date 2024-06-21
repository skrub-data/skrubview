from skrubview._summarize import summarize_dataframe


def test_summarize(make_dataframe):
    # TODO
    df = make_dataframe()
    summarize_dataframe(df)

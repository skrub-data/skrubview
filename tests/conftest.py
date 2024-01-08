import datetime
import string

import numpy as np
import polars as pl
import pytest


_PRINTABLE_CHARS = list(string.printable)
_LETTERS_PUNCT = list(string.printable + string.punctuation + " ")
_DEFAULT_N_UNIQUE = 10


def _get_generators():
    return {
        "float": _make_floats,
        "int": _make_ints,
        "str": _make_strings,
        "category": _make_strings,
        "datetime": _make_dates,
    }


def _get_default_config():
    return {
        "n_rows": 40,
        "columns": [{"dtype": dtype} for dtype in _get_generators().keys()],
    }


def _make_dataframe(config=None):
    if config is None:
        config = _get_default_config()
    columns = []
    for i, column_config in enumerate(config["columns"]):
        columns.append(
            _make_column(column_config, n_rows=config["n_rows"], random_seed=i)
        )
    return pl.DataFrame(columns)


@pytest.fixture
def make_dataframe():
    return _make_dataframe


def _make_floats(column_config, n_rows, rng):
    del column_config
    return rng.normal(size=n_rows)


def _make_ints(column_config, n_rows, rng):
    max_n_unique = column_config.get("max_n_unique", _DEFAULT_N_UNIQUE)
    return rng.integers(0, max_n_unique, size=n_rows)


def _random_string(rng, max_len=100, source=_PRINTABLE_CHARS):
    return "".join(rng.choice(source, size=rng.poisson(max_len)))


def _make_strings(column_config, n_rows, rng):
    max_n_unique = column_config.get("max_n_unique", _DEFAULT_N_UNIQUE)
    choices = [_random_string(rng) for _ in range(max_n_unique)]
    return rng.choice(choices, size=n_rows)


def _make_dates(column_config, n_rows, rng):
    start = datetime.datetime.fromisoformat("1000-01-01")
    end = datetime.datetime.fromisoformat("3000-01-01")
    delta = end - start
    all_offsets = rng.uniform(
        0,
        delta.total_seconds(),
        size=column_config.get("max_n_unique", _DEFAULT_N_UNIQUE),
    )
    offsets = rng.choice(all_offsets, size=n_rows)
    dates = [start + datetime.timedelta(seconds=off) for off in offsets]
    return dates


def _make_column(column_config, n_rows, random_seed):
    rng = np.random.default_rng(random_seed)
    data = _get_generators()[column_config["dtype"]](column_config, n_rows, rng)
    name = column_config.get("name", _random_string(rng, 10, _LETTERS_PUNCT) + "_")
    column = pl.Series(values=data, name=name)
    if column_config["dtype"] == "category":
        column = column.cast(pl.Categorical)
    return column

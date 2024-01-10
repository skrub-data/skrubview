import io

import numpy as np
from matplotlib import pyplot as plt

from . import _utils

# from matplotlib import colormaps, colors
# _PASTEL = list(map(colors.rgb2hex, colormaps.get_cmap("tab10").colors))

_SEABORN = [
    "#4c72b0",
    "#dd8452",
    "#55a868",
    "#c44e52",
    "#8172b3",
    "#937860",
    "#da8bc3",
    "#8c8c8c",
    "#ccb974",
    "#64b5cd",
]
COLORS = _SEABORN
COLOR_0 = COLORS[0]


def _serialize(fig, close=True):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="svg", bbox_inches="tight")
    out = buffer.getvalue().decode("UTF-8")
    if close:
        plt.close(fig)
    return out


def _rotate_ticklabels(ax):
    if len(ax.get_xticklabels()[0].get_text()) > 5:
        ax.set_xticks(ax.get_xticks(), ax.get_xticklabels(), rotation=45, ha="right")
        w, h = ax.figure.get_size_inches()
        ax.figure.set_size_inches((w, h + 0.3))


def histogram(col, title=None, color=COLOR_0):
    values = np.asarray(col.to_array())
    fig, ax = plt.subplots(figsize=(3, 1.5), layout="compressed")
    ax.hist(values, color=color)
    if title is not None:
        ax.set_title(title)
    _rotate_ticklabels(ax)
    return _serialize(fig)


def line(x_col, y_col):
    x = np.asarray(x_col.to_array())
    y = np.asarray(y_col.to_array())
    fig, ax = plt.subplots(figsize=(3, 2), layout="compressed")
    ax.plot(x, y)
    ax.set_xlabel(x_col.name)
    ax.set_ylabel(y_col.name)
    _rotate_ticklabels(ax)
    return _serialize(fig)


def value_counts(value_counts, n_unique, color=COLOR_0):
    values = [_utils.ellide_string(s, 30) for s in value_counts.keys()][::-1]
    counts = list(value_counts.values())[::-1]
    height = 0.2 * (len(value_counts) + 1.1)
    if n_unique > len(value_counts):
        title = f"{len(value_counts)} most frequent out of {n_unique}"
        height += .5
    else:
        title = None
    width = 0.1 * max(len(str(v)) for v in values) + 2
    fig, ax = plt.subplots(figsize=(width, height), layout="compressed")
    ax.barh(list(map(str, values)), counts, color=color)
    if title is not None:
        ax.set_title(title)
    return _serialize(fig)

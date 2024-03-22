import io

from matplotlib import pyplot as plt

from skrub import _dataframe as sbd
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


def _despine(ax):
    ax.spines[["top", "right"]].set_visible(False)


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


def _get_adjusted_fig_size(fig, ax, direction, target_size):
    size_display = getattr(ax.get_window_extent(), direction)
    size = fig.dpi_scale_trans.inverted().transform((size_display, 0))[0]
    dim = 0 if direction == "width" else 1
    fig_size = fig.get_size_inches()[dim]
    return target_size * (fig_size / size)


def _adjust_fig_size(fig, ax, target_w, target_h):
    w = _get_adjusted_fig_size(fig, ax, "width", target_w)
    h = _get_adjusted_fig_size(fig, ax, "height", target_h)
    fig.set_size_inches((w, h))


def histogram(col, title=None, color=COLOR_0):
    values = sbd.to_numpy(col)
    fig, ax = plt.subplots()
    _despine(ax)
    ax.hist(values, color=color)
    if title is not None:
        ax.set_title(title)
    _rotate_ticklabels(ax)
    _adjust_fig_size(fig, ax, 2.0, 1.0)
    return _serialize(fig)


def line(x_col, y_col):
    x = sbd.to_numpy(x_col)
    y = sbd.to_numpy(y_col)
    fig, ax = plt.subplots()
    _despine(ax)
    ax.plot(x, y)
    ax.set_xlabel(_utils.ellide_string_short(x_col.name))
    _rotate_ticklabels(ax)
    _adjust_fig_size(fig, ax, 2.0, 1.0)
    return _serialize(fig)


def value_counts(value_counts, n_unique, color=COLOR_0):
    values = [_utils.ellide_string_short(s) for s in value_counts.keys()][::-1]
    counts = list(value_counts.values())[::-1]
    if n_unique > len(value_counts):
        title = f"{len(value_counts)} most frequent"
    else:
        title = None
    fig, ax = plt.subplots()
    _despine(ax)
    ax.barh(list(map(str, range(len(values)))), counts, color=color)
    ax.set_yticks(ax.get_yticks())
    ax.set_yticklabels(list(map(str, values)))
    if title is not None:
        ax.set_title(title)

    _adjust_fig_size(fig, ax, 1.0, 0.2 * len(values))
    return _serialize(fig)

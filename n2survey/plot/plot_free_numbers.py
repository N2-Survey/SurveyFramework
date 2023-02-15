from typing import Dict, Optional, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from .common import label_wrap

__all__ = ["plot_free_numbers"]


def plot_free_numbers(
    data,
    theme: Optional[Dict] = None,
    plot_title: Union[str, bool] = False,
    textwrap_legend: int = 100,
    max_textwrap_legend: int = 200,
    **kwargs,
) -> Tuple[mpl.figure.Figure, mpl.axes.Axes]:

    if theme is not None:
        sns.set_theme(**theme)

    nr_options = len(data.columns)

    fig, ax = plt.subplots(nrows=nr_options)

    columns = label_wrap(data.columns, textwrap_legend, max_textwrap_legend)
    for i, column in enumerate(data.columns):
        counts, bins, patches = ax[i].hist(data[column])
        if i != nr_options - 1:
            ax[i].set_xticklabels([])
        ax[i].text(
            0.5,
            0.25,
            columns[i].split(":")[0] + " (" + str(int(np.sum(counts))) + ")",
            transform=ax[i].transAxes,
        )

    xmin = np.min([ax[i].get_xlim()[0] for i in range(nr_options)])
    xmax = np.max([ax[i].get_xlim()[1] for i in range(nr_options)])
    ymin = np.min([ax[i].get_ylim()[0] for i in range(nr_options)])
    ymax = np.max([ax[i].get_ylim()[1] for i in range(nr_options)])

    for i in range(nr_options):
        ax[i].set_xlim(xmin, xmax)
        ax[i].set_ylim(ymin, ymax)
        ax[i].spines["bottom"].set_color("black")
        ax[i].spines["left"].set_color("black")
        ax[i].tick_params(direction="out", left=True, bottom=True, color="black")

    ax[nr_options - 1].set_xlabel("[%]")
    # set plot title - already handled by outer plot function
    if plot_title:
        ax[0].set_title(plot_title, size=mpl.rcParams["figure.titlesize"])

    return fig, ax

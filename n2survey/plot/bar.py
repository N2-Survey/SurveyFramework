from typing import Dict, Optional, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from .common import label_wrap

__all__ = ["single_choice_bar_plot"]


def single_choice_bar_plot(
    x,
    y,
    theme: Optional[Dict] = None,
    total: Union[int, float, None] = None,
    plot_title: Union[str, bool] = False,
    show_percents: bool = True,
    show_total: bool = True,
    textwrap_x_axis: int = 100,
    max_textwrap_x_axis: int = 200,
    **kwargs,
) -> Tuple[mpl.figure.Figure, mpl.axes.Axes]:
    """Do a bar plot for a single choice question

    Args:
        x ([type]): X values for the bar plot. See `seaborn.barplot`
        y ([type]): Y values for the bar plot. See `seaborn.barplot`
        total (Union[int, float, None], optional): Total number to calculate percentage
          and to show on the figure. By default, sum of Y values is used.
        plot_title (Union[str, bool], optional): Title of the plot.
        show_percents (bool, optional): Show percents on top of boxes. Defaults to True.
        show_total (bool, optional): Show total number on the figure. Defaults to True.
        theme (Optional[Dict], optional): seaborn theme parameters.
          See `seaborn.set_theme` for the details. Defaults to None.

    Returns:
        tuple[mpl.figure.Figure, mpl.axes.Axes]: tuple (fig, ax) of the plot
    """
    # Additional parameters to provide in `sns.barplot`
    additional_params = kwargs.copy()

    if theme is not None:
        sns.set_theme(**theme)

    # HOTFIX: For some reason, setting "palette" in `set_theme`
    # does not apply the palette. To make it work, we have to provide
    # it directly to `barplot` function
    additional_params["palette"] = additional_params.get("palette", None) or theme.get(
        "palette", None
    )

    if total is None:
        total = np.array(y).sum()

    # Prepare figure
    fig, ax = plt.subplots()
    fig_width, _ = fig.get_size_inches()

    # Do the plot
    x = label_wrap(x, textwrap_x_axis, max_textwrap_x_axis)
    sns.barplot(x=x, y=y, ci=None, ax=ax, **additional_params)
    ax.spines["bottom"].set_color("black")
    ax.spines["left"].set_color("black")
    ax.tick_params(axis="x", which="major", pad=-2)
    ax.set_xticks(
        ax.get_xticks() + max(ax.get_xticks()) / 40.0,
        ax.get_xticklabels(),
        color="black",
    )

    # set plot title - already handled by outer plot function
    if plot_title:
        ax.set_title(plot_title)

    # Add percents on top
    if show_percents:
        percents = 100 * np.array(y) / total
        labels = ["{:.0f}%".format(p) for p in percents]
        ax.bar_label(ax.containers[0], labels)

    if show_total:
        plt.text(
            len(y) * 0.9,
            max(y) * 1.1,
            f"Total: {total}",
            size=mpl.rcParams["font.size"],
        )

    # scale
    ax.autoscale()
    ax.set_autoscale_on(True)

    # figure settings
    fig.tight_layout()
    fig.autofmt_xdate()
    plt.xticks(rotation=60)
    return fig, ax

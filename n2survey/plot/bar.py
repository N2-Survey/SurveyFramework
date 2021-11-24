from typing import Dict, Optional, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

__all__ = ["single_choice_bar_plot"]


def single_choice_bar_plot(
    x,
    y,
    total: Union[int, float, None] = None,
    title: Optional[str] = None,
    show_percents: bool = True,
    show_total: bool = True,
    theme: Optional[Dict] = None,
) -> Tuple[mpl.figure.Figure, mpl.axes.Axes]:
    """Do a bar plot for a single choice question

    Args:
        x ([type]): X values for the bar plot. See `seaborn.barplot`
        y ([type]): Y values for the bar plot. See `seaborn.barplot`
        total (Union[int, float, None], optional): Total number to calculate percentage
          and to show on the figure. By default, sum of Y values is used.
        title (Optional[str], optional): Title of the axes. Defaults to None.
        show_percents (bool, optional): Show percents on top of boxes. Defaults to True.
        show_total (bool, optional): Show total number on the figure. Defaults to True.
        theme (Optional[Dict], optional): seaborn theme parameters.
          See `seaborn.set_theme` for the details. Defaults to None.

    Returns:
        tuple[mpl.figure.Figure, mpl.axes.Axes]: tuple (fig, ax) of the plot
    """
    # Additional parameters to provide in `sns.barplot`
    additional_params = {}

    palette = None
    if theme is not None:
        sns.set_theme(**theme)
        palette = theme.get("palette", None)

    # HOTFIX: For some reason, setting "palette" in `set_theme`
    # does not apply the palette. To make it work, we have to provide
    # it directly to `barplot` function
    if palette is not None:
        additional_params = {"palette": palette}

    if total is None:
        total = np.array(y).sum()

    # Prepare figure
    fig, ax = plt.subplots()
    fig_width, _ = fig.get_size_inches()

    # Do the plot
    sns.barplot(x=x, y=y, ci=None, ax=ax, **additional_params)

    # Set title
    if title:
        ax.set_title(title)

    # Add percents on top
    if show_percents:
        percents = 100 * np.array(y) / total
        labels = ["{:.1f}%".format(p) for p in percents]
        ax.bar_label(ax.containers[0], labels)

    if show_total:
        plt.text(
            len(y) * 0.9,
            max(y) * 1.1,
            f"Total: {total}",
            size=fig_width * 1.5,
        )

    # scale
    ax.autoscale()
    ax.set_autoscale_on(True)

    # figure settings
    fig.tight_layout()
    fig.autofmt_xdate()

    return fig, ax

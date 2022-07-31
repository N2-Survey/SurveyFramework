from textwrap import wrap
from typing import Dict, Optional, Tuple

import matplotlib as mpl
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

__all__ = ["comparison_numeric_bar_plot"]


def get_median_and_range(survey, question, responses):
    """Return the median (e.g. 550) and the corresponding range (e.g. 501-600)

    Median calculation and conversion to range works only when there is not averaging
    involved in median calculation, meaning that the number of array elements has to be
    uneven!
    If not, remove the largest element (making the array uneven) before calculation of
    the median. This reproduces the 'correct' result as long as the ranges of the two
    values in the middle of the array are of the same size!

    Even input: ... (501-600) (601-700) ... --> ... (550) (650) ...
    Median:                                 -->        (600)
    Range conversion:     (501-600)         <--

    Args:
        survey (LimeSurvey): LimeSurvey object
        question (str): investigated question, used for selecting data to calculate median.
        responses (DataFrame): unfiltered responses DataFrame

    Returns:
         median (float): Median of the filtered DataFrame
         range (str): Corresponding range needed for specifiying the x-plotting position
    """
    # question-codes for questions that were transformed from range --> numeric
    # median calculation only works for these and the transformation has to be done before
    transformed_questions = {
        "B1b": "noincome_duration",
        "B2": "income_amount",
        "B3": "costs_amount",
        "B4": "contract_duration",
        "B10": "holiday_amount",
        "C4": "hours_amount",
        "C8": "holidaytaken_amount",
    }
    if question in transformed_questions.keys():
        transformed_question = transformed_questions[question]
        transformed_answers = survey.get_responses(transformed_question)
        filtered_transformed_answers = transformed_answers.loc[responses.index]
        # check if at least one valid (non-NaN) value is there
        if np.sum(filtered_transformed_answers.count()) > 0:
            # calculate median depending on the number of non-NaN entries
            if np.sum(filtered_transformed_answers.count()) % 2:  # uneven
                median = np.nanmedian(filtered_transformed_answers)
            else:  # even
                # exclude the highest value to get uneven number of values
                # otherwise median = average of both middle values which
                # cannot be easily reversed back into a range
                index_max = filtered_transformed_answers.idxmax()
                median = np.nanmedian(filtered_transformed_answers.drop(index_max))
            # find corresponding range in original answers, used for plotting
            index, _ = np.where(transformed_answers == median)
            range = survey.get_responses(question).iloc[index[0]][0]
            return median, range
        else:
            return np.nan, np.nan
    else:
        return np.nan, np.nan


def plot_subplot_barplot(
    ax,
    x,
    y,
    survey,
    question,
    responses,
    labels,
    color,
    display_total,
    display_percents,
    display_median,
    percent_threshold,
    y_axis_max,
    **additional_params,
):
    """Plot a single barplot.

    Args:
        ax (mpl.axes.Axes): Axes used for the current subplot.
        x (list): List of indices used as x-axis
        y (pandas Series): Counts of the respective bins.
        survey (LimeSurvey object): LimeSurvey object with all transformed questions.
        question (str): Investigated question, used for selecting data to calculate median.
        responses (pandas DataFrame): DataFrame with all (uncounted) responses.
        labels (str): Current labels for the `responses`, plotted at right top of axes.

        display_percents (bool): Show percents on top of bars. Defaults to False.
        display_total (bool): Show total number on the figure. Defaults to True.
        display_median (bool): Show median of distribution. Defaults to True.
        percent_threshold (int): Threshold for displaying percentages over bars.
        y_axis_max (int): Maximum of y-axis, array-like or the same value for all if int.


    Returns:
        ax (mpl.axes.Axes): Updated axes of the plot
    """
    sns.barplot(x=x, y=y, ci=None, ax=ax, color=color, **additional_params)
    ax.set(ylabel=None)
    # Adjust yscale manually to show highest percentage values
    if y_axis_max is not None:
        ax.set_ylim(0, y_axis_max)
    else:
        ax.set_ylim(0, 1.6 * np.max(y))
    ax.yaxis.get_major_locator().set_params(integer=True)
    total = np.array(y).sum()
    if display_total:
        ax.text(
            1.0,
            1.05,
            f"{labels}: {total}",
            c=color,
            horizontalalignment="right",
            verticalalignment="center",
            transform=ax.transAxes,
        )
    # Add percents on top
    if display_percents:
        percents = 100 * np.array(y) / total
        labels = [
            "{:.1f}%".format(p) if p > percent_threshold else "" for p in percents
        ]
        ax.bar_label(ax.containers[0], labels)
    # Add median as vertical dashed line
    if display_median:
        median, converted_range = get_median_and_range(survey, question, responses)
        if converted_range in np.asarray(x):
            plot_position = np.where(np.asarray(x) == converted_range)[0]
            ax.axvline(x=plot_position, ls="--", c="grey")
            ax.text(
                plot_position + 0.1,
                0.85 * ax.get_ylim()[1],
                f"{converted_range}",
                c="white",
                weight="bold",
                path_effects=[pe.withStroke(linewidth=2, foreground="black")],
            )

    return ax


def comparison_numeric_bar_plot(
    survey,
    question,
    list_of_responses,
    list_of_counts,
    list_of_labels,
    title: str = None,
    fig_size_inches: tuple = None,
    theme: Optional[Dict] = None,
    display_unfiltered_data: bool = True,
    display_percents: bool = False,
    display_total: bool = True,
    display_median: bool = True,
    display_no_answer: bool = True,
    wrap_text: bool = True,
    percent_threshold: int = 5,
    y_axis_max: int or list = None,
) -> Tuple[mpl.figure.Figure, mpl.axes.Axes]:
    """Do multiple bar plots for a numeric single-choice question with multiple filters.

    Args:
        survey (LimeSurvey object): LimeSurvey object with all transformed questions.
        question (str): Investigated question, used for selecting data to calculate median.
        list_of_responses (list): Unfiltered and filtered data.
        list_of_counts (list): Unfiltered and filtered counted data to plot.
        list_of_labels (list): Labels for the entries in `list_of_counts`, plotted at right top of axes.
        title (str, optional): Title of the uppermost axes. Defaults to None.
        fig_size_inches (tuple, optional): Size of the resulting Figure. Defaults to None.
        theme (Optional[Dict], optional): Seaborn theme parameters.
          See `seaborn.set_theme` for the details. Defaults to None.
        display_unfiltered_data (bool, optional): Display distribution of total data (without filtering). Defaults to True.
        display_percents (bool, optional): Show percents on top of bars. Defaults to False.
        display_total (bool, optional): Show total number on the figure. Defaults to True.
        display_median (bool, optional): Show median of distribution. Defaults to True.
        display_no_answer (bool, optional): Show 'No answer' possiblities. Defaults to True.
        wrap_text (bool, optional): Add line breaks to long questions. Defaults to True.
        percent_threshold (int, optional): Threshold for displaying percentages over bars.
        y_axis_max (int or list): Maximum of y-axes, list or the same value for all if int.

    Returns:
        tuple[mpl.figure.Figure, mpl.axes.Axes]: Tuple (fig, ax) of the plot
    """
    # Additional parameters to provide in `sns.barplot`
    additional_params = {}

    # Elements of color `palette` are used for individual subplots
    if theme is not None:
        sns.set_theme(**theme)
        palette_cmap = sns.color_palette(theme.get("palette", None), as_cmap=True)
    else:
        palette_cmap = sns.color_palette(as_cmap=True)

    # Only plot unfiltered data ('Total') as first subplot if specified
    if not display_unfiltered_data:
        list_of_counts = list_of_counts[1:]
        list_of_responses = list_of_responses[1:]
        list_of_labels = list_of_labels[1:]

    # Get a list of colors in line with palette (some palettes are almost white at edges
    # Therefore, do not go from 0-1, but from 0.2-0.8
    list_colors = [palette_cmap(i) for i in np.linspace(0.2, 0.8, len(list_of_counts))]

    # Comparison only done in one figure (max. 9 subplots)
    if len(list_of_counts) > 9:
        raise NotImplementedError(
            "Implementation only supports a maximum of 8 comparisons!"
        )

    # Set figure size according to the number of subplots and x-axis entries
    if fig_size_inches is None:
        fig_size_inches = (len(list_of_counts[0]) / 1.5, 2.0 * len(list_of_counts))

    # Filter out all 'No answer' entries for all dataframes
    if not display_no_answer:
        try:
            for i in range(len(list_of_counts)):
                list_of_counts[i] = list_of_counts[i].drop("No Answer")
        except KeyError:
            pass

    # Prepare figure:
    # Total at top, all other filtered data below
    fig, ax = plt.subplots(len(list_of_counts), 1, sharex=True)
    fig.set_size_inches(fig_size_inches)
    fig_width, _ = fig.get_size_inches()

    if y_axis_max is not None:
        if isinstance(y_axis_max, int):
            y_axis_max = np.ones(len(list_of_counts)) * y_axis_max
        elif isinstance(y_axis_max, list):
            if len(y_axis_max) != len(list_of_counts):
                raise NotImplementedError(
                    "If passing an array to `y_axis_max`, make sure it has the correct "
                    "number of entries, here: {}!".format(len(list_of_counts))
                )
    else:
        y_axis_max = [None] * len(list_of_counts)

    # Do all subplots: unfiltered at top, then all subplots with filtered data
    for i in range(len(list_of_counts)):
        data = list_of_counts[i]
        x = data.iloc[:, 0].index.values.tolist()
        y = data.iloc[:, 0]
        ax[i] = plot_subplot_barplot(
            ax[i],
            x,
            y,
            survey,
            question,
            list_of_responses[i],
            list_of_labels[i],
            list_colors[i],
            display_total,
            display_percents,
            display_median,
            percent_threshold,
            y_axis_max[i],
            **additional_params,
        )
    # Adjustments for the whole figure:
    # Set y-label only for the axis (roughly) in the middle
    ax[int(len(list_of_counts) / 2)].set_ylabel("Number of Responses")

    if wrap_text:
        title = "\n".join(wrap(title, 55))
        tick_labels = ["\n".join(wrap(label, 20)) for label in x]
        ax[-1].set_xticklabels(tick_labels)

    # Set title for uppermost axes
    if title is not None:
        ax[0].set_title(title, pad=20)

    # Figure settings
    fig.tight_layout()
    fig.autofmt_xdate(rotation=55)
    fig.subplots_adjust(top=0.90, hspace=0.3, left=0.15)

    return fig, ax

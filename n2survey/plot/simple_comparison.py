from typing import Dict, Optional, Union

import matplotlib.pyplot as plt
import numpy as np

__all__ = ["simple_comparison_plot"]


def get_percentages(array, threshold=0, answer_supress=False, totalbar=False):
    """
    This function calculates the total number of combinations from the given
    array of answer combinations.
    After that it adds the totalbar, if wanted, then it calculates a dictionary
    with the percentages for each combination+the totalbar if wanted
    """
    # get possible combinations (combi) and count how often they occure (no_of)
    (combi, no_of) = np.unique(array.astype(str), return_counts=True, axis=0)
    # if a totalbar array is calculated in the plot function survey.py
    # it will be appended to the beginning of combi and no_of
    if totalbar:
        total_combi = np.full((totalbar[0].shape[0], 1), "Total")
        total_combi = np.append(
            total_combi, np.reshape(totalbar[0], newshape=(-1, 1)), axis=1
        )
        combi = np.append(total_combi, combi, axis=0)
        no_of = np.append(totalbar[1], no_of)
    # Total values are converted to percentages and packed into a dictionary,
    # which is less confusing then pandas dataframe
    percentage = {}
    for answer in combi[:, 0]:
        answer_rows = np.where(combi[:, 0] == answer)
        percentage[answer] = np.append(
            np.reshape(combi[answer_rows, 1], newshape=(-1, 1)),
            np.reshape(
                np.round(
                    no_of[answer_rows] / sum(no_of[answer_rows]) * 100, decimals=1
                ),
                newshape=(-1, 1),
            ),
            axis=1,
        )
    return percentage


def form_x_and_y(df, totalbar=False, answer_supress=False):
    """
    This Function splits up the dataframe given to it to x and y components
    it applies the get_percentages function to calculate Percentages from
    the compared with Question.
    It also filters out the answers specified by answer_supress.
    If additional answers should be compared this function also splits them up
    for the get_percentages function which only can handle one array, not
    a list of arrays.
    """
    PERCENTAGES = []
    for entry in df:
        PERCENTAGE = get_percentages(entry, totalbar=totalbar)
        totalbar = False
        if answer_supress:
            for answer in answer_supress:
                if answer not in PERCENTAGE:
                    print(f"{answer} does not exist for this question")
                else:
                    PERCENTAGE.pop(answer)
        PERCENTAGES.append(PERCENTAGE.copy())

    x = []
    y = []
    for PERCENTAGE in PERCENTAGES:
        for entry in PERCENTAGE:
            x.append(entry)
            y.append(PERCENTAGE[entry])
    return x, y


def form_bar_positions(df, bar_positions=False, totalbar=False, answer_supress=False):
    """
    forms a complete list of bar positions for all bars, also the not
    specified ones.
    You can specify bar positions in a list, but if you
    want to specify the last bar you have to specify every bar before that,
    Maybe this can be improved for more user friendlieness.
    --> maybe exchange to a bar distance dictionary?
    if dictionary to complex for standard user, maybe list of tuples?
    [('Total',1.5),('Yes', 0.2),] etc.
    with (nameofbar, distance_from_previous_bar)
    At the moment we calculate PERCENTAGE a second time in this function,
    but the slowing of the whole plot function is neglectable due to this.
    """
    # start list of bar_positions
    if bar_positions:
        bar_positions_complete = bar_positions
    else:
        bar_positions_complete = [0]
    COUNT = 0
    BAR_POS_LENGTH = 0
    for entry in df:
        PERCENTAGE = get_percentages(entry, totalbar=totalbar)
        if answer_supress:
            for answer in answer_supress:
                if answer not in PERCENTAGE:
                    print(f"{answer} does not exist for this question")
                else:
                    PERCENTAGE.pop(answer)
        BAR_POS_LENGTH = BAR_POS_LENGTH + len(PERCENTAGE)
        totalbar = False
        if all(
            [COUNT > 0, len(bar_positions_complete) == BAR_POS_LENGTH - len(PERCENTAGE)]
        ):
            bar_positions_complete.append(max(bar_positions_complete) + 1.5)
        while len(bar_positions_complete) < BAR_POS_LENGTH:
            bar_positions_complete.append(max(bar_positions_complete) + 1)
        COUNT = COUNT + 1
    return bar_positions_complete


def simple_comparison_plot(
    df,
    answer_supress: Union[list, bool] = False,
    theme: Optional[Dict] = None,
    titles: Optional[list] = None,
    totalbar=False,
    no_answers=False,
    hide_titles=False,
    bar_positions: Union[list, bool] = False,
    show_percents=True,
    threshold_percentage=0,
    bar_width=0.8,
    legend_columns: int = 2,
    plot_title: Union[str, bool] = False,
):
    """
    plots correlations from the dataframe df with the existing answer
    combinations and applies the given specifications.
    """
    # form x-axis with answers to first question and y-axis with
    # percentages of second question correlated to each answer of the first
    # question.
    (x, y) = form_x_and_y(df, totalbar=totalbar, answer_supress=answer_supress)
    # create a list with positonings of the bars in the plot.
    bar_positions_complete = form_bar_positions(
        df, bar_positions, totalbar=totalbar, answer_supress=answer_supress
    )
    # %% Prepare/Define figure
    fig, ax = plt.subplots()
    fig_width, _ = fig.get_size_inches()
    # %% split up y to list of answers of question 2 and list of percentages
    q2_answers = []
    percentages = []
    for entry in y:
        q2_answers.append(entry[:, 0])
        percentages.append(entry[:, 1].astype(np.float64))
    all_answers = np.unique(np.concatenate(np.array(q2_answers)))
    percentage_all = []
    for (percentage, q2_answer) in zip(percentages, q2_answers):
        count = 0
        percentage_all_single = []
        for answer in all_answers:
            if answer in q2_answer:
                percentage_all_single.append(percentage[count])
                count = count + 1
            else:
                percentage_all_single.append(0)
        percentage_all.append(percentage_all_single.copy())
    # %% plot and format
    bottom = 0
    count = 0
    for answer, percentage in zip(all_answers, np.transpose(np.array(percentage_all))):
        ax.bar(
            bar_positions_complete,
            percentage,
            bottom=bottom,
            label=answer,
            width=bar_width,
        )
        plt.xticks(bar_positions_complete, x)
        bottom = bottom + percentage
        labels = percentage.astype(str)
        labels[np.where(labels.astype(np.float64) <= threshold_percentage)] = ""
        ax.bar_label(ax.containers[count], labels, fmt="%s", label_type="center")
        count = count + 1
    labels = all_answers
    ax.legend(
        labels, bbox_to_anchor=([0.1, 1, 0, 0]), ncol=legend_columns, frameon=False
    )
    ax.axes.get_yaxis().set_visible(False)
    if plot_title:
        ax.set_title(plot_title, pad=60)
    # scale
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="right")
    # figure settings
    fig.tight_layout()
    return fig, ax

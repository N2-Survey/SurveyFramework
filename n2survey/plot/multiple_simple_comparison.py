#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 18:50:01 2022

@author: theflike
"""
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from .comparison_shared_functions import (
    calculate_title_pad,
    filter_answer_sequence,
    form_bar_positions,
    form_single_answer_bar_positions,
    sort_data,
)

__all__ = ["multiple_simple_comparison_plot"]


def multiple_simple_comparison_plot(
    plot_data_list,
    suppress_answers: list = [],
    ignore_no_answer: bool = True,
    totalbar: np.ndarray = None,
    bar_positions: list = [],
    threshold_percentage: float = 0,
    bar_width: float = 0.8,
    legend_columns: int = 2,
    plot_title: Union[str, bool] = False,
    plot_title_position: tuple = (()),
    legend_title: str = None,
    answer_sequence: list = [],
    legend_sequence: list = [],
    theme=None,
):
    """
    Plots correlations between multiple choice answers and the answers of
    simple choice answers.
    """
    if ignore_no_answer:
        suppress_answers.append("I don't know")
        suppress_answers.append("I don't know.")
    # form x and y from plot_data_lists
    (x, y) = form_x_and_y(
        plot_data_list, totalbar=totalbar, suppress_answers=suppress_answers
    )
    print(y)
    # remove answers not in x from answer_sequence
    answer_sequence = filter_answer_sequence(x, answer_sequence)
    # sort x-axis (and of course y-values) by answer sequence
    for entry in y.copy():
        _, y[entry] = sort_data(answer_sequence, x, list(y[entry]))
    x, _ = sort_data(answer_sequence, x, y)
    # remove legend entries not in y
    if totalbar:
        legend_sequence.insert(0, "Total")
    legend_sequence = filter_answer_sequence([entry for entry in y], [legend_sequence])
    # %% Prepare/Define figure
    if theme is not None:
        sns.set_theme(**theme)
    fig, ax = plt.subplots()
    # %% plot
    positionlist_per_answer = form_single_answer_bar_positions(y, bar_width)
    bar_positions_complete = form_bar_positions(
        x, y, bar_width=bar_width, totalbar=totalbar
    )
    fig, ax = plot_multi_bars_per_answer(
        fig,
        ax,
        x,
        y,
        bar_positions_complete,
        positionlist_per_answer,
        legend_sequence=legend_sequence,
        legend_columns=legend_columns,
        plot_title=plot_title,
        legend_title=legend_title,
        plot_title_position=plot_title_position,
    )
    return fig, ax


def plot_multi_bars_per_answer(
    fig,
    ax,
    x,
    y,
    bar_positions,
    positionlist_per_answer,
    legend_sequence,
    legend_columns=2,
    legend_title: str = None,
    plot_title=None,
    plot_title_position: tuple = (()),
):
    for entry, offset_from_xtick in zip(legend_sequence, positionlist_per_answer):
        ax.bar(bar_positions + offset_from_xtick, list(y[entry]), label=entry)
        plt.xticks(bar_positions, x)
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="right")
    ax.legend(
        legend_sequence,
        loc=(0.1, 1),
        ncol=legend_columns,
        frameon=False,
        title=legend_title,
    )
    if plot_title:
        if plot_title_position:
            ax.text(plot_title_position[0], plot_title_position[1], plot_title)
        else:
            ax.set_title(
                plot_title,
                pad=calculate_title_pad(
                    legend_sequence, legend_columns, legend_title=legend_title
                ),
            )
    return fig, ax


def form_x_and_y(array, totalbar=None, suppress_answers=[]):
    """
    Split up the array given to it to x and y components for
    the plot.
    it collects the percentages of the people that answered the 'compare_with'
    question and the correlation with the answers those people gave to the
    main 'question'.
    It filters out the answers specified by suppress_answers.
    """
    percentages_for_comparison = []
    answers = []

    count = 0
    for entry in array:
        answers.append(entry.count().index.values[0:-1].astype(str))
        percentages_for_comparison.append(
            get_percentages(entry.values, totalbar=totalbar)
        )
        for answer in suppress_answers:
            if answer not in answers[count]:
                print(f"{answer} does not exist for this question")
            else:
                remove_index = np.where(answers[count] == answer)[0][0]
                answers[count] = np.delete(answers[count], remove_index)
                for i in percentages_for_comparison[count].copy():
                    percentages_for_comparison[count][i] = np.delete(
                        percentages_for_comparison[count][i], remove_index
                    )
        count = count + 1
    x = answers[0]
    for answer_list in answers[1:]:
        for answer in answer_list:
            x.append(answer)
    y = percentages_for_comparison[0]
    for percentages in percentages_for_comparison[1:]:
        for answer in percentages:
            if answer in y:
                print(f"double answer: {answer}")
                raise NotImplementedError(
                    """
                    only single occurence of answers supported at the moment
                    """
                )
            else:
                y[answer] = percentages[answer]
    # add totalbar if wanted, total is the average of the other percentages for
    # every answer of 'question'
    if totalbar:
        y["Total"] = np.round(sum(y.values()) / len(y), decimals=1)
    return x, y


def get_percentages(array, totalbar=None):
    """
    Calculate the total number of combinations from the given
    array of answer combinations.
    After that it adds the totalbar, if wanted, then it calculates a dictionary
    with the percentages for each combination+the totalbar if wanted
    """
    # get possible combinations (combi) and count how often they occure (no_of)
    percentage = {}
    for entry in np.unique(array[:, -1]):
        entry_subset = array[np.where(array[:, -1] == entry)][:, :-1]
        total = entry_subset.shape[0]
        calculated_percentages = np.round(
            np.count_nonzero(entry_subset, axis=0) / total * 100, decimals=1
        )
        if not np.all((calculated_percentages == 0)):
            percentage[entry] = calculated_percentages

    return percentage

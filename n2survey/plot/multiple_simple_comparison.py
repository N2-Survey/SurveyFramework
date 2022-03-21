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
    # form x and y from plot_data_lists
    (x, y) = form_x_and_y(
        plot_data_list, totalbar=totalbar, suppress_answers=suppress_answers
    )
    # %% Prepare/Define figure
    if theme is not None:
        sns.set_theme(**theme)
    fig, ax = plt.subplots()
    # %% plot
    bar_width = 0.8
    positionlist_per_answer = form_single_answer_bar_positions(y, bar_width)
    bar_positions = np.arange(len(x))
    # bar_positions_complete = form_bar_positions(
    #   plot_data_list,
    #  bar_positions,
    # totalbar=totalbar,
    # suppress_answers=suppress_answers,
    # )
    fig, ax = plot_multi_bars_per_answer(
        fig, ax, x, y, bar_positions, positionlist_per_answer
    )
    return fig, ax


def plot_multi_bars_per_answer(fig, ax, x, y, bar_positions, positionlist_per_answer):
    for entry, offset_from_xtick in zip(y, positionlist_per_answer):
        ax.bar(bar_positions + offset_from_xtick, list(y[entry]), label=entry)
        plt.xticks(bar_positions, x)
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="right")
    return fig, ax


def form_single_answer_bar_positions(y, bar_width):
    """
    calculates the offset of multiple bars given in dictionary 'y'
    to a single x-position, depending on 'bar_width'
    """
    number_of_bars = len(y)
    space_per_answer = bar_width * number_of_bars
    bar_positions_per_answer = np.arange(
        -space_per_answer / 2 + 0.5 * bar_width, space_per_answer / 2, bar_width
    )
    print(bar_positions_per_answer)
    return bar_positions_per_answer


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

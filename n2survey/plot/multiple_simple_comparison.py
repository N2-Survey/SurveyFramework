#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 18:50:01 2022

@author: theflike
"""
from typing import Union

import numpy as np

__all__ = ["multiple_simple_comparison_plot"]


def multiple_simple_comparison_plot(
    plot_data_list,
    suppress_answers: list = [],
    ignore_no_answer: bool = True,
    totalbar: np.ndarray = None,
    bar_positions: Union[list, bool] = False,
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
    print(answer_sequence[0])
    total_participants = plot_data_list[0].shape[0]
    (x, y) = form_x_and_y(
        plot_data_list, totalbar=totalbar, suppress_answers=suppress_answers
    )
    brakk
    return True


def form_x_and_y(array, totalbar=None, suppress_answers=[]):
    """
    Split up the array given to it to x and y components for
    the plot.
    it collects the percentages of the people that answered the 'compare_with'
    question and the correlation with the answers those people gave to the
    main 'question'.
    It filters out the answers specified by suppress_answers.
    """
    x = []
    percentages_for_comparison = []
    for entry in array:
        x.append(np.array(entry.columns))
        percentages_for_comparison.append(
            get_percentages(entry.values, totalbar=totalbar)
        )
    print(x)
    print(percentages_for_comparison)
    print(percentages_for_comparison[0]["Woman"])
    brakk
    for answer in suppress_answers:
        if answer not in percentage_correlated_answers:
            print(f"{answer} does not exist for this question")
        else:
            percentage_correlated_answers.pop(answer)
    percentages_for_comparison.append(percentage_correlated_answers.copy())

    x = []
    y = []
    for percentage_correlated_answers in percentages_for_comparison:
        for entry in percentage_correlated_answers:
            x.append(entry)
            y.append(percentage_correlated_answers[entry])
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
        percentage[entry] = np.round(
            np.count_nonzero(entry_subset, axis=0) / total * 100, decimals=1
        )

    return percentage

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
    # print(answer_sequence)
    (x, y) = form_x_and_y(
        plot_data_list, totalbar=totalbar, suppress_answers=suppress_answers
    )
    # %% Prepare/Define figure
    if theme is not None:
        sns.set_theme(**theme)
    fig, ax = plt.subplots()
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
    percentages_for_comparison = []
    answers = []
    count = 0
    for entry in array:
        answers.append(entry.count().index.values.astype(str))
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
                brakk

        count = count + 1
    print(x)
    brakk
    print(percentages_for_comparison)
    print(percentages_for_comparison[0]["Woman"])
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

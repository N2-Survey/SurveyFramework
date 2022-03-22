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
    aspect_ratio_from_arguments,
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
    calculate_aspect_ratio: bool = True,
    remove_unchosen_answers: bool = True,
):
    print(theme)
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
    # %% Prepare/Define figure and calculate dimensions
    positionlist_per_answer = form_single_answer_bar_positions(y, bar_width)
    bar_positions_complete = form_bar_positions(
        x, y, bar_width=bar_width, totalbar=totalbar
    )
    # %%% calculate dimensions of figure
    if theme is not None:
        if calculate_aspect_ratio:
            width = aspect_ratio_from_arguments(
                bar_positions_complete, positionlist_per_answer, theme, bar_width
            )
            height = theme["rc"]["figure.figsize"][1]
        else:
            width, height = theme["rc"]["figure.figsize"]
        theme["rc"]["figure.figsize"] = (width, height)
        sns.set_theme(**theme)
    fig, ax = plt.subplots()
    fig.set_tight_layout(True)
    # %% plot

    fig, ax = plot_multi_bars_per_answer(
        fig,
        ax,
        x,
        y,
        bar_positions_complete,
        positionlist_per_answer,
        legend_sequence,
        legend_columns=legend_columns,
        plot_title=plot_title,
        legend_title=legend_title,
        plot_title_position=plot_title_position,
        threshold_percentage=threshold_percentage,
        bar_width=bar_width,
    )
    # enlarge y-axis maximum due to bar labels
    new_y_axis_size = 1.05 * ax.get_ylim()[1]
    if theme is not None:
        new_y_axis_size = new_y_axis_size * theme["font_scale"]
    ax.set_ylim(top=new_y_axis_size)
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
    threshold_percentage: float = 0,
    bar_width: float = 0.8,
):
    count = 0
    for entry, offset_from_xtick in zip(legend_sequence, positionlist_per_answer):
        ax.bar(
            bar_positions + offset_from_xtick,
            list(y[entry]),
            label=entry,
            width=bar_width,
        )
        plt.xticks(bar_positions, x)
        labels = np.array(y[entry]).astype(str)
        labels[np.where(labels.astype(np.float64) <= threshold_percentage)] = ""
        ax.bar_label(
            ax.containers[count],
            labels,
            fmt="%s",
            label_type="edge",
            rotation=90,
            padding=2,
        )
        count = count + 1
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="right")
    ax.legend(
        legend_sequence,
        loc=(0.1, 1),
        ncol=legend_columns,
        frameon=False,
        title=legend_title,
    )
    # set y-axis to invisible
    ax.axes.get_yaxis().set_visible(False)
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
    fig.tight_layout()
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
    return x, y


def get_percentages(array, totalbar=None):
    """
    Calculate the total number of combinations from the given
    array of answer combinations.
    After that it adds the totalbar, if wanted, then it calculates a dictionary
    with the percentages for each combination+the totalbar if wanted
    """
    # get possible combinations and count how often they occure
    percentage = {}
    for entry in np.unique(array[:, -1]):
        entry_subset = array[np.where(array[:, -1] == entry)][:, :-1]
        total = entry_subset.shape[0]
        calculated_percentages = np.round(
            np.count_nonzero(entry_subset, axis=0) / total * 100, decimals=1
        )
        if not np.all((calculated_percentages == 0)):
            percentage[entry] = calculated_percentages
    if totalbar:
        total_participants = len(array)
        total_question_answers = np.round(
            np.count_nonzero(array[:, :-1], axis=0) / total_participants * 100,
            decimals=1,
        )
        percentage["Total"] = total_question_answers
        totalbar = False
    return percentage

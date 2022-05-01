#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 18:50:01 2022

@author: theflike
"""
from textwrap import wrap
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
    plot_bubbles,
    sort_data,
)

__all__ = ["multiple_multiple_comparison_plot"]


def multiple_multiple_comparison_plot(
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
    maximum_length_x_axis_answers=20,
    show_zeroes: bool = True,
    bubbles: Union[bool, float] = None,
):
    """
    Plots correlations between multiple choice answers and the answers of
    simple choice answers.
    """
    no_sub_bars = None
    if bubbles:
        no_sub_bars = True
    if ignore_no_answer:
        suppress_answers.append("No Answer")
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
    # wrap text in x-axis
    x = ["\n".join(wrap(entry, width=maximum_length_x_axis_answers)) for entry in x]
    max_lines = max([entry.count("\n") for entry in x])
    # remove legend entries not in y
    if totalbar:
        legend_sequence.insert(0, "Total")
    legend_sequence = filter_answer_sequence([entry for entry in y], [legend_sequence])

    # %% Prepare/Define figure
    if bubbles:
        positionlist_per_answer = [0]
    else:
        positionlist_per_answer = form_single_answer_bar_positions(
            y, bar_width, bar_positions_per_answer=bar_positions
        )
    bar_positions_complete = form_bar_positions(
        x,
        y,
        bar_width=bar_width,
        totalbar=totalbar,
        distance_between_bars=2,
        positionlist_per_answer=list(positionlist_per_answer),
        no_sub_bars=no_sub_bars,
    )
    # plt.rc('text', usetex=True) --> makes cm-super necessary for latex in plots
    # %%% calculate dimensions of figure
    if theme is not None:
        if calculate_aspect_ratio:
            width = aspect_ratio_from_arguments(
                bar_positions_complete,
                positionlist_per_answer,
                theme,
                bar_width,
                max_lines_xtick=max_lines,
            )
            height = theme["rc"]["figure.figsize"][1]
        else:
            width, height = theme["rc"]["figure.figsize"]
        theme["rc"]["figure.figsize"] = (width, height)
        sns.set_theme(**theme)
    fig, ax = plt.subplots()
    fig.set_tight_layout(True)
    # %% plot
    if bubbles:
        fig, ax = plot_bubbles(
            fig,
            ax,
            x,
            y,
            bar_positions_complete,
            positionlist_per_answer,
            legend_sequence,
            theme=theme,
            legend_columns=legend_columns,
            plot_title=plot_title,
            legend_title=legend_title,
            plot_title_position=plot_title_position,
            threshold_percentage=threshold_percentage,
            bar_width=bar_width,
            show_zeroes=show_zeroes,
            bubbles=bubbles,
        )
    else:
        fig, ax = plot_multi_bars_per_answer(
            fig,
            ax,
            x,
            y,
            bar_positions_complete,
            positionlist_per_answer,
            legend_sequence,
            theme=theme,
            legend_columns=legend_columns,
            plot_title=plot_title,
            legend_title=legend_title,
            plot_title_position=plot_title_position,
            threshold_percentage=threshold_percentage,
            bar_width=bar_width,
            show_zeroes=show_zeroes,
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
    theme=None,
    legend_columns=2,
    legend_title: str = None,
    plot_title=None,
    plot_title_position: tuple = (()),
    threshold_percentage: float = 0,
    bar_width: float = 0.8,
    show_zeroes: bool = True,
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
        label_values = (np.array(y[entry])).astype(str)
        labels = np.array([i + "%" for i in label_values], dtype=object)
        labels[np.where(label_values.astype(np.float64) <= threshold_percentage)] = ""
        labels[np.where(label_values.astype(np.float64) == 100.0)] = "100%"
        if show_zeroes:
            labels[np.where(label_values.astype(np.float64) == 0)] = r"|"
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
                    legend_sequence,
                    legend_columns,
                    theme=theme,
                    legend_title=legend_title,
                ),
            )
    fig.tight_layout()
    return fig, ax


def form_x_and_y(plot_data_list, totalbar=None, suppress_answers=[]):
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
    for question_compare_with_tuple in plot_data_list:
        answers.append(question_compare_with_tuple[0].count().index.values.astype(str))

        percentages_for_comparison.append(
            get_percentages(question_compare_with_tuple, totalbar=totalbar)
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


def get_percentages(question_compare_with_tuple, totalbar=None):
    """
    Calculate the total number of combinations from the given
    array of answer combinations.
    After that it adds the totalbar, if wanted, then it calculates a dictionary
    with the percentages for each combination+the totalbar if wanted
    """
    # translate the dataframes of the two questions
    question_results = question_compare_with_tuple[0]
    question_answers = question_results.count().index.values
    compare_with_results = question_compare_with_tuple[1]
    compare_with_answers = compare_with_results.count().index.values
    persons_total = question_answers.shape[0]
    percentage = {}
    for answer in compare_with_answers:
        percentage[answer] = np.zeros(shape=question_answers.shape)
    for answer in compare_with_answers:
        # define total number of people who answered zutreffend (=True) for this
        # answer to compare_with
        answered_zutreffend = 0
        # cycle through all participants that gave an answer to compare_with answer
        for person_id in compare_with_results.index:
            if compare_with_results.loc[person_id, answer]:
                # if person with id ´person_id´ chose zutreffend (=True) for
                # ´answer´ to ´compare_with´:
                # add one for each answer to ´question´ which they chose also
                # zutreffend (=True)
                percentage[answer] = percentage[answer] + question_results.loc[
                    person_id, :
                ].values.astype("float64")
                # and add 1 to the total number of people that chose
                # zutreffend (=True) for ´answer´ to ´compare_with´.
                answered_zutreffend = answered_zutreffend + 1
        if answered_zutreffend != 0:
            percentage[answer] = np.round(
                (percentage[answer] / answered_zutreffend * 100), decimals=1
            )
    if totalbar:
        percentage["Total"] = np.round(
            np.count_nonzero(question_results, axis=0) / persons_total * 100,
            decimals=1,
        )
        totalbar = False
    return percentage

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 18:50:01 2022

@author: TheFlike
"""
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from .common import (
    aspect_ratio_from_arguments,
    calculate_title_pad,
    filter_answer_sequence,
    form_bar_positions,
    form_single_answer_bar_positions,
    label_wrap,
    plot_bubbles,
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
    show_zeroes: bool = True,
    bubbles: Union[bool, float] = None,
    textwrap_x_axis: int = 100,
    max_textwrap_x_axis: int = 200,
    textwrap_legend: int = 100,
    max_textwrap_legend: int = 200,
    **kwargs,
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
    x, y, total_cnts = form_x_and_y(
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

    # wrap text in x-axis and, if bubbleplot, also text in y-axis
    x = label_wrap(x, textwrap_x_axis, max_textwrap_x_axis)
    max_lines_x = max([entry.count("\n") for entry in x]) + 1

    if bubbles:
        # can be added to a changeable variable, but I don't think it is
        # necessary for the moment.
        maximum_length_y_axis_answers = max_textwrap_x_axis
        y_bubble_plot = label_wrap(legend_sequence, maximum_length_y_axis_answers)
        max_lines_y = max([entry.count("\n") for entry in y_bubble_plot]) + 1
    else:
        max_lines_y = 3

    # %%
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
        distance_between_bars=2.5,
        positionlist_per_answer=list(positionlist_per_answer),
        no_sub_bars=no_sub_bars,
    )
    # plt.rc('text', usetex=True) --> makes cm-super necessary for latex in plots
    # %%% calculate dimensions of figure
    if theme is not None:
        if calculate_aspect_ratio:
            width, height = aspect_ratio_from_arguments(
                bar_positions_complete,
                positionlist_per_answer,
                theme,
                bar_width,
                max_lines_xtick=max_lines_x,
                max_lines_ytick=max_lines_y,
            )
            if not bubbles:
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
            total_cnts,
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
            textwrap_legend=textwrap_legend,
            max_textwrap_legend=max_textwrap_legend,
            **kwargs,
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
    total_cnts,
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
    textwrap_legend: int = 100,
    max_textwrap_legend: int = 200,
    **kwargs,
):
    count = 0
    for entry, offset_from_xtick in zip(legend_sequence, positionlist_per_answer):
        ax.bar(
            bar_positions + offset_from_xtick,
            list(y[entry]),
            label=entry,
            width=bar_width,
        )
        plt.xticks(np.array(bar_positions) + len(bar_positions) / 20.0, x)
        labels = np.array(["{:.0f}%".format(p) for p in np.array(y[entry])])
        labels[np.array(y[entry]) <= threshold_percentage] = ""

        if show_zeroes:
            labels[np.where(np.array(y[entry]) == 0)] = r"|"
        ax.bar_label(
            ax.containers[count],
            labels,
            fmt="%s",
            label_type="edge",
            rotation=90,
            padding=3,
        )
        count = count + 1
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="right")
    legend_sequence = [
        lst + " (" + str(total_cnts[lst]) + ")" for lst in legend_sequence
    ]
    legend_sequence = label_wrap(legend_sequence, textwrap_legend, max_textwrap_legend)
    ax.legend(
        legend_sequence,
        bbox_to_anchor=(kwargs.get("bbox_to_anchor", [0.1, 1, 0, 0])),
        loc=kwargs.get("loc", "upper center"),
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
    plt.xticks(rotation=60)
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
        percent_tmp, total_cnts = get_percentages(
            question_compare_with_tuple, totalbar=totalbar
        )
        percentages_for_comparison.append(percent_tmp)
        for answer in suppress_answers:
            # if answer not in answers[count]:
            # print(f"{answer} does not exist for this question")
            #    no_exist = True
            if answer in answers[count]:
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
    return x, y, total_cnts


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
    compare_with_answers = np.unique(compare_with_results.loc[:])
    total_participants = len(question_results)
    # count number of yes answers of every answer to compare_with_question
    persons_total_answered_yes = {}
    for question_answer in question_answers:
        persons_total_answered_yes[question_answer] = np.sum(
            question_results.loc[:, question_answer]
        )
    percentage = {}
    total_cnts = {}
    for entry in compare_with_answers:
        percentage[entry] = []
    for compare_with_answer in compare_with_answers:
        # translate simple choice to bool array, depending on compare_with_answer
        compare_with_bool_array = np.zeros(shape=(total_participants,)).astype(bool)
        compare_with_bool_array[
            np.where(compare_with_results.values[:, 0] == compare_with_answer)
        ] = True
        # count participants that answered both, compare_with_answer and
        # question answer, with yes
        for question_answer in question_answers:
            single_percentage = np.sum(
                compare_with_bool_array.astype(float)
                * question_results.loc[:, question_answer].astype(float)
            )
            # convert to percent and round
            if persons_total_answered_yes[question_answer]:
                single_percentage = np.round(
                    (100 * single_percentage / np.sum(compare_with_bool_array)),
                    decimals=1,
                )
            percentage[compare_with_answer].append(single_percentage)
            total_cnts[compare_with_answer] = np.sum(compare_with_bool_array)
    if totalbar:
        percentage["Total"] = np.round(
            np.count_nonzero(question_results, axis=0) / total_participants * 100,
            decimals=1,
        )
        totalbar = False
        total_cnts["Total"] = total_participants
    return percentage, total_cnts

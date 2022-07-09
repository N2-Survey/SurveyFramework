#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 21:28:19 2022

@author: theflike
"""
from textwrap import wrap
from typing import Union

import matplotlib.pyplot as plt
import numpy as np

__all__ = [
    "sort_data",
    "form_bar_positions",
    "form_single_answer_bar_positions",
    "filter_answer_sequence",
    "calculate_title_pad",
    "aspect_ratio_from_arguments",
    "plot_bubbles",
]


def plot_bubbles(
    fig,
    ax,
    x,
    y,
    bar_positions,
    positionlist_per_answer,
    legend_sequence,
    maximum_length_y_axis_answers: int = 20,
    theme=None,
    legend_columns=2,
    legend_title: str = None,
    plot_title=None,
    plot_title_position: tuple = (()),
    threshold_percentage: float = 0,
    bar_width: float = 0.8,
    show_zeroes: bool = True,
    bubbles: Union[bool, float] = None,
    ylim: tuple = None,
):
    compare_with_answer_positions = list(range(1, len(legend_sequence) + 1))
    if ylim:
        plt.ylim(ylim)
    else:
        plt.ylim(0, (compare_with_answer_positions[-1] + 1))
    if type(bubbles) == bool:
        bubble_size = calculate_bubblesize()
    else:
        bubble_size = bubbles
    for entry in legend_sequence:
        x_scatter = bar_positions
        y_scatter = [compare_with_answer_positions[legend_sequence.index(entry)]] * len(
            x_scatter
        )
        z_scatter = y[entry]
        ax.scatter(
            x_scatter,
            y_scatter,
            s=list(np.array(z_scatter) * bubble_size),
        )
        plt.xticks(bar_positions, x)
        # collect and wrap up y_axis entries
        compare_with_answers = [
            "\n".join(wrap(entry, width=maximum_length_y_axis_answers))
            for entry in legend_sequence
        ]
        plt.yticks(compare_with_answer_positions, compare_with_answers)
        label_values = (np.array(y[entry])).astype(str)
        labels = np.array([i + "%" for i in label_values], dtype=object)
        labels[np.where(label_values.astype(np.float64) <= threshold_percentage)] = ""
        labels[np.where(label_values.astype(np.float64) == 100.0)] = "100%"
        if show_zeroes:
            labels[np.where(label_values.astype(np.float64) == 0)] = r"o"
        for label, x_pos, y_pos in zip(labels, x_scatter, y_scatter):
            ax.annotate(label, (x_pos, y_pos), ha="center", va="center")
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="right")
    plt.setp(ax.get_yticklabels(), rotation=30, horizontalalignment="right")
    if plot_title:
        if plot_title_position:
            ax.text(plot_title_position[0], plot_title_position[1], plot_title)
        else:
            ax.set_title(plot_title)
    if legend_title:
        plt.ylabel(legend_title)
    fig.tight_layout()
    return fig, ax


def calculate_bubblesize():
    raise NotImplementedError(
        "Calculating bubble-size not yet implemented\n"
        "Please set bubbles=float where float is the wished bubblesize,\n"
        "reasonable bubblesize would be 100"
    )
    return True


def aspect_ratio_from_arguments(
    bar_positions_complete,
    positionlist_per_answer,
    theme,
    bar_width,
    answer_distance: float = None,
    bar_distance: float = None,
    bubble_size: float = None,
    max_lines_xtick: float = 3,
    max_lines_ytick: float = 3,
):
    """
    calculates the width of the plot, depending on total number of bars,
    distance between group of bars, bar thickness etc.
    """
    distance_between_answers = answer_distance or (0.5 * bar_width)
    distance_between_bars = bar_distance or (0.25 * bar_width)
    space_nedded_for_x_ticks = (
        len(bar_positions_complete) * max_lines_xtick * 0.5 * theme["font_scale"]
    )
    space_needed_for_y_ticks = (
        len(bar_positions_complete) * max_lines_ytick * 0.5 * theme["font_scale"]
    )
    width = (
        len(bar_positions_complete) * len(positionlist_per_answer) * bar_width
        + distance_between_answers * len(bar_positions_complete)
        + distance_between_bars * len(positionlist_per_answer)
    ) * 0.4
    if theme["font_scale"] > bar_width:
        width = width / bar_width * 0.8 * theme["font_scale"]
    if width < space_nedded_for_x_ticks:
        print("x_ticks need more space")
        width = space_nedded_for_x_ticks
    height = space_needed_for_y_ticks

    return width, height


def calculate_title_pad(labels, legend_columns, theme=None, legend_title: str = None):
    """
    calculates the height of the title above the plot depending on number
    of legend entries and number of columns that are reserved for the legend.
    """
    pad = int(len(labels) / legend_columns) * 20 + 20
    if legend_title:
        pad = pad + 20
    if theme:
        pad = pad * theme["font_scale"]
    return pad


def filter_answer_sequence(x, answer_sequence):
    """
    Remove answers from sequence that were supressed while creating x
    """
    all_answer_sequence = []
    for answer_list in answer_sequence:
        all_answer_list = answer_list.copy()
        for answer in answer_list:
            if answer not in x:
                all_answer_list.remove(answer)
        for answer in all_answer_list:
            all_answer_sequence.append(answer)
    return all_answer_sequence


def sort_data(sequence, x, y):
    """
    Sort lists x and y by comparing x and list sequence by rearranging x and y
    simoultaneously until x == sequence --> all entries in sequence have to
    also be in x
    at the moment each answer can only occure once in the plot, so if
    you want to add questions it is necessary to supress e.g. the 'no_answer'
    answer, else it would give an error. Can be improved in future.
    """
    indices = []
    for x_entry in x:
        if np.where(np.array(sequence) == x_entry)[0].shape[0] == 1:
            position = sequence.index(x_entry)
            indices.append(position)
        else:
            print(f"double bar: {x_entry}")
            raise NotImplementedError(
                """
                only single occurence of bars supported at the moment
                """
            )
    x_sorted = [entry for _, entry in sorted(zip(indices, x))]
    y_sorted = [entry for _, entry in sorted(zip(indices, y))]
    return x_sorted, y_sorted


def form_bar_positions(
    x,
    y,
    positionlist_per_answer: list = [0],
    bar_width: float = 0.8,
    totalbar: bool = False,
    bar_positions: list = [],
    additional_question_start_indizes: list = [],
    distance_between_bars: float = None,
    no_sub_bars: bool = None,
):
    bar_positions_complete = bar_positions or [0]
    if no_sub_bars:
        number_bars_per_answer = 1
    else:
        number_bars_per_answer = len(y)
    space_per_answer = max(positionlist_per_answer) - min(positionlist_per_answer)
    if not distance_between_bars:
        distance_between_bars = 1.5 * space_per_answer / number_bars_per_answer
    while len(bar_positions_complete) < len(x):
        bar_positions_complete.append(
            (max(bar_positions_complete) + distance_between_bars + space_per_answer)
        )
    return bar_positions_complete


def form_single_answer_bar_positions(y, bar_width, bar_positions_per_answer: list = []):
    """
    calculates the offset of multiple bars given in dictionary 'y'
    to a single x-position, depending on 'bar_width'
    """
    number_of_bars = len(y)
    space_per_answer = bar_width * number_of_bars
    if bar_positions_per_answer:
        while len(bar_positions_per_answer) < number_of_bars:
            bar_positions_per_answer.append(bar_positions_per_answer[-1] + bar_width)
        bar_positions_per_answer = np.array(bar_positions_per_answer)

    else:
        bar_positions_per_answer = np.arange(
            -space_per_answer / 2 + 0.5 * bar_width, space_per_answer / 2, bar_width
        )
    return bar_positions_per_answer

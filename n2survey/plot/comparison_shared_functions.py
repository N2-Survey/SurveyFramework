#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 21:28:19 2022

@author: theflike
"""
import numpy as np

__all__ = ["sort_data"]


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

from typing import Dict, Optional, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import seaborn as sns

__all__ = ["simple_comparison_plot"]

def calculate_barwidth(xs, bar_width):
    # necessary for same barwidth for all plots
    bar_width_correct = []
    for xrow in xs:
        no_bars_row = np.array([])
        total = 0
        for x in xrow:
            no_bars_row = np.append(no_bars_row, len(x))
            total = total+len(x)
        bar_width_correct.append(list(np.round(no_bars_row*bar_width/total,
                                               decimals=2)))
    return bar_width_correct

def calculate_subplot_width(xs, fig_width):
    subplot_widths = []
    for xrow in xs:
        no_bars_row = np.array([])
        total = 0
        for x in xrow:
            no_bars_row = np.append(no_bars_row, len(x))
            total = total+len(x)
        subplot_widths.append(list(np.round(no_bars_row*fig_width/total,
                                               decimals=2)))
    return subplot_widths

def get_percentages(array, threshold=0, answer_supress = False):
    (combi, 
     no_of) = np.unique(array.astype(str), return_counts = True, axis=0)
    # calculate percentages of x
    percentage = {}
    for answer in combi[:,0]:
        answer_rows = np.where(combi[:,0] == answer)
        percentage[answer] = np.append(
            np.reshape(combi[answer_rows, 1], newshape = (-1,1)),
            np.reshape(
                np.round(no_of[answer_rows]/sum(no_of[answer_rows])*100, 
                         decimals=1), newshape = (-1,1)
                ), axis=1
            )
    percentage = pd.DataFrame.from_dict(percentage,
                                           orient='index'
                                           )
    return percentage
    
def form_xs_and_ys(data_dfs):
    xs = []
    ys = []
    rowcount = 0
    for row in data_dfs:
        xrow = []
        yrow = []
        for entry in row:
            if type(entry) == np.ndarray:
                percentage_df = get_percentages(entry)
                xrow.append(list(percentage_df.index.values))
                yrow.append(pd.Series(percentage_df.iloc[:,0]))
            else:
                xrow.append(list(entry.index.values))
                yrow.append(list(entry.iloc[:,0].values))
        xs.append(xrow.copy())
        ys.append(yrow.copy())
        rowcount = rowcount+1
    return xs, ys

def simple_comparison_plot(data_dfs,
                           dimensions = False,
                           answer_supress = False,
                           theme: Optional[Dict] = None,
                           titles: Optional[list] = None,
                           totalbar = False,
                           no_answers = False,
                           hide_titles = False,
                           spacing_bar = False,
                           show_percents = True,
                           threshold = 0,
                           bar_width = 1
                           ):
    (xs,ys) = form_xs_and_ys(data_dfs)
    bar_width = calculate_barwidth(xs, bar_width)
    # %% additional parameters from bar.py
    # Additional parameters to provide in `sns.barplot`
    additional_params = {}

    palette = None
    if theme is not None:
        sns.set_theme(**theme)
        palette = theme.get("palette", None)

    # HOTFIX: For some reason, setting "palette" in `set_theme`
    # does not apply the palette. To make it work, we have to provide
    # it directly to `barplot` function
    if palette is not None:
        additional_params = {"palette": palette}
        
    # %% dimensions of plot
    if dimensions:
        (width,height) = dimensions
    else:
        width = len(xs[0])*8
        height = len(xs)*9
        
    # %% create figure
    
    fig = plt.figure()
    fig.set_size_inches(width,height)
    
    # %% plotting
    position = 1
    for xrow,yrow,width_row in zip(xs,ys, bar_width):
        for (x, y, width) in zip(xrow, yrow, width_row):
            # add subplot and specify positon where to plot
            ax = fig.add_subplot(
                len(xs), len(xrow),
                position
                )
            # plot normal bar plot
            if type(y) == list:
                sns.barplot(x=x, y=y, ci=None, ax=ax, **additional_params)
            # plot combined comparison plot
            else:
                # unpack pandas dataframe to usefull variables 
                q2_answers = []
                percentages = []
                for entry in y.values:
                    q2_answers.append(entry[:,0])
                    percentages.append(entry[:,1].astype(np.float64))
                all_answers = np.unique(np.concatenate(np.array(q2_answers)))
                percentage_all = []
                for (percentage,
                     q2_answer) in zip(percentages, q2_answers):
                    count=0
                    percentage_all_single = []
                    for answer in all_answers:
                        if answer in q2_answer:
                            percentage_all_single.append(percentage[count])
                            count = count+1
                        else:
                            percentage_all_single.append(0)
                    percentage_all.append(percentage_all_single.copy())
                # plot comparison bars
                bottom = 0
                count=0
                for answer,percentage in zip(all_answers, np.transpose(np.array(percentage_all))):
                    ax.bar(x, percentage, bottom=bottom, label=answer,
                           width=width)
                    bottom = bottom + percentage
                    labels = percentage.astype(str)
                    labels[np.where(labels.astype(np.float64) <= threshold)]=''
                    ax.bar_label(ax.containers[count], labels, fmt='%s',
                                 label_type='center')
                    count = count+1
                labels = all_answers
                plt.legend(labels, bbox_to_anchor=([0.1, 1, 0, 0]), ncol=2,
                           frameon=False)
            # scale
            plt.setp(ax.get_xticklabels(), rotation=30,
                     horizontalalignment='right')
            position = position+1
            print(ax.figure.subplotpars.left)
    # figure settings
    fig.tight_layout()
    return fig, ax
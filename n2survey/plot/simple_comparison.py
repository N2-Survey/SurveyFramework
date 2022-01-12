from typing import Dict, Optional, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import seaborn as sns

__all__ = ["simple_comparison_plot"]


def get_percentages(array):
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
        # calculate barheights for overlapping bars
        barheight = np.array([percentage[answer][0,1]]).astype(np.float64)
        count = 0
        for entry in percentage[answer][1:,1].astype(np.float64):
            barheight = np.append(barheight,
                                  barheight[count]+entry)
            count = count+1
        percentage[answer] = np.append(percentage[answer],
                                       np.reshape(barheight, newshape=(-1, 1)),
                                       axis=1)
        percentage = pd.DataFrame.from_dict(percentage,
            orient='index'
                     )
        return percentage
    
def form_xs_and_ys(data_dfs):
    xs = []
    ys = []
    for row in data_dfs:
        xrow = []
        yrow = []
        for entry in row:
            if type(entry) == np.ndarray:
                percentage = get_percentages(entry)
                xrow.append(percentage.index.values)
                yrow.append(pd.Series(percentage.iloc[:,0]))
            else:
                xrow.append(list(entry.index.values))
                yrow.append(list(entry.iloc[:,0].values))
        xs.append(xrow.copy())
        ys.append(yrow.copy())
    return xs, ys

def simple_comparison_plot(data_dfs,
                           dimensions = False,
                           answer_supress = False,
                           theme: Optional[Dict] = None,
                           titles: Optional[list] = None,
                           totalbar = False,
                           no_answers = False,
                           hide_titles = False,
                           spacing_bar = False
                           ):
    (xs,ys) = form_xs_and_ys(data_dfs)
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
    
    for xrow,yrow in zip(xs,ys):
        print(len(xs))
        print(len(ys))
        for (x,y) in zip(xrow,yrow):
            ax = fig.add_subplot(
                len(xs), len(xrow), (xs.index(xrow)+1+xrow.index(x)*len(xs))
                )
            sns.barplot(x=x, y=y, ci=None, ax=ax, **additional_params)
            # scale
            #ax.autoscale()
            #ax.set_autoscale_on(True)
            plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')
            

    # figure settings
    fig.tight_layout()
    return fig, ax
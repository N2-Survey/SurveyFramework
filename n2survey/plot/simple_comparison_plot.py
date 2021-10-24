import warnings
from typing import List, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

# sys.path.insert(0, "/N2_Survey/SurveyFramework/n2survey/lime")

warnings.filterwarnings("error")


"""
NOTICE:
    all content between the two dash line "---" below,
    can be moved to structure or what ever pre-processing part.
    and some examples are provided under the test directory.
    good luck, dron.
"""


# -------------------------------------------------------------------------------------------------------------
def prepare_df(
    file: str,
    col_x: str,
    col_y: str,
    ques: dict,
    replace_name_dict_ind: dict = None,
    replace_name_dict_col: dict = None,
    need_total: bool = False,
    need_x_null: bool = True,
    need_y_null: bool = True,
) -> pd.DataFrame:
    """
    prepare a dataframe for column x vs. column y.

    INPUT:
    file [str]
        file path
    col_x [str]
        column for horizontal axis
    col_y [str]
        column for vertical axis
    ques [dict]
        question dict
    replace_name_dict_ind [dict]
        wether need to replace the index name
    replace_name_dict_col [dict]
        wether need to replace the column name
    need_total [bool]
        wether need "Total="
    need_x_null [bool]
        wether need Null data in horizontal axis
    need_y_null [bool]
         wether need Null data in vertical axis

    OUTPUT:
    p_df: [pandas DataFrame] after preprocess dataframe.

    """

    name_dict_x = extract_question(ques, col_x)
    name_dict_y = extract_question(ques, col_y)

    df = pd.read_csv(file, usecols=[col_x, col_y]).fillna("No Answer")

    g_df = df.groupby([col_x, col_y]).size().reset_index(name="count")

    p_df = g_df.pivot(index=col_x, columns=col_y).fillna(0)
    p_df.columns = [name for _, name in p_df.columns]
    p_df = add_empty_cols(p_df.T, name_dict_x)
    p_df = add_empty_cols(p_df.T, name_dict_y)

    new_index = find_correspond_names(
        list(p_df.index),
        name_dict_x,
        replace_name_dict_ind,
    )

    new_columns = find_correspond_names(
        list(p_df.columns),
        name_dict_y,
        replace_name_dict_col,
    )

    p_df.index, p_df.columns = new_index, new_columns

    if need_x_null is False:
        p_df.drop("No Answer", inplace=True)
    if need_y_null is False:
        p_df.drop(("count", "No Answer"), axis=1, inplace=True)

    if need_total:
        p_df = p_df.append(p_df.sum().rename("Total"))

    return p_df


def add_empty_cols(df: pd.DataFrame, name_dict: dict) -> pd.DataFrame:
    """
    add empty columns to the dataFrame

    INPUT:

    df [pd.DataFrame]: dataFrame
    name_dict [dict]: dictionary used for name definition

    OUTPUT:

    df [pd.DataFrame]: dataFrame after add new empty columns

    """

    for i, (k, _) in enumerate(name_dict.items()):
        if k not in df.columns:
            df.insert(i, k, [0] * len(df.index))

    return df


def extract_question(questions: dict, col_name: str) -> dict:
    """
    extract question

    INPUT:

    question [dict]: from 'read_xml_file'
    col_name [str]: columns name

    OUTPUT:

    name_dict [dict]: new name dict
    """

    for ques in questions:
        if ques["name"] == col_name:
            name_dict = ques["choices"]
    return name_dict


def find_correspond_names(
    columns: list,
    org_name_dict: dict,
    replace_name_dict: dict = None,
) -> list:
    """
    find the corrsponding names and if neccessary (maybe too long or what ever) replace some of them

    INPUT:

    column [list]:
        corresponding columns
    org_name_dict [dict]:
        orignal name dict
    replace_name_dict [dict]:
        the name used for replace some orignal names

    OUTPUT:

    names [list]:
        corrspond names find from "question" dic
    """

    print(
        f"Laushir, if name is tai long and you want to change, \n \
            here provides the {org_name_dict.values() }, dron."
    )
    if replace_name_dict:
        name_dict = dict()
        for key, val in org_name_dict.items():
            if val in replace_name_dict.keys():
                name_dict[key] = replace_name_dict[val]
            else:
                name_dict[key] = val
    else:
        name_dict = org_name_dict

    if "No Answer" in columns:
        names = list(name_dict.values()) + list(["No Answer"])
    else:
        names = list(name_dict.values())

    return names


def percent_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    convert the data into percentage, return DataFrame. (option)

    INPUT:

    df [pd.DataFrame]:      orignal dataframe

    OUTPUT:

    new__df.transpose():    percentage dataframe

    """

    df_dic = dict()

    for label, row in df.iterrows():

        row = np.asarray(row)
        new_row = row / row.sum()
        df_dic[label] = new_row
    new_df = pd.DataFrame.from_dict(df_dic)
    col_name = [name for _, name in df.columns]
    new_df.index = col_name

    return new_df.transpose()


def percent_from_list_to_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    convert the data into percentage, return DataFrame.

    INPUT:

    df [pd.DataFrame]:
        orignal dataframe

    OUTPUT:

    new__df:
        percentage dataframe
    """

    df_list = list()

    for _, row in df.iterrows():
        row = np.asarray(row)
        if row.sum() == 0:
            new_row = row * 0
        else:
            new_row = row / row.sum()
        df_list.append(new_row)
    new_df = pd.DataFrame(df_list)

    col_name = [name for name in df.columns]

    new_df.index = df.index
    new_df.columns = col_name

    return new_df


def recast_multi_to_one(
    filepath: str,
    ques: dict,
    col_xs: List[Tuple[str, bool, bool]],
    col_ys: Tuple[str, bool],
    replace_name_dict_ind: dict,
    replace_name_dict_col: dict,
) -> Tuple[List[Tuple[int, bool]], int, pd.DataFrame]:
    """
    this is used for mulitple comparison, which integrate all columns in DataFrame used for
    comparison into one DataFrame. (neccessary)

    INPUT:

    filepath [str]:
        path of file
    ques [dict]:
        question dict from 'read_xml_dict'
    col_xs [List[Tuple[str, bool, bool]]]:
        columns information which used for x axis in the bar ploting.
    col_ys [Tuple[str, bool]]:
        columns information which used for y axis in the bar ploting
    replace_name_dict_ind [dict]:
        replace some of the name of index (as some of the names are too long or what ever)
    replace_name_dict_col [dict]:
        replace some of the name of columns (as some of the names are too long or what ever)

    OUTPUT:

    dim_xs:
        dimensons of columns which used for x axis variables
    dim_y:
        dimenson of columns which used for y axis variable
    recast_df:
        new data frame

    """

    col_y, y_no_answer = col_ys
    p_dfs, dim_xs, dim_y = list(), list(), list()
    for col_x, need_total, x_no_answer in col_xs:
        p_df = prepare_df(
            filepath,
            col_x,
            col_y,
            ques,
            replace_name_dict_col,
            replace_name_dict_ind,
            need_total=need_total,
            need_x_null=x_no_answer,
            need_y_null=y_no_answer,
        )
        dim_xs.append((len(p_df.index), need_total))

        p_dfs.append(p_df)
    recast_df = pd.concat(p_dfs)
    dim_y = len(recast_df.columns)

    return dim_xs, dim_y, recast_df


def assemble_data_process(
    filepath: str,
    structure_xml: dict,
    col_xs: List[Tuple[str, bool, bool]],
    col_ys: Tuple[str, bool],
    replace_name_dict_ind: dict = None,
    replace_name_dict_col: dict = None,
) -> Tuple[List[Tuple[int, bool]], int, pd.DataFrame]:
    """
    assemble all the data process outside the plot function.

    INPUT:

    filepath [str]:
        'data' path
    structure_xml [dict]:
        get from 'read_xml_file'
    col_xs [List[Tuple[str, bool, bool]]]:
        info of columns used for plot x axis
    col_ys [Tuple[str, bool]]:
        info of columns used for plot x axis
    replace_name_dict_ind [dict]:
        replace some of the name of index (as some of the names are too long or what ever)
    replace_name_dict_col [dict]:
        replace some of the name of index (as some of the names are too long or what ever)

    OUTPUT:

    dim_xs:
        dimensons of columns which used for x axis variables
    dim_y:
        dimenson of columns which used for y axis variable
    recast_df:
        new data frame

    """

    _, ques = structure_xml["sections"], structure_xml["questions"]

    dim_xs, dim_y, recast_df = recast_multi_to_one(
        filepath,
        ques,
        col_xs,
        col_ys,
        replace_name_dict_ind,
        replace_name_dict_col,
    )

    return dim_xs, dim_y, recast_df


# --------------------------------------------------------------------------------------------


def add_text_in_bar(
    ax: mpl.axes.Axes,
    f_size: tuple,
    p_df: pd.DataFrame,
    dim_y: int,
    interval: float,
    x_ticks_scale: float = 0.5,
    x_ticks_displacement: float = 2,
    set_location: list = None,
) -> Tuple[list, mpl.axes.Axes]:
    """
    add the percentage and other text content into each bar.

    INPUT:

    ax [mpl.axes.Axes]: axes
    f_size [tuple]:
        figure size
    p_df [pd.DataFrame]:
        dataFrame (after pre-processing)
    dim_y [int]:
        dimenson of columns which used for y axis variable
    interval [float]:
        intervals between each bar
    x_ticks_scale [float]:
        ratio used for scaling x
    x_ticks_displacement [float]:
        displacment used for shifting bar
    set_location [list]:
        set bar location along x axis

    OUTPUT:

    r_sum [list]: sum over row
    ax [mpl.axes.Axes]: axes
    """

    data, r_sum, c_data, h = list(), list(), list(), list()
    for _, row in p_df.iterrows():
        if sum(list(row)) == 0:
            r_sum.append(0.00000001)
        else:
            r_sum.append(sum(list(row)))
    for i, (_, col) in enumerate(p_df.iteritems()):
        c_data.append(np.asarray(col) / np.asarray(r_sum))
    r = len(col)

    data = np.asarray(c_data).flatten()

    accumu_height = list()

    if set_location:
        locator_list = set_location * dim_y

    for i, p in enumerate(ax.patches):

        if set_location:
            p.set_x(
                locator_list[i] * x_ticks_scale
                + x_ticks_displacement
                - p.get_width() / 2
            )
        else:
            p.set_x(
                (p.get_x() + p.get_width() / 2) * x_ticks_scale
                + x_ticks_displacement
                - p.get_width() / 2
            )

        h.append(p.get_height())
        if i < r:
            accumu_height.append(p.get_height())
        if data[i] >= 0.05:
            percent = f"{100 * data[i]:.0f}%"
            accumu_height, height = text_height(h, i, r, accumu_height)
            ax.annotate(
                percent,
                (p.get_x() + p.get_width() * 0.1, p.get_y() + p.get_height() * 0.4),
                fontsize=f_size[0] * 0.9,
                fontweight="heavy",
                color="white",
            )

    return r_sum, ax


def text_height(
    h: List[float], i: int, r: int, accumu_height: List[float]
) -> Tuple[List[float], float]:
    """
    calculate the position of the text in every patch of each bar

    INPUT:

    h [List[float]]:
        each stack's height
    i [int]:
        correspond to # stack level
    r [int]:
        # of each used columns
    accumu_height [List[float]]:
        accumulated height of stacked bar

    OUTPUT:

    accumu_height [List[float]]:
        accumulated height of stacked bar
    height:
        after stack, the height (diff from accumu_height)
    """

    height = 0
    if i < r:
        height = h[i] * 0.5
    else:
        accumu_height[i % r] += h[i]
        height = accumu_height[i % r] - h[i] * 0.36

    return (accumu_height, height)


def bar_plot_settings(
    fig: mpl.figure.Figure,
    ax: mpl.axes.Axes,
    f_size: tuple,
    dim_xs: List[Tuple[int, bool]],
    dim_y: int,
    interval: float,
    title: str = None,
    ylabel: str = None,
    xlabel: str = None,
    legend_location: str = None,
    save_figure: bool = False,
    no_frame: bool = True,
    row_sum: int = None,
    x_ticks_scale: float = 0.5,
    x_ticks_displacement: float = 2,
    set_location: list = None,
) -> Tuple[mpl.figure.Figure, mpl.axes.Axes]:
    """
    some figure settings in simple bar plot.

    INPUT:

    fig [mpl.figure.Figure]:
        mpl figure
    ax [mpl.axes.Axes]:
        mpl axes
    f_size [tuple]:
        igure size
    dim_xs [List[Tuple[int, bool]]]:
        dimensons of columns which used for x axis variables
    dim_y [int]:
        dimenson of columns which used for y axis variable
    title [str]:
        changed title default is None
    interval [float]:
        intervals between each bar
    ylabel [str]: y
    xlabel [str]: x
    legend_location [str]:
        location of legend
    save_figure [bool]: save or not
    no_frame [bool]:
        with or without legend frame
    row_sum [int]:
        sum of each dataFrame row
    x_ticks_scale [float]:
        ratio used for scaling x
    x_ticks_displacement [float]:
        displacment used for shifting bar
    set_location [list]:
        set bar location along x axis

    OUTPUT:

    fig [mpl.figure.Figure]: mpl figure
    ax [mpl.axes.Axes]: mpl axes
    """

    # lable font
    label_font = {
        "fontsize": f_size[0] * 1.2,
        "fontfamily": "DejaVu Sans",
        "fontstyle": "oblique",
    }

    # title font
    title_font = {
        "fontsize": f_size[0] * 1.5,
        "fontfamily": "DejaVu Sans",
        "fontstyle": "oblique",
    }

    # ticks
    ax.tick_params(direction="out", labelsize=f_size[0] * 1.2)

    if set_location:
        locator_list = set_location
    else:
        locator_list = ax.get_xticks()

    ax.xaxis.set_major_locator(
        ticker.FixedLocator(
            np.asarray(locator_list) * x_ticks_scale + x_ticks_displacement
        )
    )

    # label
    ax.set_ylabel(ylabel, **label_font)
    ax.set_xlabel(xlabel, **label_font)

    # ticklabels
    if row_sum:
        tic_label = list(ax.get_xticklabels())
        new_tic_label = set_ticklabels(labels=tic_label, r_sum=row_sum)
        ax.set_xticklabels(new_tic_label, **label_font)

    # title
    if title:
        ax.set_title(title, y=1.1, **title_font)

    # frame: if you use old version of matplotlib maybe this will work for you:
    # mpl.rcParams['axes.spines.bottom'] = False
    ax.spines.top.set_visible(False)
    ax.spines.right.set_visible(False)

    if no_frame:
        ax.spines.left.set_visible(False)
        ax.spines.bottom.set_visible(False)
        ax.tick_params(left=False, labelleft=False)
    else:
        ax.spines["bottom"].set_linewidth(2)
        ax.spines["left"].set_linewidth(2)

    # legend
    if legend_location:
        # works in 3.4.3 not work some previous version
        ax.get_legend().remove()

    ax.autoscale()
    ax.set_autoscale_on(True)

    # figure settings
    anchor = (0.5, 0.9)
    handles, leg_labels = ax.get_legend_handles_labels()
    new_leg_labels = list()
    for name in leg_labels:
        new_leg_labels.append(name)
    fig.legend(
        handles[0:dim_y],
        new_leg_labels[0:dim_y],
        ncol=dim_y,
        bbox_to_anchor=anchor,
        fontsize=f_size[0] * 1,
        loc=legend_location,
        frameon=False,
        labelspacing=0.1,
        handlelength=1,
        handletextpad=0.7,
        columnspacing=1,
    )

    try:
        fig.tight_layout(pad=1.2)
    except UserWarning:
        print(
            "Laushir, the most possible reason for this is that the question choice is too long\n\
            which lead to not enough bottom space for tight layout, so hai shtrolsha."
        )
    fig.autofmt_xdate()
    fig.savefig(save_figure)

    return fig, ax


def set_ticklabels(labels: list, r_sum: int) -> List[str]:
    """
    deal with the xtick label text

    INPUT:

    labels [list]:  lables
    r_sum [int]:    sum over row

    OUTPUT:

    tic_l [list]:   new tick lables
    """

    tic_l = list()
    tic_l = [
        i.get_text() + "(" + str(int(j)) + ")" if i.get_text() != "-oth-" else "Other"
        for i, j in zip(labels, r_sum)
    ]
    return tic_l


def multi_bar_to_one_compare(
    dim_xs: List[Tuple[int, bool]],
    dim_y: int,
    recast_df: pd.DataFrame,
    save_figure: str = None,
    give_title: str = None,
    interval: float = 0.5,
    legend_location: str = "upper center",
    color: list = None,
    fig_size: tuple = (10, 5),
    x_ticks_displacement: float = 1,
    x_ticks_scale: float = 0.5,
    set_location: list = None,
) -> Tuple[mpl.figure.Figure, mpl.axes.Axes]:

    """
    main func for both single or multiple comparison(s).

    INPUT:

    filepath [str]:
        'data' path
    structure_xml [dict]:
        get from 'read_xml_file'
    col_xs [List[Tuple[str, bool, bool]]]:
        info of columns used for plot x axis
    col_ys [Tuple[str, bool]]:
        info of columns used for plot x axis
    replace_name_dict_ind [dict]:
        replace some of the name of index (as some of the names are too long or what ever)
    replace_name_dict_col [dict]:
        replace some of the name of index (as some of the names are too long or what ever)
    save_figure [str]:
        save figure to path.
    give_title [str]:
        changed title default is None
    interval [float]:
        intervals between each bar
    legend_location [str]:
        location of legend
    color [list]:
        color scheme used from plotting
    fig_size [tuple]:
        figure size setting
    x_ticks_scale [float]:
        ratio used for scaling x
    x_ticks_displacement [float]:
        displacment used for shifting bar
    set_location [list]:
        set bar location along x axis

    OUTPUT:

    fig [mpl.figure.Figure]: mpl figure
    ax [mpl.axes.Axes]: mpl axes
    """

    fig, ax = plt.subplots(figsize=fig_size)

    if set_location:
        if len(set_location) != sum([i for i, _ in dim_xs]):
            raise Exception(
                f"Laushir, the num of bars ({sum([i for i, _ in dim_xs])}) are not match with \n\
                the num of location ({len(set_location)}) you give. Na hwedron."
            )

    if color is not None and len(color) != dim_y:
        raise Exception(
            f"Laushir, there need ({dim_y}) kinds of colors to make it as a color map list,\n\
            you dra only gives ({len(color)}) colors."
        )

    ax = percent_from_list_to_df(recast_df).plot.bar(
        ax=ax, stacked=True, width=0.03 * fig_size[0], color=color
    )

    r_sum, ax = add_text_in_bar(
        ax,
        fig_size,
        recast_df,
        dim_y=dim_y,
        interval=interval,
        set_location=set_location,
        x_ticks_displacement=x_ticks_displacement,
        x_ticks_scale=x_ticks_scale,
    )

    bar_plot_settings(
        fig,
        ax,
        f_size=fig_size,
        title=give_title,
        legend_location=legend_location,
        row_sum=r_sum,
        dim_xs=dim_xs,
        dim_y=dim_y,
        interval=interval,
        x_ticks_displacement=x_ticks_displacement,
        x_ticks_scale=x_ticks_scale,
        set_location=set_location,
        save_figure=save_figure,
    )

    return fig, ax

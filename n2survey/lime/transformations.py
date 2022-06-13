import re

import numpy as np
import pandas as pd

__all__ = [
    "rate_supervision",
    "rate_mental_health",
    "rate_satisfaction",
    "range_to_numerical",
    "calculate_duration",
    "rate_satisfaction",
]


def rate_supervision(
    question_label: str,
    responses: pd.DataFrame,
    choices: dict,
    keep_subscores: bool = False,
) -> pd.DataFrame:
    """Calculate average direct/formal supervision rating

    Args:
        question_label (str): Question label to use for transformation type inference
        responses (pd.DataFrame): DataFrame containing responses data
        choices (dict): dict for answer choice conversion
        keep_subscores (bool, optional): Whether to include scores from subquestions
            in the output DataFrame, or only total score and classification.
            Default False.

    Returns:
        pd.DataFrame: Rounded supervision ratings and classifications
    """
    # Infer labels from question
    if "formal supervisor" in question_label:
        label = "formal_supervision"
    elif "direct supervisor" in question_label:
        label = "direct_supervision"
    else:
        raise ValueError("Question incompatible with specified transformation.")
    # Supervision classes sorted from high to low (high score equals high satisfaction)
    supervision_classes = [
        "very satisfied",
        "rather satisfied",
        "neither satisfied nor dissatisfied",
        "rather dissatisfied",
        "very dissatisfied",
    ]
    supervision_class_codes = ["A1", "A2", "A3", "A4", "A5"]
    supervision_class_scores = [5.0, 4.0, 3.0, 2.0, 1.0]

    # Set up score conversion dicts for individual questions
    supervision_question_scores = {
        "Fully agree": 5.0,
        "Partially agree": 4.0,
        "Neither agree nor disagree": 3.0,
        "Partially disagree": 2.0,
        "Fully disagree": 1.0,
    }
    # Inverse supervision transformation: Score (5.0) --> Class ('Very satisfied')
    supervision_score_to_class = {
        score: the_class
        for the_class, score in zip(supervision_classes, supervision_class_scores)
    }
    # Inverse supervision transformation: Class ('Very satisfied') --> Code ('A1')
    supervision_class_to_code = {
        the_class: code
        for code, the_class in zip(supervision_class_codes, supervision_classes)
    }

    # Map responses from code to text then to score
    df = pd.DataFrame()
    for column in responses.columns:
        df[f"{column}_score"] = (
            responses[column]
            .map(choices)
            .map(supervision_question_scores, na_action="ignore")
        )

    # Calculate mean rating and round (ignoring NaN)
    df[f"{label}_score"] = df.mean(axis=1, skipna=True).round()

    # Classify into categories
    df[f"{label}_class"] = pd.Categorical(
        df[f"{label}_score"]
        .map(supervision_score_to_class, na_action="ignore")
        .map(supervision_class_to_code, na_action="ignore"),
        categories=supervision_class_codes,
        ordered=True,
    )

    if not keep_subscores:
        df = df.drop(df.columns[:-2], axis=1)

    return df


def rate_mental_health(
    question_label: str,
    responses: pd.DataFrame,
    choices: dict,
    condition: str = None,
    keep_subscores: bool = False,
) -> pd.DataFrame:
    """Calculate State/Trait Anxiety or Depression score based on responses to
        question based on the following references:
            K. Kroenke, R. L. Spitzer, J. B. W. William, and B. Löwe., The
                Patient Health Questionnaire somatic, anxiety,and depressive
                symptom scales: a systematic review. General Hospital
                Psychiatry, 32(4):345–359, 2010.
            T. M. Marteau and H. Bekker., The development of a six-item short-
                form of the state scale of the spielberger state-trait anxiety
                inventory (STAI). British Journal of Clinical Psychology,
                31(3):301–306, 1992.

    Args:
        question_label (str): Question label to use for transformation type inference
        responses (pd.DataFrame): DataFrame containing responses data
        choices (dict): dict for answer choice conversion
        condition (str, optional): Which kind of mental health condition to rate,
            "state_anxiety", "trait_anxiety", or "depression". If not specified,
            the condition is automatically infered. Default None.
        keep_subscores (bool, optional): Whether to include scores from subquestions
            in the output DataFrame, or only total score and classification.
            Default False.

    Returns:
        pd.DataFrame: Mental health condition ratings and classifications
    """

    # Infer condition type if not provided
    if condition is None:
        if "I feel calm" in question_label:
            condition = "state_anxiety"
        elif "calm, cool and collected" in question_label:
            condition = "trait_anxiety"
        elif "interest or pleasure" in question_label:
            condition = "depression"
        else:
            raise ValueError("Question incompatible with any supported condition type.")

    # Set up condition-specific parameters
    if condition == "state_anxiety":
        if "I feel calm" not in question_label:
            raise ValueError("Question incompatible with specified condition type.")
        num_subquestions = 6
        base_score = 10 / 3
        conversion = ["pos", "neg", "neg", "pos", "pos", "neg"]
        label = "state_anxiety"
        classification_boundaries = [0, 37, 44, 80]
        classes = ["no or low anxiety", "moderate anxiety", "high anxiety"]
        choice_codes = ["A1", "A2", "A3"]

    elif condition == "trait_anxiety":
        if "calm, cool and collected" not in question_label:
            raise ValueError("Question incompatible with specified condition type.")
        num_subquestions = 8
        base_score = 5 / 2
        conversion = [
            "pos",
            "neg",
            "neg",
            "pos",
            "neg",
            "neg",
            "pos",
            "neg",
        ]
        label = "trait_anxiety"
        classification_boundaries = [0, 37, 44, 80]
        classes = ["no or low anxiety", "moderate anxiety", "high anxiety"]
        choice_codes = ["A1", "A2", "A3"]
    elif condition == "depression":
        if "interest or pleasure" not in question_label:
            raise ValueError("Question incompatible with specified condition type.")
        num_subquestions = 8
        base_score = 1
        conversion = ["freq" for i in range(8)]
        label = "depression"
        classification_boundaries = [0, 4, 9, 14, 19, 24]
        classes = [
            "no to minimal depression",
            "mild depression",
            "moderate depression",
            "moderately severe depression",
            "severe depression",
        ]
        choice_codes = ["A1", "A2", "A3", "A4", "A5"]
    else:
        raise ValueError(
            "Unsupported condition type. Please consult your friendly local psychiatrist."
        )

    # Set up score conversion dicts
    pos_direction_scores = {
        "Not at all": 4 * base_score,
        "Somewhat": 3 * base_score,
        "Moderately": 2 * base_score,
        "Very much": 1 * base_score,
    }
    neg_direction_scores = {
        "Not at all": 1 * base_score,
        "Somewhat": 2 * base_score,
        "Moderately": 3 * base_score,
        "Very much": 4 * base_score,
    }
    frequency_scores = {
        "Not at all": 0 * base_score,
        "Several days": 1 * base_score,
        "More than half the days": 2 * base_score,
        "Nearly every day": 3 * base_score,
    }
    conversion_dicts = {
        "pos": pos_direction_scores,
        "neg": neg_direction_scores,
        "freq": frequency_scores,
    }
    invert_dict = {the_class: code for code, the_class in zip(choice_codes, classes)}

    # Map responses from code to text then to score
    df = pd.DataFrame()
    for column, conversion in zip(responses.columns, conversion):
        df[f"{column}_score"] = (
            responses[column]
            .map(choices)
            .map(conversion_dicts[conversion], na_action="ignore")
        )

    # Calculate total anxiety or depression scores
    # scaled by number of non-NaN responses
    # e.g. scale by 8/5 if 5/8 subquestions answered
    responses_counts = df.notna().sum(axis=1)
    df[f"{label}_score"] = (
        df.sum(axis=1, skipna=True).div(responses_counts).mul(num_subquestions)
    )

    # Suppress entries with less than half of all subquestions answered
    df.loc[responses_counts < num_subquestions / 2, f"{label}_score"] = None

    # Classify into categories
    df[f"{label}_class"] = pd.cut(
        df[f"{label}_score"],
        bins=classification_boundaries,
        labels=classes,
    ).map(invert_dict, na_action="ignore")

    if not keep_subscores:
        df = df.drop(df.columns[:-2], axis=1)

    return df


def strRange_to_intRange(strAnswer: str) -> int:

    """Calculate the mean of all numbers present in a string.

    Args:
        strAnswer (str): String containing numbers.

    Returns:
        int: Mean of all values present in the string.

    """

    if re.search(r"(?:[1-9]\d*)", strAnswer):
        list_range = re.findall(r"(?:[1-9]\d*)(?:\.)?(?:[1-9]\d+)?", strAnswer)
        list_range_numerical = list(map(int, list_range))

        return int(np.mean(list_range_numerical))

    else:
        return np.NaN  # Handy when computing mean, median,... using numpy


def range_to_numerical(question_label: str, responses: pd.DataFrame) -> pd.DataFrame:

    """Get numerical values from responses with ranges in a non-numerical datatype.

    Args:
        question_label (str): Question label to use for transformation type inference
        responses (pd.DataFrame): DataFrame containing responses data

    Returns:
        pd.DataFrame: Numerical values for each range
    """

    check_condition = {
        "For how long have you been working on your PhD without pay": "noincome_duration",
        "Right now, what is your monthly net income for your work at your research organization": "income_amount",
        "How much do you pay for your rent and associated living costs per month in euros": "costs_amount",
        "What was or is the longest duration of your contract or stipend related to your PhD project": "contract_duration",
        "How many holidays per year can you take according to your contract or stipend": "holiday_amount",
        "On average, how many hours do you typically work per week in total": "hours_amount",
        "How many days did you take off (holiday) in the past year": "holidaytaken_amount",
    }

    # Assign new question label
    for label in check_condition:
        if label in question_label:
            new_question_label = check_condition[label]

    # Check if correct question has been chosen
    if new_question_label is None:
        raise ValueError("Question incompatible with specified condition type.")

    df = pd.DataFrame()

    responses_numerical = responses.iloc[:, 0].apply(strRange_to_intRange)

    df[f"{new_question_label}"] = responses_numerical

    return df


def calculate_duration(start_responses: pd.DataFrame, end_responses: pd.DataFrame):
    """Calculate duration

    Args:
        start_responses (pd.DataFrame): DataFrame containing responses data of the start of duration
        end_responses (pd.DataFrame): DataFrame containing responses data of the end of duration

    Returns:
        pd.DataFrame: Rounded PhD duration in days, months and years
    """

    # get labels of start and end questions to get their data
    df = pd.concat(
        [start_responses, end_responses],
        axis=1,
    )

    # duration calculation, return as day
    df["PhD duration (days)"] = df.iloc[:, 1] - df.iloc[:, 0]

    # convert days to month and year
    df["PhD duration (months)"] = df.iloc[:, 2] / np.timedelta64("1", "M")
    df["PhD duration (years)"] = df.iloc[:, 2] / np.timedelta64("1", "Y")

    # convert PhD duration (days) to float type for consistency
    df["PhD duration (days)"] = df["PhD duration (days)"].dt.days

    # drop temporary columns used for duration calculation
    # and return only duration in day, month and year
    df = df.iloc[:, 2:].round()

    return df


def rate_satisfaction(
    question_label: str,
    responses: pd.DataFrame,
    choices: dict,
    keep_subscores: bool = False,
) -> pd.DataFrame:
    """Calculate average overall satisfaction rating
    Args:
        question_label (str): Question label to use for transformation type inference
        responses (pd.DataFrame): DataFrame containing responses data
        choices (dict): dict for answer choice conversion
        keep_subscores (bool, optional): Whether to include scores from subquestions
            in the output DataFrame, or only total score and classification.
            Default False.
    Returns:
        pd.DataFrame: Rounded satisfaction ratings and classifications
    """
    # Infer labels from question
    if "satisfied" in question_label:
        label = "satisfaction"
    else:
        raise ValueError("Question incompatible with specified transformation.")
    # Satisfation classes sorted from high to low (high score equals high satisfaction)
    satisfaction_classes = [
        "very satisfied",
        "rather satisfied",
        "neither satisfied nor dissatisfied",
        "rather dissatisfied",
        "very dissatisfied",
    ]
    satisfaction_class_codes = ["A1", "A2", "A3", "A4", "A5"]
    satisfaction_class_scores = [5.0, 4.0, 3.0, 2.0, 1.0]

    # Set up score conversion dicts for individual questions
    satisfaction_question_scores = {
        "Very satisfied": 5.0,
        "Satisfied": 4.0,
        "Neither/nor": 3.0,
        "Dissatisfied": 2.0,
        "Very dissatisfied": 1.0,
    }
    # Inverse satisfaction transformation: Score (5.0) --> Class ('Very satisfied')
    satisfaction_score_to_class = {
        score: the_class
        for the_class, score in zip(satisfaction_classes, satisfaction_class_scores)
    }
    # Inverse satisfaction transformation: Class ('Very satisfied') --> Code ('A1')
    satisfaction_class_to_code = {
        the_class: code
        for code, the_class in zip(satisfaction_class_codes, satisfaction_classes)
    }

    # Map responses from code to text then to score
    df = pd.DataFrame()
    for column in responses.columns:
        df[f"{column}_score"] = (
            responses[column]
            .map(choices)
            .map(satisfaction_question_scores, na_action="ignore")
        )

    # Calculate mean rating and round (ignoring NaN)
    df[f"{label}_score"] = df.mean(axis=1, skipna=True).round()

    # Classify into categories
    df[f"{label}_class"] = pd.Categorical(
        df[f"{label}_score"]
        .map(satisfaction_score_to_class, na_action="ignore")
        .map(satisfaction_class_to_code, na_action="ignore"),
        categories=satisfaction_class_codes,
        ordered=True,
    )

    if not keep_subscores:
        df = df.drop(df.columns[:-2], axis=1)

    return df

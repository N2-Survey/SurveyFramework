"""Lime Survey related helper functions

The module contains helper functions for parsing
lime survey data such as *.xml structure files
"""

import os
import re
from typing import Optional
from warnings import warn

from bs4 import BeautifulSoup
from bs4.element import Tag

__all__ = [
    "read_lime_questionnaire_structure",
]


def _get_clean_string(tag: Tag) -> str:
    """Clear a text in XML from HTML tags and line breaks"""
    # Remove HTML tags and line breaks
    clean_string = (
        " ".join(BeautifulSoup(tag.text, "html.parser").stripped_strings)
        .replace("\n", " ")
        .replace("\t", " ")
        .replace("\xa0", " ")
        .strip()
    )

    # Replace multiply repeated spaces by one
    clean_string = re.sub(" +", " ", clean_string)

    return clean_string


def _parse_question_title(question: Tag) -> str:
    text_sections = question.find_all("text", recursive=False)
    if len(text_sections) >= 1:
        question_label = _get_clean_string(text_sections[0])
        if len(text_sections) > 1:
            warn(
                f"More than one 'text' section provided for question {question}."
                " Only the first one was used."
            )
    else:
        raise AssertionError(f"No question label for question {question}")

    return question_label


def _parse_question_description(question: Tag) -> str:
    description = ""
    directive_sections = question.find_all("directive", recursive=False)
    if len(directive_sections) >= 1:
        description = " ".join(
            [
                _get_clean_string(description)
                for description in directive_sections[0].find_all("text")
            ]
        )
        if len(directive_sections) > 1:
            warn(
                f"More than one 'directive' section provided for question {question}."
                " Only the first one was used."
            )
    return description


def _parse_question_subquestions(question: Tag) -> list[tuple[str, str]]:
    # TODO: Add validation that varName is provided
    # TODO: Add validation that there is only one <text> tag
    return [
        (subquestion["varName"], _get_clean_string(subquestion.find("text")))
        for subquestion in question.find_all("subQuestion", recursive=False)
    ]


def _parse_single_question_response(response: Tag) -> tuple[dict, Optional[dict]]:
    # Common response structure
    parsed_response = {
        "name": response.attrs.get("varName", ""),
        "format": None,
        "length": None,
        "label": None,
        "choices": None,
    }
    contingent_response = None

    # Get first child node of <response> section
    response_data = response.findChild()

    # Parse non-fixed question
    if response_data.name == "free":
        parsed_response.update(
            format=_get_clean_string(response_data.format),
            length=_get_clean_string(response_data.length),
            label=_get_clean_string(response_data.label),
        )
    # Parse fixed question (i.e. with choises)
    elif response_data.name == "fixed":
        # Parse choices
        choices = {
            _get_clean_string(category.value): _get_clean_string(category.label)
            for category in response_data.find_all("category", recursive=False)
        }
        parsed_response.update(choices=choices)

        # Parse contingent question
        contingent_question = response_data.find("contingentQuestion")
        if contingent_question is not None:
            assert (
                len(response_data.find_all("contingentQuestion")) == 1
            ), f"Too many 'contingentQuestion's for response {response}"

            contingent_response = {
                "name": contingent_question["varName"],
                "text": _get_clean_string(contingent_question.find("text")),
                "length": _get_clean_string(contingent_question.length),
                "format": _get_clean_string(contingent_question.format),
                "contingent_of_name": parsed_response["name"],
                "contingent_of_choice": _get_clean_string(
                    contingent_question.parent.value
                ),
            }
    else:
        raise AssertionError(
            f"Unexpected response format {response}. Unknown response type."
        )

    return (parsed_response, contingent_response)


def _parse_question_responses(question: Tag) -> list[tuple[dict, Optional[dict]]]:
    response_sections = question.find_all("response", recursive=False)

    if len(response_sections) == 0:
        raise AssertionError(
            f"Unexpected question format for question {question}."
            " There is no 'response' section."
        )

    parsed_responses = [
        _parse_single_question_response(response) for response in response_sections
    ]

    return parsed_responses


def _get_question_group_name(responses: list[Tag]) -> str:
    names = [response["name"] for response, _ in responses]
    if len(names) == 1:
        question_group_name = names[0]
    elif len(names) > 1:
        question_group_name = os.path.commonprefix(names)
        question_group_name = question_group_name.split("_")[0]
    else:
        raise ValueError("At least one response with a name is required")

    return question_group_name


def _parse_question(question: Tag) -> list[dict]:
    """
    TODO
    """

    # Get question label
    question_label = _parse_question_title(question)

    # Get question description
    question_description = _parse_question_description(question)

    # Get question subQuestions, if it has
    subquestions = _parse_question_subquestions(question)

    # Get question responses
    responses = _parse_question_responses(question)

    # Check assumptions
    subquestions_count = len(subquestions)
    responses_count = len(responses)
    assert (subquestions_count == 0) or (responses_count == 1), (
        f"Unexpected question type for question {question}."
        " Subquestion with multiply responses are not supported."
    )

    # Combine responses and subquestions
    columns_list = []
    if subquestions_count:
        response, contingent = responses[0]
        assert contingent is None, (
            f"Unexpected question type for question {question}."
            " Subquestion with contingent questions are not supported."
        )

        for name, label in subquestions:
            # Add the column
            columns_list.append(
                {
                    "name": name,
                    "label": label,
                    "format": response["format"],
                    "choices": response["choices"],
                }
            )

    else:
        for response, contingent in responses:
            # Get a label
            if response["label"]:
                label = response["label"]
            else:
                label = question_label
            # Add the column
            columns_list.append(
                {
                    "name": response["name"],
                    "label": label,
                    "format": response["format"],
                    "choices": response["choices"],
                }
            )
            if contingent is not None:
                # Get a label
                if contingent["text"]:
                    # If text was provided for the contingent question
                    # then use it combinded with the question label
                    label = " / ".join([columns_list[-1]["label"], contingent["text"]])
                else:
                    # If text was not provided for the contingent question
                    # then use contingent choice label combinded with the
                    # question label
                    label = " / ".join(
                        [
                            columns_list[-1]["label"],
                            columns_list[-1]["choices"][
                                contingent["contingent_of_choice"]
                            ],
                        ]
                    )
                # Add the column information
                columns_list.append(
                    {
                        "name": contingent["name"],
                        "label": label,
                        "format": contingent["format"],
                        "contingent_of_name": contingent["contingent_of_name"],
                        "contingent_of_choice": contingent["contingent_of_choice"],
                    }
                )

    # Add keys common for the whole <question> section
    question_group_name = _get_question_group_name(responses)
    columns_list = [
        {
            **column,
            "question_group": question_group_name,
            "question_label": question_label,
            "question_description": question_description,
        }
        for column in columns_list
    ]

    return columns_list


def _parse_section(section: Tag) -> dict:
    """Parse questionnaire section

    Args:
        section (Tag): bs4 element of a section like `soup.find("section")`

    Returns:
        dict: A dictionary with the section information consisting of "id", "title",
          and "info"
    """
    # Get section ID
    section_id = section.attrs.get("id", None)
    if section_id is None:
        raise AssertionError(
            "Unexpected section structure."
            f" No id attribute found for section {section}"
        )
    else:
        section_id = int(section_id)

    # Parse <sectionInfo> tags
    section_info = ""
    section_title = None
    for info in section.find_all("sectionInfo"):
        position = _get_clean_string(info.position)
        if position == "title":
            section_title = _get_clean_string(section.sectionInfo.find("text"))
        elif position in ("before", "after"):
            current_text = " ".join(
                [
                    _get_clean_string(description)
                    for description in info.find_all("text")
                ]
            )
            section_info = f"{section_info} {current_text}".strip()
        else:
            raise AssertionError(
                "Unexpected section structure."
                f" Unexpected sectionInfo position '{position}' for section {section}"
            )

    if section_title is None:
        raise AssertionError(
            f"Unexpected section structure. No title found for section {section}"
        )

    return {
        "id": section_id,
        "title": section_title,
        "info": section_info,
    }


def read_lime_questionnaire_structure(filepath: str) -> dict[str, dict]:
    """TODO:"""

    # Read the structure file
    with open(filepath, "r") as fp:
        soup = BeautifulSoup(fp, "xml")

    # Parse sections and questions
    result_sections = list()
    result_questions = list()
    for section in soup.find_all("section"):
        section_dict = _parse_section(section)
        result_sections.append(section_dict)

        # Parse question
        for question in section.find_all("question"):
            # Get columns description for the question
            question_columns_list = _parse_question(question)
            # Add section_id to the columns descriptions
            question_columns_list = [
                {**column, "section_id": section_dict["id"]}
                for column in question_columns_list
            ]
            # Append to the resulting list of columns
            result_questions += question_columns_list

    return {"sections": result_sections, "questions": result_questions}

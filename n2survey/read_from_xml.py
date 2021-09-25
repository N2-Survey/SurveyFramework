import re
from json import dump
from typing import Dict

from bs4 import BeautifulSoup, Tag


def _text_refining(s: str) -> str:
    """
    Replacing unnecessary indents, linebreaks, and unicodes due to consistent processing
    """
    matched = ["\n", "\t", "\xa0"]
    res_s = re.sub("|".join(matched), "", s)
    return res_s


def _sectioninfo_text_parse(bsString: str) -> str:
    text = ""
    sps = BeautifulSoup(bsString, "html.parser").find_all("p")
    for sp in sps:
        if bool(sp.string):
            text += _text_refining(sp.string)
    return text


def _assemble_section(section: Tag, section_id: int) -> dict:
    """
    assemble all contents for each section as a dict
    """
    section_info = ""
    for info in section.find_all("sectionInfo"):
        if info.position.get_text() == "title":
            section_title = section.sectionInfo.find("text").get_text()
        else:
            section_text = info.find_all("text")
            text_p = ""
            for t in section_text:
                text_p += _sectioninfo_text_parse(t.string)
            section_info = text_p
    section_dict = {"id": section_id, "title": section_title, "info": section_info}
    return section_dict


def _find_choices(resp: Tag) -> dict:
    """
    find all the choices belong to each question
    """
    cates = dict()
    categories = resp.find_all("category")
    for category in categories:
        category_lab = category.label.string
        category_val = category.value.string
        # A#other case
        if bool(category.contingentQuestion):
            category_val = category.contingentQuestion.attrs["varName"]
            category_lab = _text_refining(
                category.contingentQuestion.find("text").get_text()
            )
        cates[category_lab] = category_val
    return cates


def _integrate_subquestions(
    question: Tag, question_content: str, section_id: int
) -> list:
    """
    extract subquestions from data and make them as separated columns
    """
    res_subquestions = list()
    subs = question.find_all("subQuestion")
    if question.response.category is not None:
        sub_type = "subquestion choice"
    else:
        sub_type = "subquestion text"
    for sub in subs:
        res_subquestions.append(
            {
                "name": sub["varName"],
                "question": question_content + "[" + sub.find("text").get_text() + "]",
                "description": "",
                "question type": sub_type,
                "is_other": False,
                "is_sub": True,
                "choices": _find_choices(question.response),
                "section_id": section_id,
                "qustion group": question.response.attrs["varName"],
            }
        )
    return res_subquestions


def _store_questions(
    question: Tag,
    section_id: int,
    question_content: str,
    question_desc: str,
) -> list:
    """
    question include:
        1. multiple choice question (w/o descriptions)
            1.1 multi choice + other choice item + "other" type question. See F3T
            1.2 pure multi choice
        2. single choice question (w/o descriptions)
            2.1 single choice with "other" type question
            2.2 pure single choice
        3. pure "text" question
        4. "comment" type question
    """
    store_question = list()
    resps = question.find_all("response")

    for resp in resps:
        len_cate = len(resp.find_all("category"))
        # multiple choice or contingent-> other + multiple choice (eg. "F3T")
        if len_cate == 1:
            if bool(resp.category.contingentQuestion):
                is_other = True
                name = resp.attrs["varName"] + "[other]"
                question_content = question_content + "[other]"
                question_type = "other text"
                question_choices = resp.category.contingentQuestion.find(
                    "text"
                ).string  # other
            else:
                is_other = False
                name = resp.attrs["varName"]
                question_type = "multi choice"
                question_choices = _find_choices(resp)
        # single choice or contingent -> other + single choice (eg. "A1other")
        elif len_cate > 1:
            is_other = False
            name = resp.attrs["varName"]
            question_type = "single choice"
            question_choices = _find_choices(resp)
            if bool(resp.find_all("category")[-1].contingentQuestion):
                store_question.append(
                    {
                        "name": resp.attrs["varName"] + "[other]",
                        "question": question_content,
                        "description": question_desc,
                        "question type": "other text",
                        "is_other": True,
                        "is_sub": False,
                        "choices": resp.find_all("category")[-1]
                        .contingentQuestion.find("text")
                        .stringquestion_choices,
                        "section_id": section_id,
                        "qustion group": resps[-1].attrs["varName"],
                    }
                )
        # here len_cate == 0 which is comment type (eg. "F5a1_comment") or pure text (eg. "last")
        else:
            question_choices = {}
            is_other = False
            # "comment" type question
            if len(resps) == 2:
                question_type = "comment text"
                name = resps[-1].attrs["varName"] + "[comment]"
            # pure "text" type
            else:
                question_type = "text"
                name = question.response.attrs["varName"]

        store_question.append(
            {
                "name": name,
                "question": question_content,
                "description": question_desc,
                "question type": question_type,
                "is_other": is_other,
                "is_sub": False,
                "choices": question_choices,
                "section_id": section_id,
                "qustion group": resps[-1].attrs["varName"],
            }
        )
    return store_question


def _concat_question_text(questions: list) -> str:
    """
    some question text contains long paragraphs or separated texts,
    use thisfunc to concate them to one.
    """
    res_desc = ""
    for question in questions:
        res_desc += _html_purify(question.string)
    return res_desc


def _assemble_questions(question: Tag, section_id: int) -> dict:
    """
    assemble all contents for each question
    """
    question_content = _html_purify(question.find("text").string)
    if question.find("directive") is not None:
        question_descs = question.find("directive").find_all("text")
        question_desc = _concat_question_text(question_descs)
    else:
        question_desc = ""
    stored_questions = _store_questions(
        question, section_id, question_content, question_desc
    )
    subquestion_dict = list()
    if bool(question.subQuestion):
        subquestion_dict = _integrate_subquestions(
            question, question_content, section_id
        )
    return stored_questions + subquestion_dict


def _html_purify(htmls: str) -> str:
    """
    after parsing from xml, some text still in form of html, use this func to parse it out
    """
    return _text_refining(BeautifulSoup(htmls, "html.parser").get_text())


def decompose_results(sections, questions):
    """
    dumps the "Sections" and "Questions" part to file
    to make it easy for using.
    """
    with open("../data/tmp/Sections.dat", "w") as fs:
        dump(sections, fs)
    with open("../data/tmp/Questions.dat", "w") as fq:
        dump(questions, fq)


def read_lime_questionnaire_structure(filepath: str) -> Dict[str, dict]:
    """
    Reads questionnaire structure XML file

    Args:
        filepath: A string with a path to a XML file with questionnaire structure

    Returns:
        A dict containing the questionnaire structure:
        {
            "sections": {
               {
                   "id":13901,
                   "title": "Demographics",
                   "info": "In this section, we will ask general questions about yourself \
                       and your doctoral project."
               },
               ....
            },
            "questions": {
                {
                    "name": "A1",
                    "question": "What is your year of birth?",
                    "description": "Please use the following format: "xxxx", e.g. 1989",
                    "question type": "sigle choice",
                    "is_other": False,
                    "is_sub": False,
                    "choices": {"I don't want to answer this question": "A2", ...},
                    "section_id": 13901,
                    "question group": A1
                },
                {
                    "name": "A4[other]",
                    "question": "What is your year of birth? [other]",
                    "description": "Please use the following format: "xxxx" , e.g. 1989",
                    "question type": "text",
                    "is_other": True,
                    "is_sub": False,
                    "choices": {},
                    "section_id": 13901,
                    "question group": A4
                },
                {
                    "name": "C5_SQ003",
                    "question": "Do you get external financial support to cover...",
                    "description": "",
                    "question type": "multi choice",
                    "is_other": False,
                    "is_sub": False,
                    "chioces": {"Parents": "Y"},
                    "section_id": 13907 ,
                    "question group": C5T
                },
                ...
            }
        }

    Raises:
        ValueError: Invalid XML file
        ValueError: Provided file has unexpected structure
    """
    ans = dict()
    f = open(filepath, "r")

    soup = BeautifulSoup(f, "xml")
    res_sections = list()
    res_questions = list()
    sections = soup.find_all("section")

    for section in sections:
        section_id = section.attrs["id"]
        section_dict = _assemble_section(section, section_id)
        res_sections.append(section_dict)
        questions = section.find_all("question")

        for question in questions:
            question_dict = _assemble_questions(question, section_id)
            res_questions += question_dict

    ans = {"sections": res_sections, "questions": res_questions}

    return ans

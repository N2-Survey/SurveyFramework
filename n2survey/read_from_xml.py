# flake8: noqa
import re
import sys
import bs4
from bs4 import BeautifulSoup

from json import dump
from typing import Dict


def _text_refining(s: str) -> str:
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

def _find_choices(resp: bs4.element.Tag) -> dict:
    cates = dict()
    categories = resp.find_all("category")
    for category in categories:
        category_lab = category.label.string
        category_val = category.value.string
        # A#other case
        if bool(category.contingentQuestion):
            category_val = category.contingentQuestion.attrs["varName"]
            category_lab = _text_refining(category.contingentQuestion.find("text").get_text())
        cates[category_lab] = category_val
    return cates


def _integrate_subquestions(question: bs4.element.Tag, section_id: int) -> list:
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
                "question": sub.find("text").get_text(),
                "description": "",
                "question type": sub_type,
                "is_other": False,
                "is_sub": True,
                "choices": _find_choices(question.response),
                "section_id": section_id,
                "qustion group": question.response.attrs["varName"]
            })
    return res_subquestions


def _store_questions(question: bs4.element.Tag, section_id: int, question_content: str, question_desc: str) -> list:
    '''
    question include:
        1. multiple choice question (w/o descriptions)
            1.1 multi choice + other choice item + "other" type question. See F3T
            1.2 pure multi choice
        2. single choice question (w/o descriptions)
            2.1 single choice with "other" type question
            2.2 pure single choice
        3. pure "text" question
        4. "comment" type question
    '''
    store_question = list()
    resps = question.find_all("response")

    for resp in resps:
        len_cate = len(resp.find_all('category'))
        # multiple choice or contingent-> other + multiple choice (eg. "F3T")
        if len_cate == 1:
            if bool(resp.category.contingentQuestion):
                is_other = True
                name = resp.attrs["varName"]+'[other]'
                question_type = 'other text'
                question_choices = resp.category.contingentQuestion.find('text').string # other
            else:
                is_other = False
                name = resp.attrs["varName"]
                question_type = 'multi choice'
                question_choices = _find_choices(resp)            
        # single choice or contingent -> other + single choice (eg. "A1other")
        elif len_cate > 1:
            if bool(resp.category.contingentQuestion):
                is_other = True
                name = resp.attrs["varName"]+'[other]'
                question_type = 'other text'
                question_choices = resp.category.contingentQuestion.find('text').string # other
            else:
                is_other = False
                name = resp.attrs["varName"]
                question_type = 'single choice'
                question_choices = _find_choices(resp)  
        # here len_cate == 0 which is comment type (eg. "F5a1_comment") or pure text (eg. "last")
        else:
            question_choices = {}
            is_other = False
            # "comment" type question
            if len(resps) == 2:
                question_type = 'comment text'
                name = resps[-1].attrs["varName"] + "[comment]"
            # pure "text" type
            else:
                question_type = 'text'
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
                "qustion group": resps[-1].attrs["varName"]
            })
    return store_question


def _concat_question_text(questions: list) -> str:
    res_desc = ""
    for question in questions:
        res_desc += _html_purify(question.string)
    return res_desc

def _html_purify(htmls: str)-> str:
    return _text_refining(BeautifulSoup(htmls, "html.parser").get_text())
 

def decompose_results(sections, questions):
    with open("../data/tmp/Sections.dat", "w") as fs:
        dump(sections, fs)
    with open("../data/tmp/Questions.dat", "w") as fq:
        dump(questions, fq)


def read_lime_questionnaire_structure(filepath: str)-> Dict[dict, dict]:
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
                    "description": "Please use the following format: 'xxxx' , e.g. 1989",
                    "question type": "sigle choice",
                    "is_other": False,
                    "is_sub": False,
                    "choices": {"I don't want to answer this question": 'A2', ...},
                    "section_id": 13901,
                    "question group": A1
                },
                {
                    "name": "A4[other]",
                    "question": "What is your year of birth? other",
                    "description": "Please use the following format: 'xxxx' , e.g. 1989",
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
    try:
        f = open(filepath, "r")
    except OSError:
        print(f"{filepath} is an invalid xml file")
        sys.exit()
    f = open(filepath, "r")

    soup = BeautifulSoup(f, "xml")
    sections = soup.find_all("section")
    res_sections = list()
    res_questions = list()

    for section in sections:
        section_id = section.attrs["id"]
        section_title = section.sectionInfo.find('text').get_text()

        for info in section.find_all("sectionInfo"):
            section_text = info.find_all("text")
            text_p = ""
            for t in section_text:
                text_p += _sectioninfo_text_parse(t.string)
            section_info = text_p
        res_sections.append({"id": section_id, "title": section_title, "info": section_info})
        questions = section.find_all("question")

        for question in questions:
            question_content = _html_purify(question.find("text").string)
            if question.find("directive") is not None:
                question_descs = question.find("directive").find_all("text")
                question_desc = _concat_question_text(question_descs)
            else:
                question_desc = ""
            stored_questions = _store_questions(question, section_id, question_content, question_desc)
            subquestion_dict = list()
            if bool(question.subQuestion):
                subquestion_dict = _integrate_subquestions(question, section_id)
            res_questions += subquestion_dict + stored_questions

    ans = {"sections": res_sections, "questions": res_questions}

    return ans


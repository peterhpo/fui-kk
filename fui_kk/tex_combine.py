#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Combines all latex files into 1 big latex document"""

__authors__    = ["Ole Herman Schumacher Elgesem"]
__copyright__  = "Ole Herman Schumacher Elgesem"

__license__    = "MIT"
# This file is subject to the terms and conditions defined in
# file 'LICENSE.txt', which is part of this source code package.

import os
import sys
import json
import argparse
import re
from collections import OrderedDict, deque
from file_funcs import dump_json, load_json

def get_args():
    argparser = argparse.ArgumentParser(description='Combine tex reports into 1 document')
    argparser.add_argument('--semester', '-s', help='Semester(folder name)', type=str, required=True)
    argparser.add_argument('--verbose', '-v', help='Print moves', action="store_true")
    args = argparser.parse_args()

    return args

def data_folder(semester):
    return "./data/"+semester+"/"

def extract_number(course_code):
    m = re.search(r"[0-9]{4}", course_code)
    if m is None:
        return None
    return int(m.group(0))

def get_participation_string(participation, language):
    if language == "EN":
        labels = ["Respondents","of"]
    elif language == "NO":
        labels = ["Antall besvarelser","av"]
    else:
        print("Unknown language: " + str(language))
        sys.exit(1)
    invited = int(participation["invited"])
    answered = int(participation["answered"])
    return r"\textbf{lcb}{labels[0]}:{rcb} {} {labels[1]} {} ({percentage:.1f}\%)".format(
        answered,
        invited,
        labels = labels,
        lcb = r"{",
        rcb = r"}",
        percentage = 0 if invited == 0 else (answered / invited * 100))

def tex_combine(semester, verbose=False):
    semester_folder = data_folder(semester)

    path = semester_folder+"/resources/course_names/all.json"
    course_names = load_json(path)

    path = semester_folder + "/outputs/courses.json"
    semester_data = load_json(path)

    tex_contents = deque([])

    with open(semester_folder+"/inputs/tex/header.tex") as f:
        tex_contents.append(f.read())

    course_codes = []
    for x in course_names:
        if x not in course_codes:
            course_codes.append(x)

    for x in semester_data:
        if x not in course_codes:
            course_codes.append(x)

    for course_code in course_codes:
        if course_code not in semester_data:
            continue
        course_data = semester_data[course_code]
        language = course_data["language"]
        if extract_number(course_code) >= 4000:
            langueage = "EN"
        else:
            language = "NO"

        path = semester_folder + "downloads/participation/" + course_code + ".json"
        participation_string = ""
        try:
            participation = load_json(path)
            if participation["answered"] <= 4:
                continue
            participation_string = get_participation_string(participation, language)
        except FileNotFoundError:
            print('Could not open '+path+' ! Skipping...')
            participation_string = ("\nThe course "+course_code+" numbers.json file is missing!\n")

        path = semester_folder + "outputs/tex/" + course_code + ".tex"
        try:
            with open(path,'r') as f:
                try:
                    course_name = course_names[course_code]
                except KeyError:
                    course_name = "Unknown course name"
                    print("Warning: Unknown course name:" + course_code)
                tex_contents.append(r"\section{"+course_code+r" - "+course_name+r"}")
                tex_contents.append(r"\label{course:"+course_code+r"}")
                tex_contents.append(participation_string)
                tex_contents.append(r'''
                \begin{minipage}[t]{\textwidth}
                \vspace*{-0.5cm}
                \vspace*{\fill}
                \noindent\makebox[\textwidth]{
                    \hspace{2.5cm}\includegraphics[trim=0 50 0 0,clip,width=1.7\textwidth]{../plots/COURSE.pdf}
                }%
                \end{minipage}
                \vspace*{0.2cm}
                '''.replace("COURSE", course_code))
                tex_contents.append(f.read())
                tex_contents.append(r"\newpage")
        except FileNotFoundError:
            print('Could not open '+path+' ! Skipping...')
            tex_contents.append("\nThe course "+course_code+" tex file is missing!\n")

    with open(semester_folder+"/inputs/tex/tail.tex") as f:
        tex_contents.append(f.read())

    tex_final = "\n\n".join(tex_contents)

    report_folder = semester_folder + "/outputs/report/"
    os.makedirs(report_folder, exist_ok = True)
    report_name = "fui-kk_report_"+semester+".tex"

    with open(report_folder+report_name, 'w') as f:
        f.write(tex_final)

if __name__ == '__main__':
    args = get_args()
    tex_combine(args.semester, args.verbose)

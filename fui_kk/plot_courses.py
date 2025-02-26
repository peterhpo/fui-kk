#!/usr/bin/env python3
"""This is a module that is used for generating plots that show how a
course has evolved."""

__authors__    = ["Ole Herman Schumacher Elgesem", "Lars Tveito"]
__copyright__  = "Lars Tveito"
__credits__    = ["Lars Tveito"]
__license__    = "MIT"

# The MIT License (MIT)

# Copyright (c) 2016 Lars Tveito

# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import multiprocessing, pipes, os, re
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import json
import sys
from collections import OrderedDict
from functools import partial
from copy import copy

from file_funcs import dump_json, load_json, print_json
from language import determine_language


def get_general_question(course_semester):
    language = course_semester["language"]
    general_questions = ["Hva er ditt generelle intrykk av kurset?",
                         "Hva er ditt generelle inntrykk av kurset?",
                         "What is your general impression of the course?",
                         "How do you rate the course in general?"]
    for question in general_questions:
        if question in course_semester:
            return question

    print("Cannot find general question: " + json.dumps(course_semester, indent=2))
    sys.exit(1)

def plot_course(course_name, courses, output, scales, semester):
    course = courses[course_name]
    general_question = get_general_question(course[semester])

    scale_text = list(reversed(scales[general_question]["order"]))
    scale_val = list(range(len(scale_text)))

    scale = scale_text

    semester_codes = list(course.keys())

    # Filter out semesters which had a different question:
    for semester_code in semester_codes:
        if general_question not in course[semester_code]:
            del course[semester_code]

    if semester not in semester_codes:
        print("Warning: the course {} doesn't have data for {}".format(course_name, semester))
        return

    semester_codes = list(course.keys())
    semesters      = list(course.items())

    end_index      = semester_codes.index(semester)+1
    semester_codes = semester_codes[0:end_index]
    semesters      = semesters[0:end_index]

    scores = []
    for semester_code in semester_codes:
        scores.append(course[semester_code][general_question]["average"])

    language = determine_language(general_question) # Defaults to None

    plot_title = ("General assessment since" if language == "EN" else
                  "Generell vurdering fra") # Default to norwegian
    plot_title = "{} {}".format(plot_title, semester_codes[0])

    fig = plt.figure(figsize=(10, 5), edgecolor='k')
    plt.title(plot_title)

    semester_nums = range(len(semester_codes))
    plt.plot(semester_nums, scores, marker='o', markersize=5)

    # Some space between between axis lines and points.
    plt.xlim(-0.2, len(semester_nums) - 0.8)

    # Semester codes along the x-axis.
    plt.xticks(semester_nums, semester_codes)

    # Rating descriptions along the y-axis
    plt.ylim(-0.5, len(scale)-0.5)
    plt.yticks(range(len(scale)), scale)

    axis = plt.gca()
    axis.yaxis.grid(True)
    plt.subplots_adjust(left=0.2, right=0.8, top=0.9, bottom=0.1)

    print("Generated plot: " + output+course_name+'.pdf')
    plt.savefig(output+course_name+'.pdf', format='pdf')
    plt.savefig(output+course_name+'.png', format='png')
    plt.close('all')

def generate_plots(courses, scales, semester_name):
    semester = load_json("./data/"+semester_name+"/outputs/courses.json")
    courses_to_plot = list(semester.keys())
    outdir = "".join(["./data/", semester_name, "/outputs/plots/"])
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    for c in courses_to_plot:
        plot_course(c, courses, outdir, scales, semester_name)

def plot_courses(semester):
    semester = sys.argv[1]
    courses = load_json("./data/courses.json")
    scales = load_json("./data/"+semester+"/outputs/scales.json")
    generate_plots(courses, scales, semester)

if __name__ == "__main__":
    plot_courses(sys.argv[1])

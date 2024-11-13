#!/usr/bin/env python3
"""This is a module that is used for generating plots that show how a
course has evolved."""

__authors__    = ["Ole Herman Schumacher Elgesem", "Lars Tveito", "Peter Hjelle Petersen-Øverleir"]
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

import os
import sys
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import json
from collections import OrderedDict
import itertools
import multiprocessing

from file_funcs import dump_json, load_json, print_json
from language import determine_language

color_map = {}  # Dictionary to map course codes to colors

def plot_course(args):
    """
    Plot the course evaluation over semesters, handling multiple entries per semester.
    """
    course_name, course_data, output, scales, semester = args
    
    try:
        scale_text = None

        # Determine the general question
        general_question = determine_general_question(course_data, semester)
        if general_question:
            scale_text = list(reversed(scales[general_question]["order"]))

        if scale_text is None:
            print(f"Warning: Unable to determine the general question for the course {course_name}")
            return

        scale_val = list(range(len(scale_text)))
        scale = scale_text

        semester_codes = list(course_data.keys())

        if not semester_codes:
            return

        semester_codes = sorted(semester_codes)

        all_semesters = generate_full_semester_range(semester_codes)

        scores_per_semester = OrderedDict()
        course_codes_per_semester = OrderedDict()

        for semester_code in all_semesters:
            if semester_code in course_data:
                data_list = course_data[semester_code]
                if isinstance(data_list, dict):
                    data_list = [data_list]

                for data in data_list:
                    general_question = get_general_question(data)
                    if general_question and general_question in data:
                        if semester_code not in scores_per_semester:
                            scores_per_semester[semester_code] = []
                            course_codes_per_semester[semester_code] = []
                        avg = data[general_question]["average"]
                        scores_per_semester[semester_code].append(float(avg) if avg != "None" else avg)
                        course_codes_per_semester[semester_code].append(data["course"]["code"])

        if not scores_per_semester:
            print(f"No valid semesters with data found for course {course_name}.")
            return

        language = determine_language(general_question)

        valid_semesters = [sem for sem in all_semesters if sem in scores_per_semester]

        if not valid_semesters:
            print(f"No valid semesters to plot for course {course_name}.")
            return

        plot_title = ("General assessment since " if language == "EN" else "Generell vurdering fra ") + valid_semesters[0]

        fig, ax = plt.subplots(figsize=(12, 6), edgecolor='k')
        plt.title(plot_title)

        valid_semester_nums = list(range(len(valid_semesters)))
        color_cycle = itertools.cycle(plt.get_cmap('tab10').colors)

        labeled_courses = set()  # Keep track of labeled course codes for the entire plot

        for i, semester_code in enumerate(valid_semesters):
            scores = scores_per_semester[semester_code]
            course_codes = course_codes_per_semester[semester_code]

            for j, (score, course_code) in enumerate(zip(scores, course_codes)):
                x_position = i

                # Assign a color to the course code if it hasn't been assigned yet
                if course_code not in color_map:
                    color_map[course_code] = next(color_cycle)
                current_color = color_map[course_code]

                # Only display the course code text if it hasn't been labeled in the entire plot
                if course_code not in labeled_courses:
                    text_label = course_code
                    labeled_courses.add(course_code)  # Add course code to the set
                else:
                    text_label = None  # No label if already added

                if score == "None":
                    median_score = (len(scale) - 1) / 2
                    ax.plot(x_position, median_score, 'x', color=current_color, alpha=0.7)
                    if text_label:  # Only show text if label is not None
                        plt.text(x_position + 0.06, median_score + 0.2, text_label, fontsize=9, va='bottom', ha='right', color=current_color, 
                                bbox=dict(facecolor='white', alpha=0.5))
                else:
                    ax.plot(x_position, score, 'o-', color=current_color, label=course_code if j == 0 else "", alpha=0.7)
                    if text_label:  # Only show text if label is not None
                        plt.text(x_position + 0.06, score + 0.2, text_label, fontsize=9, va='bottom', ha='right', color=current_color, 
                                bbox=dict(facecolor='white', alpha=0.5))

                # Connect points with a continuous line of the same color
                if i > 0:
                    previous_x_position = i - 1
                    previous_scores = scores_per_semester[valid_semesters[i - 1]]
                    for previous_score, previous_course_code in zip(previous_scores, course_codes_per_semester[valid_semesters[i - 1]]):
                        if previous_course_code == course_code:
                            if previous_score == "None":
                                previous_score = median_score
                            ax.plot([previous_x_position, x_position], [previous_score, score if score != "None" else median_score], 
                                    '-', color=current_color, alpha=0.7)

        plt.xlim(-0.5, len(valid_semesters) - 0.5)
        plt.xticks(valid_semester_nums, valid_semesters, rotation=45)
        plt.ylim(-0.5, len(scale) - 0.5)
        plt.yticks(range(len(scale)), scale)
        axis = plt.gca()
        axis.yaxis.grid(True)

        plt.subplots_adjust(left=0.2, right=0.8, top=0.9, bottom=0.2)
        
        output_file_base = f"{output}{course_name}"
        plt.savefig(f"{output_file_base}.pdf", format='pdf')
        plt.savefig(f"{output_file_base}.png", format='png')
        plt.close(fig)  # Ensure the figure is closed properly

        print(f"Generated plot: {output_file_base}.pdf")
    except Exception as err:
        print(f"Error plotting course {course_name}: {err}")

def determine_general_question(course_data, semester):
    """
    Determine the general question for a given semester's data.
    """
    general_questions = [
        "Hva er ditt generelle inntrykk av emnet?",
        "Hva er ditt generelle intrykk av kurset?",
        "Hva er ditt generelle inntrykk av kurset?",
        "What is your general impression of the course?",
        "How do you rate the course in general?"
    ]
    semester_data = course_data.get(semester, [])
    if isinstance(semester_data, dict):
        semester_data = [semester_data]

    for data in semester_data:
        for question in general_questions:
            if question in data:
                return question
    return None

def get_general_question(course_semester):
    """
    Retrieve the general question from the semester's data.
    """
    general_questions = [
        "Hva er ditt generelle inntrykk av emnet?",
        "Hva er ditt generelle intrykk av kurset?",
        "Hva er ditt generelle inntrykk av kurset?",
        "What is your general impression of the course?",
        "How do you rate the course in general?"
    ]
    for question in general_questions:
        if question in course_semester:
            return question
    return None

def generate_full_semester_range(semester_codes):
    """
    Generate a full range of semester codes based on the existing ones.
    """
    years_terms = sorted(set((int(sem[1:]), sem[0]) for sem in semester_codes if len(sem) > 1))
    full_range = []

    if not years_terms:
        return full_range

    min_year = min(years_terms, key=lambda x: x[0])[0]
    max_year = max(years_terms, key=lambda x: x[0])[0]

    for year in range(min_year, max_year + 1):
        for term in ['V', 'H']:
            full_range.append(f"{term}{year}")

    return full_range

def generate_plots(courses, scales, semester_name):
    """
    Generate plots for all courses for a specified semester.
    """
    semester_data_path = f"./data/{semester_name}/outputs/courses.json"
    semester = load_json(semester_data_path)
    courses_to_plot = list(semester.keys())
    outdir = f"./data/{semester_name}/outputs/plots/"
    os.makedirs(outdir, exist_ok=True)

    pool = multiprocessing.Pool()
    args = [(course_code, courses[course_code], outdir, scales, semester_name) for course_code in courses_to_plot]
    
    results = pool.map(plot_course, args)
    pool.close()
    pool.join()

    for result in results:
        if result:
            print(result)

def plot_courses(semester):
    """
    Plot courses for a specific semester.
    """
    courses = load_json("./data/aggregated_courses.json")
    scales = load_json(f"./data/{semester}/outputs/scales.json")
    generate_plots(courses, scales, semester)

def plot_all_semesters():
    """
    Plot courses for all semesters found in the data directory.
    """
    base_path = "./data/"
    semesters = [d for d in os.listdir(base_path) 
                 if os.path.isdir(os.path.join(base_path, d))]
    for semester in semesters:
        plot_courses(semester)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "all":
            plot_all_semesters()
        else:
            plot_courses(sys.argv[1])
    else:
        print("Usage: python3 script_name.py [SEMESTER|all]")

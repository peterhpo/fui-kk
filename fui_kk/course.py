#!/usr/bin/env python3
"""Create relevant statistics from individual responses"""

__authors__    = ["Ole Herman Schumacher Elgesem", "Peter Hjelle Petersen-Øverleir"]
__modified_by__ = ["Peter Hjelle Petersen-Øverleir"]
__copyright__  = "Ole Herman Schumacher Elgesem"
__license__    = "MIT"
# This file is subject to the terms and conditions defined in
# file 'LICENSE.txt', which is part of this source code package.

import os
import sys
import json
from collections import OrderedDict, defaultdict
from file_funcs import dump_json, load_json, path_join
from language import determine_language
from scales import answer_case

def generate_stats(responses, participation, scales, stats=None, course_code=None):
    if stats is None:
        stats = OrderedDict()

    started = int(participation["started"])
    answered = int(participation["answered"])
    if answered == 0:
        return None

    invited = int(participation["invited"])
    percentage = 100 * answered / invited if invited > 0 else 100

    stats["respondents"] = {
        "started": started,
        "answered": answered,
        "invited": invited,
    }
    stats["answer_percentage"] = percentage

    questions = OrderedDict()
    language = None

    for question in responses:
        if language is None:
            language = determine_language(question)

        if question in scales:
            question_answers = responses[question]
            scale_info = scales[question]
            answer_order = [answer_case(x) for x in reversed(scale_info["order"])]
            answer_ignore = set(answer_case(x) for x in scale_info["ignore"])

            counts = defaultdict(int)
            total, ctr = 0, 0
            all_ignored = True

            for answer in question_answers:
                normalized_answer = answer_case(answer)
                if normalized_answer not in answer_ignore:
                    all_ignored = False
                    try:
                        index = answer_order.index(normalized_answer)
                        ctr += 1
                        total += index
                        counts[normalized_answer] += 1
                    except ValueError:
                        continue

            if all_ignored:
                average = "None"
                average_text = "All answers ignored"
            else:
                average = total / ctr if ctr > 0 else "None"
                average_text = answer_order[int(round(average, 0))] if average != "None" else ""

            questions[question] = {
                "counts": dict(counts),
                "average": average,
                "average_text": average_text
            }

    stats["language"] = language
    stats["questions"] = questions
    return stats

def generate_stats_file(responses_path, participation_path, output_path, scales, course):
    responses = load_json(responses_path)
    participation = load_json(participation_path)

    stats = OrderedDict()
    stats["course"] = course
    
    stats = generate_stats(responses, participation, scales, stats, course["code"])
    
    if not stats:
        return
    
    if not stats["language"]:
        return
    
    dump_json(stats, output_path)

def generate_stats_dir(responses_dir, participation_dir, output_dir, scales, course_names, semester_name):
    for filename in os.listdir(responses_dir):
        if filename.endswith(".json"):
            course_code = os.path.splitext(filename)[0]
            course_name = course_names.get(course_code, "Unknown")
            
            course = {
                "code": course_code,
                "name": course_name,
                "semester": semester_name
            }
            
            responses_path = path_join(responses_dir, filename)
            participation_path = path_join(participation_dir, filename)
            output_path = path_join(output_dir, filename)
            generate_stats_file(responses_path, participation_path, output_path, scales, course)

def generate_stats_semester(semester_path, semester_name):
    outputs_dir = os.path.join(semester_path, "outputs")
    scales_path = os.path.join(outputs_dir, "scales.json")
    scales = load_json(scales_path)
    
    course_names = load_json("./resources/course_names/all.json")
    
    generate_stats_dir(
        os.path.join(outputs_dir, "responses"),
        os.path.join(semester_path, "downloads", "participation"),
        os.path.join(outputs_dir, "stats"),
        scales, course_names, semester_name)

if __name__ == '__main__':
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        sys.exit("Must specify a valid directory.")

    directory = sys.argv[1]
    for root, dirs, _ in os.walk(directory):
        for d in dirs:
            if "." not in d:
                os.makedirs(path_join(root,d,"inputs","md"), exist_ok=True)
                os.makedirs(path_join(root,d,"inputs","tex"), exist_ok=True)
        break

    for semester_dir in os.listdir(directory):
        semester_path = os.path.join(directory, semester_dir)
        if os.path.isdir(semester_path):
            generate_stats_semester(semester_path, semester_dir)

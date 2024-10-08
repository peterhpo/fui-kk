#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Combines all data for the semester into a shared json"""

__authors__    = ["Ole Herman Schumacher Elgesem", "Peter Hjelle Petersen-Øverleir"]
__copyright__  = "Ole Herman Schumacher Elgesem"
__license__    = "MIT"
# This file is subject to the terms and conditions defined in
# file 'LICENSE.txt', which is part of this source code package.
import os
import json
from collections import OrderedDict
from file_funcs import dump_json, load_json
from plot_courses import get_general_question

def get_semester_order(start_year, stop_year):
    start_year = int(start_year)
    stop_year = int(stop_year)
    s_order = []
    for i in range(start_year, stop_year):
        s_order.append("V" + str(i))
        s_order.append("H" + str(i))
    return s_order

def get_semesters(path):
    semester_order = get_semester_order(2000, 2030)
    semesters = []
    for root, subdirs, files in os.walk(path):
        semesters = list(filter(lambda x: x != ".git", subdirs))
        break

    indices = [semester_order.index(x) for x in semesters]
    semesters = [x for (y, x) in sorted(zip(indices, semesters))]
    return semesters

def load_course_info(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {filepath}: {e}")
        return {}

def generate_summary_report(data):
    summary = {}

    for course_code, semesters in data.items():
        total_responses = 0
        total_invited = 0
        total_rating_sum = 0
        total_rating_count = 0
        
        for semester, entries in semesters.items():
            for details in entries:
                # Skip entries where all answers are ignored
                general_question = get_general_question(details)
                if general_question:
                    rating_data = details.get(general_question, {})
                    if (rating_data.get("average") == "None" and 
                        rating_data.get("average_text") == "All answers ignored"):
                        continue
                
                respondents = details['respondents']
                total_responses += respondents['answered']
                total_invited += respondents['invited']

                if general_question:
                    rating_data = details.get(general_question, {})
                    
                    average = float(rating_data.get("average", 0)) if rating_data.get("average") != "None" else 0
                    counts = sum(rating_data.get("counts", {}).values())
                    total_rating_sum += average * counts
                    total_rating_count += counts

        avg_response_rate = (total_responses / total_invited * 100) if total_invited > 0 else 0
        avg_rating = (total_rating_sum / total_rating_count) if total_rating_count > 0 else 0
        
        summary[course_code] = {
            "total_responses": total_responses,
            "total_invited": total_invited,
            "average_response_rate": avg_response_rate,
            "average_rating": avg_rating
        }

    return summary

def aggregate_courses_with_replacements(course_data, course_info):
    aggregated_data = OrderedDict()

    # Preprocess replacements to make sure we know every course's target code
    course_replacements = {k: v["replacement_code"] for k, v in course_info.items() if "replacement_code" in v}

    # Copy existing course data to aggregated_data
    for course_code, semesters in course_data.items():
        if course_code not in aggregated_data:
            aggregated_data[course_code] = OrderedDict()
        for sem, details in semesters.items():
            if sem not in aggregated_data[course_code]:
                aggregated_data[course_code][sem] = []
            aggregated_data[course_code][sem].extend(details)

    # Iterate through each course and aggregate the child to the parent when necessary
    for course_code, semesters in course_data.items():
        # Determine if the course is a child, and if so, get its parent
        parent_course_code = course_replacements.get(course_code, course_code)

        if course_code != parent_course_code:  # The course is a child
            # Ensure the parent exists in `aggregated_data`
            if parent_course_code not in aggregated_data:
                aggregated_data[parent_course_code] = OrderedDict()

            # Add child course data to the parent's data
            for semester, details in semesters.items():
                if semester not in aggregated_data[parent_course_code]:
                    aggregated_data[parent_course_code][semester] = []
                aggregated_data[parent_course_code][semester].extend(details)

    return aggregated_data

if __name__ == '__main__':
    semesters = get_semesters("./data")
    courses = OrderedDict()
    
    for s in semesters:
        p = "./data/" + s + "/outputs/courses.json"
        semester = load_json(p)
        for course in semester:
            if course not in courses:
                courses[course] = OrderedDict()
            if s not in courses[course]:
                courses[course][s] = []
            courses[course][s].append(semester[course])

    dump_json(courses, "./data/courses.json")
    
    combined_data = load_json("./data/courses.json")
    course_info = load_course_info("./courses/courses_info.json")

    aggregated_courses = aggregate_courses_with_replacements(combined_data, course_info)
    dump_json(aggregated_courses, "./data/aggregated_courses.json")

    summary_report = generate_summary_report(aggregated_courses)
    dump_json(summary_report, "./data/summary_report.json")

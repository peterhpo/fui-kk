#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Divides course evaluation results among fui-members."""

__authors__    = ["Ole Herman Schumacher Elgesem", "Peter Hjelle Petersen-Øverleir"]
__modified_by__ = ["Peter Hjelle Petersen-Øverleir"]
__email__      = "olehelg@uio.no"
__copyright__  = "Ole Herman Schumacher Elgesem"
__credits__    = ["Ole Herman Schumacher Elgesem"]
__license__    = "MIT"
# This file is subject to the terms and conditions defined in
# file 'LICENSE.txt', which is part of this source code package.

import os
import sys
import json
import requests
from collections import OrderedDict
from bs4 import BeautifulSoup
from file_funcs import dump_json, load_json

def fetch_fui_members():
    url = "https://ififui.no/fagutvalget/"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch the webpage: {url}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    members = []

    # Retrieving members from the table (leder, nestleder and økonomiansvarlig)
    table = soup.find('table', class_='table')
    if table:
        rows = table.find_all('tr')[1:]  # Skip the header row
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                members.append(cols[1].text.strip())

    # Retrieving members from the <ul> section
    ul_header = soup.find(id="medlemmer")
    if ul_header:
        ul_section = ul_header.find_next("ul")
        if ul_section:
            lis = ul_section.find_all('li')
            for li in lis:
                name = li.text.split("(")[0].strip()
                members.append(name)
    
    return members

def course_divide(semester, people):
    p = f"./data/{semester}/outputs/courses.json"
    semester_data = load_json(p)
    courses = []
    for name, data in semester_data.items():
        answers = data["respondents"]["answered"]
        if answers > 4:
            courses.append((name, answers))
    courses = sorted(courses, reverse=True, key=lambda x: x[1])

    num = len(people)
    members = []
    for i in range(num):
        member = OrderedDict()
        member["name"] = people[i]
        member["answers"] = 0
        member["courses"] = []
        members.append(member)

    index = 0
    for course in courses:
        victim = members[index]
        victim["answers"] += course[1]
        victim["courses"].append(course[0])

        index = (index + 1) % num
    
    print(json.dumps(members, indent=1))

def main():
    if len(sys.argv) < 3:
        print("Usage: ./course_divide.py <num|names> semester")
        exit()

    try:
        num = int(sys.argv[1])
        people = ["Unknown"] * num
    except ValueError:
        names_input = sys.argv[1]
        if names_input.lower() == 'names':
            people = fetch_fui_members()
        else:
            people = names_input.split(',')
    
    semester = sys.argv[2]
    course_divide(semester, people)

if __name__ == "__main__":
    main()

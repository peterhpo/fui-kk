#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Downloads course codes and names from the University of Oslo website"""

__authors__    = ["Ole Herman Schumacher Elgesem", "Peter Hjelle Petersen-Øverleir"]
__modified_by__ = ["Peter Hjelle Petersen-Øverleir"]
__copyright__  = "Ole Herman Schumacher Elgesem"
__license__    = "MIT"

import os
import argparse
import requests
from collections import OrderedDict
from bs4 import BeautifulSoup

from file_funcs import dump_json

def get_args():
    """Parse command-line arguments."""
    argparser = argparse.ArgumentParser(description='Download course data from the University of Oslo website')
    argparser.add_argument('--url', '-u', help='Base URL to fetch course data from', type=str,
                           default='https://www.uio.no/studier/emner/matnat/ifi/')
    argparser.add_argument('--output', '-o', help='Output file for course data (JSON format)', type=str, required=True)
    argparser.add_argument('--filter', '-f', help='File with course codes to exclude', type=str)
    args = argparser.parse_args()
    return args

def write_page(content, path):
    """Saves the HTML content of a webpage to a file for later inspection."""
    dirname = os.path.dirname(path)
    os.makedirs(dirname, exist_ok=True)
    with open(path + ".html", 'wb') as f:
        f.write(content)

def fetch_course_replacement_info(url):
    """Fetch the replacement course information from the provided URL."""
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        message_box = soup.find("div", {"class": "vrtx-context-message-box uio-info-message blue grid-container"})
        if message_box:
            message_text = message_box.find("div", {"class": "message-text"})
            if message_text:
                replacement_link = message_text.find("a")
                if replacement_link:
                    replacement_url = replacement_link.get("href")
                    replacement_code = replacement_link.text.split(" ")[0]
                    return replacement_code
    return None

def course_dict(html):
    """Extract course codes, names, hrefs, and replacement information from the HTML content."""
    courses = OrderedDict()
    soup = BeautifulSoup(html, "html.parser")
    
    for td in soup.find_all("td", class_="vrtx-course-description-name"):
        a_tag = td.find("a")  # Find the <a> tag inside the td
        if a_tag:
            href = a_tag.get("href")  # Get the href attribute from the <a> tag
            l = td.text.split(" ")
            course_code = l[0]
            course_name = " ".join(l[2:-2])
            print(href)
            replacement_code = fetch_course_replacement_info(f"https://uio.no/{href}")
            courses[course_code] = {
                "name": course_name,
                "href": href,
                "replacement_code": replacement_code
            }
    
    return courses

def reverse_replacement_graph(courses):
    """Reverse the graph to map courses to the courses they replace."""
    reversed_graph = OrderedDict()
    for code, details in courses.items():
        replacement_code = details.get("replacement_code")
        if replacement_code:
            if replacement_code not in reversed_graph:
                reversed_graph[replacement_code] = []
            reversed_graph[replacement_code].append(code)
    
    return reversed_graph

def course_filter(courses, filters):
    """Filter out courses based on the provided filters."""
    if not filters:
        return courses
    filtered_courses = {code: name for code, name in courses.items() if all(substr not in code for substr in filters)}
    return filtered_courses

def fetch_courses(url, page=None):
    """Fetch course data from a given page. Also fetches discontinued courses if "page" is set"""
    new_url = url
    if page:
        new_url = f"{url}?filter.status=discontinued&page={page}"  # Fetches discontinued courses (relevant for INF- courses)
    response = requests.get(new_url)
    response.raise_for_status()  # Ensure we handle HTTP errors
    html = response.content.decode("utf-8")
    return course_dict(html)

def course_list(url, path, filters_path, max_pages=3):
    """Main function to fetch, filter, and save course data."""
    filters = []
    if filters_path:
        with open(filters_path) as f:
            filters = f.read().splitlines()

    all_courses = OrderedDict()
    
    for page in range(1, max_pages + 1):
        print(f"Fetching data from page {page}")
        courses = fetch_courses(url, page)
        all_courses.update(courses)
    courses = fetch_courses(url)
    all_courses.update(courses)

    # Filter out courses based on provided filters
    filtered_courses = course_filter(all_courses, filters)
    
    # Reverse the graph to map courses to the courses they replace
    reversed_graph = reverse_replacement_graph(filtered_courses)
    
    # Combine filtered courses with reversed graph info
    for course_code, details in filtered_courses.items():
        details["replaces"] = reversed_graph.get(course_code, [])

    dump_json(filtered_courses, path)

if __name__ == '__main__':
    args = get_args()
    course_list(args.url, args.output, args.filter)

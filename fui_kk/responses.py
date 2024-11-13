#!/usr/bin/env python3
"""Parses csv files and outputs json data for course."""

__authors__    = ["Ole Herman Schumacher Elgesem", "Peter Hjelle Petersen-Øverleir"]
__copyright__  = "Ole Herman Schumacher Elgesem"
__credits__    = ["Erik Vesteraas"]
__license__    = "MIT"
# This file is subject to the terms and conditions defined in
# file "LICENSE.txt", which is part of this source code package.

import os
import sys
import csv
import json
import argparse
from bs4 import BeautifulSoup
from collections import OrderedDict

from file_funcs import dump_json, load_json, path_join

def get_args():
    argparser = argparse.ArgumentParser(
                description = "Parse csv file(s) and output json course data")
    argparser.add_argument("--output", "-o", help="Output dir", type=str)
    argparser.add_argument("--input", "-i", help="Input dir/file", type=str)
    argparser.add_argument("--semester", "-s", default="all", help="Semester", type=str)

    args = argparser.parse_args()

    if args.semester:
        if args.semester == "all":
            dirs = next(os.walk('data'))[1]
            for d in dirs:
                if d.replace("/", "") == "all":
                    sys.exit("Error: Recursion check failed - 'all' folder!")
                if d[0] != ".":
                    os.system("python3 fui_kk/responses.py -s "+d)
            sys.exit()
        else:
            args.input = path_join("data",args.semester,"downloads/csv")
            args.output = path_join("data",args.semester,"outputs/responses")

    if not args.input or not args.output:
        sys.exit("Error: Specify input and output using -i and -o parameters, or semester using -s parameter")
    return args

def parse_course_csv(csv_filename):
    data = []
    with open(csv_filename, encoding='utf-8') as csv_file:
        for row in csv.reader(csv_file, delimiter=';'):
            data.append(row)
    
    if not data:
        return {} # Handle the case when the CSV is empty

    labels = data[0]
    responses_raw = data[1:]
    responses = OrderedDict()
    for l in labels:
        responses[l] = []

    for r in range(0, len(responses_raw)):
        if len(responses_raw[r]) != len(labels):
            print(f"Warning: Skipping row {r} in {csv_filename} because it does not match the header length. Something with the data went wrong... You should check the file on line {r+2}.")
            continue
        
        for i in range(0, len(labels)):
            responses[labels[i]].append(responses_raw[r][i])
    
    return responses

def init_csv_reader():
    # Hack
    csv_max = sys.maxsize
    overflow = True
    while overflow:
        overflow = False
        try:
            csv.field_size_limit(csv_max)
        except OverflowError:
            overflow = True
            csv_max = int(csv_max/16)

def parse_csv_files(input_path, output_dir):
    if not os.path.exists(input_path):
        sys.exit("Error: invalid input path '{}'".format(input_path))

    input_files = []
    if os.path.isfile(input_path):
        input_files.append(input_path)
    else:
        for (root, dirs, files) in os.walk(input_path):
            for file_x in files:
                if file_x.endswith(".csv"):
                    input_files.append(path_join(root,file_x))

    if os.path.exists(output_dir):
        if os.path.isfile(output_dir):
            sys.exit("Error: Out arg must be directory.")
    else:
        os.makedirs(output_dir)

    for csv_filename in input_files:
        coursename = csv_filename.replace(".csv","")
        coursename = coursename.replace(input_path, "")
        coursename = coursename.replace("/", "")
        content = parse_course_csv(csv_filename)
        dump_json(content, path_join(output_dir,coursename)+".json")

def main():
    args = get_args()
    init_csv_reader()
    parse_csv_files(args.input, args.output)

if __name__ == "__main__":
    main()

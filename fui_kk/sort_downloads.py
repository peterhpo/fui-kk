#!/usr/bin/env python3
"""Automatically sort downloaded data (html and csv) into folder structure based on file names."""

__authors__ = ["Ole Herman Schumacher Elgesem", "Peter Hjelle Petersen-Øverleir"]
__modified_by__ = ["Peter Hjelle Petersen-Øverleir"]
__copyright__ = "Ole Herman Schumacher Elgesem"
__credits__ = ["Erik Vesteraas"]
__license__ = "MIT"

import os
import re
import sys
from shutil import copyfile
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from file_funcs import path_join

def get_args():
    parser = ArgumentParser(description='Sort downloads into folder structure',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', type=str, default='./downloads', help='Input directory')
    parser.add_argument('-o', '--output', type=str, default='./data', help='Output directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print moves')
    parser.add_argument('-d', '--delete', action='store_true', help='Delete moved files')
    parser.add_argument('-e', '--exclude', type=str, default=r'(testskjema)|(XXX)|(\*\*\*)', help='Exclude regex')
    return parser.parse_args()

def main():
    args = get_args()
    exclude_pattern = re.compile(args.exclude)
    semester_pattern = re.compile(r'(V|H)[0-9]{4}')
    course_code_pattern = re.compile(r'(([A-Z]{1,5}-)?[A-Z]{1,5}[0-9]{3,4})([A-Z]{1,5})?')

    for root, _, files in os.walk(args.input):
        for file_x in files:
            path = path_join(root, file_x)
            if exclude_pattern.search(path):
                continue

            semester_match = semester_pattern.search(path)
            course_match = course_code_pattern.search(path)

            if not semester_match or not course_match:
                if args.verbose:
                    print(f"Skipped - {'No semester' if not semester_match else 'No course code'}: {path}")
                continue

            extension = os.path.splitext(path)[1][1:]
            folder_type = 'participation' if extension == 'json' else extension

            target_folder = path_join(args.output, semester_match.group(0), 'downloads', folder_type)
            os.makedirs(target_folder, exist_ok=True)

            new_path = path_join(target_folder, course_match.group(0) + '.' + extension)
            
            if args.delete:
                try:
                    os.remove(new_path)
                except:
                    pass
                os.rename(path, new_path)
            else:
                copyfile(path, new_path)

            if args.verbose:
                print(f"{path} -> {new_path}")

    if args.delete:
        while args.delete:
            args.delete = False
            for root, subdirs, files in os.walk(args.input):
                if not subdirs and not files:
                    os.rmdir(root)
                    if args.verbose:
                        print(f"Removed empty directory: {root}")
                    args.delete = True

if __name__ == '__main__':
    main()

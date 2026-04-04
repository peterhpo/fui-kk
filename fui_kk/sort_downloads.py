#!/usr/bin/env python3
"""Automatically sort downloaded data (html and csv) into folder structure
based on file names, and remove column "500 kr? :)" in CSVs for semesters
between 2023 and 2026.
"""

__authors__ = ["Ole Herman Schumacher Elgesem", "Peter Hjelle Petersen-Øverleir"]
__modified_by__ = ["Peter Hjelle Petersen-Øverleir"]
__copyright__ = "Ole Herman Schumacher Elgesem"
__credits__ = ["Erik Vesteraas"]
__license__ = "MIT"

import os
import re
from shutil import copyfile
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from file_funcs import path_join


def get_args():
    parser = ArgumentParser(
        description='Sort downloads into folder structure and clean CSVs',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-i', '--input', type=str, default='./downloads',
                        help='Input directory')
    parser.add_argument('-o', '--output', type=str, default='./data',
                        help='Output directory')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print moves')
    parser.add_argument('-d', '--delete', action='store_true',
                        help='Delete moved files')
    parser.add_argument('-e', '--exclude', type=str,
                        default=r'(testskjema)|(XXX)|(\*\*\*)',
                        help='Exclude regex')
    return parser.parse_args()


def semester_year_in_range(semester_str: str) -> bool:
    """semester_str like 'V2023' or 'H2026'."""
    try:
        year = int(semester_str[-4:])
    except ValueError:
        return False
    return 2023 <= year <= 2026


def process_file(args, path, exclude_pattern, semester_pattern, course_code_pattern):
    if exclude_pattern.search(path):
        return f"Excluded: {path}"

    semester_match = semester_pattern.search(path)
    course_match = course_code_pattern.search(path)

    if not semester_match or not course_match:
        return f"Skipped - {'No semester' if not semester_match else 'No course code'}: {path}"

    semester = semester_match.group(0)
    extension = os.path.splitext(path)[1][1:]  # without dot

    folder_type = 'participation' if extension == 'json' else extension
    target_folder = path_join(args.output, semester, 'downloads', folder_type)
    os.makedirs(target_folder, exist_ok=True)

    new_path = path_join(target_folder, course_match.group(0) + '.' + extension)

    # CSV + semester in [2023, 2026] -> use pandas to drop column
    if extension.lower() == 'csv' and semester_year_in_range(semester):
        try:
            df = pd.read_csv(path, sep=';', dtype=str)
            if '500 kr? :)' in df.columns:
                df = df.drop(columns=['500 kr? :)'])
                if args.verbose:
                    print(f'Removed column "500 kr? :)" from {path}')
            elif 'Want 500 kr?' in df.columns:
                df = df.drop(columns=['Want 500 kr?'])
                if args.verbose:
                    print(f'Removed column "Want 500 kr?" from {path}')
            else:
                if args.verbose:
                    print(f'No "500 kr? :)" or "Want 500 kr?" column in {path}')
            df.to_csv(new_path, sep=';', index=False)
            if args.delete:
                os.remove(path)
        except Exception as e:
            # On error, fall back to simple copy/move
            if args.verbose:
                print(f"Error cleaning CSV {path}: {e}, copying instead.")
            if args.delete:
                try:
                    os.remove(new_path)
                except Exception:
                    pass
                os.rename(path, new_path)
            else:
                copyfile(path, new_path)
    else:
        # Non-CSV or outside target year range: just copy/move
        if args.delete:
            try:
                os.remove(new_path)
            except Exception:
                pass
            os.rename(path, new_path)
        else:
            copyfile(path, new_path)

    return f"{path} -> {new_path}"


def main():
    args = get_args()
    exclude_pattern = re.compile(args.exclude)
    semester_pattern = re.compile(r'(V|H)[0-9]{4}')
    course_code_pattern = re.compile(r'(([A-Z]{1,5}-)?[A-Z]{1,5}[0-9]{3,4})([A-Z]{1,5})?')

    files_to_process = []
    for root, _, files in os.walk(args.input):
        for file_x in files:
            path = path_join(root, file_x)
            files_to_process.append(path)

    with ThreadPoolExecutor() as executor:
        future_to_path = {
            executor.submit(
                process_file,
                args,
                path,
                exclude_pattern,
                semester_pattern,
                course_code_pattern
            ): path
            for path in files_to_process
        }

        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                result = future.result()
                if args.verbose and result:
                    print(result)
            except Exception as e:
                print(f"Error processing file {path}: {e}")

    if args.delete:
        # Remove empty directories in input
        changed = True
        while changed:
            changed = False
            for root, subdirs, files in os.walk(args.input):
                if not subdirs and not files:
                    os.rmdir(root)
                    if args.verbose:
                        print(f"Removed empty directory: {root}")
                    changed = True


if __name__ == '__main__':
    main()

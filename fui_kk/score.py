import os
import json
import argparse
import numpy as np


def find_all(dictionary, search_key):
    hits = []
    for key, value in dictionary.items():
        if isinstance(value, dict):
            hits.extend(find_all(value, search_key))
        elif key == search_key:
            hits.append(dictionary[key])
    return hits


def calculate_average(semester):
    with open(os.path.join("data", semester, "outputs", "courses.json"), "r") as f:
        courses = json.load(f)
    averages = find_all(courses, "average")
    numeric_averages = []
    for avg in averages:
        if avg is not None:
            try:
                numeric_averages.append(float(avg))
            except ValueError:
                pass

    if numeric_averages:
        return round(np.mean(numeric_averages), 2)
    else:
        return None


def sort_averages(averages):
    # Extract years and sort them
    years = sorted(set(int(k[1:]) for k in averages.keys()))

    # Rebuild the dictionary in the desired order: V(year), H(year)
    sorted_averages = {}
    for year in years:
        spring_key = f"V{year}"
        autumn_key = f"H{year}"
        if spring_key in averages:
            sorted_averages[spring_key] = averages[spring_key]
        if autumn_key in averages:
            sorted_averages[autumn_key] = averages[autumn_key]

    return sorted_averages


def update_js_file(averages):
    js_file_path = './resources/web/copy/vurdering.js'

    try:
        with open(js_file_path, 'r') as f:
            js_content = f.read()

        avg_score_str = 'var avg_score = '
        start_index = js_content.index(avg_score_str) + len(avg_score_str)
        end_index = js_content.index('}', start_index)
        
        print(start_index, end_index)

        # Creating the updated `avg_score` dictionary string to replace the old one
        new_avg_score = ',\n    '.join(f"'{key}': {value:.2f}" for key, value in averages.items())
        new_avg_score = '{\n    ' + new_avg_score + '\n  }'

        new_js_content = js_content[:start_index] + new_avg_score + js_content[end_index + 1:]

        with open(js_file_path, 'w') as f:
            f.write(new_js_content)

        print(f"Updated {js_file_path} with new averages")
    except Exception as e:
        print(f"Error updating {js_file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Calculate the average score for a semester")
    parser.add_argument("semester", help="The semester to calculate the average for, or 'all' for all semesters")
    args = parser.parse_args()

    semester = args.semester

    all_averages = {}

    if semester == "all":
        dirs = next(os.walk('data'))[1]
        for d in dirs:
            if d[0] != ".":
                try:
                    avg = calculate_average(d)
                    if avg is not None:
                        all_averages[d] = avg
                        print(f"Semester average for {d} is {avg} (or {avg + 1} in scale used by vurdering.js)")
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error processing semester {d}: {e}")

        overall_average = round(np.mean(list(all_averages.values())), 2) if all_averages else None
        if overall_average is not None:
            print(f"Overall average for all semesters is {overall_average} (or {overall_average + 1} in scale used by vurdering.js)")
        else:
            print("No valid averages found for any semester.")
    else:
        try:
            avg = calculate_average(semester)
            if avg is not None:
                all_averages[semester] = avg
                print(f"Semester average for {semester} is {avg} (or {avg + 1} in scale used by vurdering.js)")
            else:
                print(f"No valid averages found for semester {semester}.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error processing semester {semester}: {e}")

    # Sort the averages by year
    sorted_averages = sort_averages(all_averages)

    # Update the JavaScript file
    update_js_file(sorted_averages)


if __name__ == '__main__':
    main()

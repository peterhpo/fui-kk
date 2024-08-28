#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Downloads CSV reports for a user from nettskjema.uio.no using OAuth 2.0"""

__authors__ = ["Erik Vesteraas", "Peter Hjelle Petersen-Øverleir"]
__modified_by__ = ["Peter Hjelle Petersen-Øverleir"]
__copyright__ = "Erik Vesteraas"
__license__ = "MIT"
# This file is subject to the terms and conditions defined in
# file 'LICENSE.txt', which is part of this source code package.

import os
import sys
import locale
import argparse
import pickle
import requests
import json
from dotenv import load_dotenv

from file_funcs import path_join, path_clean, filename_clean, dump_json
from api_funcs import obtain_token, save_token, api_request, load_token

def get_args():
    argparser = argparse.ArgumentParser(description='Download report data from nettskjema.uio.no')
    argparser.add_argument('--out', '-o', help='Output directory (default="./downloads")', type=str, default='./downloads')
    argparser.add_argument('--filter', '-f', help='String to filter by', type=str)
    argparser.add_argument('--csv', help='Download CSV files', action="store_true")
    args = argparser.parse_args()

    # Set all to True if none are provided
    if not args.csv:
        args.csv = True

    return args

def write_to_file(folder, name, extension, content):
    if not os.path.exists(folder):
        os.makedirs(folder)
    filename = path_clean(path_join(folder, name) + '.' + extension)
    with open(filename, 'w', encoding="utf-8") as f:
        f.write(content)

def read_list(path):
    try:
        with open(path, 'r') as f:
            return f.read().split("\n")
    except FileNotFoundError:
        return []

def read_binary(path):
    try:
        with open(path, 'rb') as fp:
            return pickle.load(fp)
    except FileNotFoundError:
        return None

def write_binary(path, data):
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(path, 'wb') as fp:
        pickle.dump(data, fp)

def os_encode(msg):
    os_encoding = locale.getpreferredencoding()
    return msg.encode(os_encoding)

def error(msg, exception=None, *, label=None):
    if label:
        print(f"\n***FUI-KK ERROR: {label}***")
    else:
        print("\n***FUI-KK ERROR***")
    if exception:
        print(f"Exception: {type(exception)}\nMessage: {exception}\n")
    print(msg)
    # sys.exit(-1)

def download_files(args):
    downloaded = read_list(args.out + "/downloaded.txt")

    formdata = read_binary(args.out + "/formdata.dat")
    if not formdata:
        forms_url = "https://api.nettskjema.no/v3/form/me"
        response = api_request(forms_url)
        forms = response.json()
        
        # Check if forms contain expected keys
        try:
            formdata = [(form['title'], form['formId'], form['numberOfDeliveredSubmissions']) for form in forms]
        except KeyError as e:
            error(f"Key error: {e}. Expected keys not found in the response", e)
        
        write_binary(args.out + "/formdata.dat", formdata)

    if args.filter:
        filtered = [x for x in formdata if args.filter in x[0]]
        print(f'Filter matched {len(filtered)} of {len(formdata)} forms')
        formdata = filtered

    out_path = path_clean(args.out)
    csv_path = path_join(out_path, 'csv')
    stats_path = path_join(out_path, 'stats')
    
    stats_aggregated = {}

    for (name, form_id, number_of_delivered_submissions) in formdata:
        try:
            if str(form_id) in downloaded:
                print(f"Skipping {name} (id={form_id})")
                continue
            print(f"Fetching {name} (id={form_id})")
        except UnicodeEncodeError as e:
            error(f"Form id={form_id}\nForm name: {os_encode(name)}", e, label="Non-unicode codepage")
        
        name_cleaned = filename_clean(name)

        # Fetch invitations data
        try:
            invites_url = f"https://api.nettskjema.no/v3/form/{form_id}/invitations"
            response = api_request(invites_url)
            if response.ok:
                invitations = [json.loads(line) for line in response.text.splitlines()]
                num_invited = len(invitations)
                num_answered = number_of_delivered_submissions
                response_rate = (num_answered / num_invited) * 100 if num_invited > 0 else 0

                stats = {
                    "started": 0,
                    "answered": number_of_delivered_submissions,
                    "invited": num_invited,
                    "response_rate": response_rate
                }
                
        except Exception as e:
            error(f"Failed to fetch invitations for {name} (id={form_id})", label=f"HTTP {e}")
            stats = {
                "started": 0,
                "answered": number_of_delivered_submissions,
                "invited": 0,
                "response_rate": 0
            }
                    
        dump_json(stats, f"{stats_path}/{name_cleaned}.json")

        # Aggregate statistics
        stats_aggregated[name] = stats

        if args.csv:
            csv_url = f"https://api.nettskjema.no/v3/form/{form_id}/csv-report"
            response = api_request(csv_url)
            if response.ok:
                write_to_file(csv_path, name_cleaned, 'csv', response.content.decode())
            else:
                error(f"Failed to fetch CSV report for {name} (id={form_id})", label=f"HTTP {response.status_code}")
        
        with open(args.out + "/downloaded.txt", 'a') as f:
            f.write(str(form_id) + "\n")

    # Write the aggregated stats to a file
    stats_filename = 'stats.json'
    dump_json({"respondents": stats_aggregated}, path_join(stats_path, stats_filename))

def main():
    load_dotenv()
    
    args = get_args()
    token_data = load_token()

    if not token_data:
        token_data = obtain_token()
        save_token(token_data)

    try:
        download_files(args)
    except requests.exceptions.TooManyRedirects as e:
        error("Sometimes nettskjema doesn't like us.\nJust wait a little while and continue\nby rerunning the script.", e, label="Nettskjema")

if __name__ == '__main__':
    main()

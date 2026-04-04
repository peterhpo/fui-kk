#!/usr/bin/env python3
"""Moves reports (raw data) from the local folder to WebDAV via SSH tunnel."""

__authors__    = ["Ole Herman Schumacher Elgesem", "Peter Hjelle Petersen-Øverleir"]
__modified_by__ = ["Peter Hjelle Petersen-Øverleir"]
__license__    = "MIT"

import os
import sys
import argparse

from dotenv import load_dotenv

from webdav_funcs import WebdavTunnel

HARDCODED_WEBDAV_BASE_URL = (
    "https://www-dav.mn.uio.no/"
    "ifi/livet-rundt-studiene/organisasjoner/fui/"
)

def get_args():
    argparser = argparse.ArgumentParser(description='Upload reports to vortex')
    argparser.add_argument(
        '--input', '-i',
        help='Input directory (default="./data")',
        type=str, default='./data'
    )
    argparser.add_argument(
        '--output', '-o',
        help='Output directory (logical base path on WebDAV, default="/")',
        type=str, default='/KURS/'
    )
    argparser.add_argument('--semester', '-s', help='Semester', type=str)
    argparser.add_argument(
        '--verbose', '-v',
        help='Print moves', action="store_true"
    )
    args = argparser.parse_args()

    if not args.semester:
        print("Need to specify semester, ex: -s V2026")
        sys.exit(1)
    if len(args.semester) != 5:
        print("Invalid format for semester, ex: -s V2026")
        sys.exit(1)

    return args


def copy_file(fs, src, dst, verbose=False):
    if verbose:
        print("Uploading:", src, "->", dst)
    if not os.path.exists(src):
        print(f"Warning: cannot copy file {src} - does not exist.")
        return

    # Ensure remote directory exists
    remote_dir = os.path.dirname(dst)
    if remote_dir and not fs.exists(remote_dir):
        fs.makedirs(remote_dir, exist_ok=True)

    # Copy from local filesystem to WebDAV
    fs.put_file(src, dst)


def upload_files(fs, src_dir, dest_dir, semester, verbose=False):
    """
    Moves files from args.input (local) to args.output (logical base under WebDAV).
    """
    src_dir_csv = f"{src_dir}/{semester}/downloads/csv/"
    src_dir_json_stats = f"{src_dir}/{semester}/outputs/stats/"

    for responses_csv in os.listdir(src_dir_csv):
        course = responses_csv[:-4]  # remove ".csv" to only have the course code

        to_folder = f"{dest_dir}{course}/{semester}/"

        from_csv = src_dir_csv + responses_csv
        from_json = src_dir_json_stats + course + ".json"

        to_csv = to_folder + responses_csv
        to_json = f"{to_folder}{course}_stats.json"

        copy_file(fs, from_csv, to_csv, verbose)
        copy_file(fs, from_json, to_json, verbose)


if __name__ == '__main__':
    args = get_args()

    load_dotenv()
    webdav_user = os.getenv("WEBDAV_USERNAME")   # FUI user, e.g. 'fui'
    webdav_password = os.getenv("WEBDAV_PASSWORD")
    twofa_user = os.getenv("SSH_USER_2FA")       # your personal UiO user, e.g. 'peterhp'

    if not webdav_user or not webdav_password:
        print("Need WEBDAV_USERNAME and WEBDAV_PASSWORD in environment.")
        sys.exit(1)
    if not twofa_user:
        print("Need SSH_USER_2FA (your 2FA UiO username) in environment.")
        sys.exit(1)

    with WebdavTunnel(
        base_url=HARDCODED_WEBDAV_BASE_URL,
        webdav_user=webdav_user,
        webdav_password=webdav_password,
        twofa_user=twofa_user,
    ) as fs:
        upload_files(fs, args.input, args.output, args.semester, args.verbose)

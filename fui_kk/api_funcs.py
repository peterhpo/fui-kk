#!/usr/bin/env python3
"""Functions to authenticate with the nettskjema API using tokens and some standard requests."""

__authors__    = ["Peter Hjelle Petersen-Øverleir"]
__copyright__  = "Peter Hjelle Petersen-Øverleir"
__credits__    = ["Peter Hjelle Petersen-Øverleir"]
__license__    = "MIT"

import requests
from requests.auth import HTTPBasicAuth
import datetime
import json
import os
import time
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def init_session():
    session = requests.Session()
    retrier = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retrier)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "Nettskjema-Downloader"})
    return session

def obtain_token(session):
    load_dotenv()
    token_url = "https://authorization.nettskjema.no/oauth2/token"
    client_id = os.getenv('API_CLIENT_ID')
    client_secret = os.getenv('API_SECRET')

    data = {
        'grant_type': 'client_credentials',
    }

    response = session.post(token_url, data=data, auth=HTTPBasicAuth(client_id, client_secret))

    print("Request URL:", token_url)
    print("Request Data:", data)
    print("Response Status Code:", response.status_code)
    print("Response Text:", response.text)

    response.raise_for_status()
    return response.json()

def save_token(token_data):
    token_data['expires_at'] = datetime.datetime.now().timestamp() + token_data['expires_in']
    with open('token.json', 'w') as f:
        json.dump(token_data, f)

def load_token():
    try:
        with open('token.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def check_and_refresh_token(session):
    token_data = load_token()

    if not token_data:
        return obtain_and_save_new_token(session)

    now = datetime.datetime.now()
    expires_at = datetime.datetime.fromtimestamp(token_data['expires_at'])

    if now >= expires_at:
        print("Token expired. Obtaining a new token...")
        return obtain_and_save_new_token(session)
    else:
        return token_data

def obtain_and_save_new_token(session):
    token_data = obtain_token(session)
    save_token(token_data)
    return token_data

def api_request(session, url, method='GET', data=None, params=None, timeout=300, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            token_data = check_and_refresh_token(session)
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}

            if method == 'GET':
                response = session.get(url, headers=headers, params=params, timeout=timeout)
            elif method == 'POST':
                response = session.post(url, headers=headers, json=data, timeout=timeout)
            elif method == 'PUT':
                response = session.put(url, headers=headers, json=data, timeout=timeout)
            elif method == 'PATCH':
                response = session.patch(url, headers=headers, json=data, timeout=timeout)
            elif method == 'DELETE':
                response = session.delete(url, headers=headers, json=data, timeout=timeout)
            else:
                raise ValueError("Unsupported HTTP method")

            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 400:
                retries += 1
                if retries >= max_retries:
                    print(f"Max retries exceeded for URL: {url}")
                    raise http_err
                print(f"HTTP 400 error on {url}, retrying {retries}/{max_retries}...")
                time.sleep(2 ** retries)  # Exponential backoff
            else:
                raise http_err

        except requests.exceptions.RequestException as req_err:
            raise req_err

# Endpoint-specific functions
def get_form_info(session, form_id):
    url = f"https://api.nettskjema.no/v3/form/{form_id}/info"
    return api_request(session, url).json()

def get_form_submissions(session, form_id):
    url = f"https://api.nettskjema.no/v3/form/{form_id}/answers"
    return api_request(session, url).json()

def create_submission(session, form_id, submission_data):
    url = f"https://api.nettskjema.no/v3/form/{form_id}/submission"
    return api_request(session, url, method='POST', data=submission_data).json()

def delete_submission(session, form_id, submission_id):
    url = f"https://api.nettskjema.no/v3/form/{form_id}/submission/{submission_id}"
    return api_request(session, url, method='DELETE').json()

def update_codebook(session, form_id, codebook_data):
    url = f"https://api.nettskjema.no/v3/form/{form_id}/codebook"
    return api_request(session, url, method='PUT', data=codebook_data).json()

def get_user_info(session):
    url = "https://api.nettskjema.no/v3/me"
    return api_request(session, url).json()

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
from dotenv import load_dotenv

def obtain_token():
    load_dotenv()
    token_url = "https://authorization.nettskjema.no/oauth2/token"
    client_id = os.getenv('API_CLIENT_ID')
    client_secret = os.getenv('API_SECRET')

    
    data = {
        'grant_type': 'client_credentials',
    }
    
    response = requests.post(token_url, data=data, auth=HTTPBasicAuth(client_id, client_secret))
    
    # Add debugging here
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

def check_and_refresh_token():
    token_data = load_token()
    
    if not token_data:
        return obtain_and_save_new_token()
    
    now = datetime.datetime.now()
    expires_at = datetime.datetime.fromtimestamp(token_data['expires_at'])
    
    if now >= expires_at:
        print("Token expired. Obtaining a new token...")
        return obtain_and_save_new_token()
    else:
        return token_data

def obtain_and_save_new_token():
    token_data = obtain_token()
    save_token(token_data)
    return token_data

def api_request(url, method='GET', data=None, params=None, timeout=300):
    token_data = check_and_refresh_token()
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    if method == 'GET':
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data, timeout=timeout)
    elif method == 'PUT':
        response = requests.put(url, headers=headers, json=data, timeout=timeout)
    elif method == 'PATCH':
        response = requests.patch(url, headers=headers, json=data, timeout=timeout)
    elif method == 'DELETE':
        response = requests.delete(url, headers=headers, json=data, timeout=timeout)
    else:
        raise ValueError("Unsupported HTTP method")
    
    response.raise_for_status()
    return response

# Endpoint-specific functions
def get_form_info(form_id):
    url = f"https://api.nettskjema.no/v3/form/{form_id}/info"
    return api_request(url).json()

def get_form_submissions(form_id):
    url = f"https://api.nettskjema.no/v3/form/{form_id}/answers"
    return api_request(url).json()

def create_submission(form_id, submission_data):
    url = f"https://api.nettskjema.no/v3/form/{form_id}/submission"
    return api_request(url, method='POST', data=submission_data).json()

def delete_submission(form_id, submission_id):
    url = f"https://api.nettskjema.no/v3/form/{form_id}/submission/{submission_id}"
    return api_request(url, method='DELETE').json()

def update_codebook(form_id, codebook_data):
    url = f"https://api.nettskjema.no/v3/form/{form_id}/codebook"
    return api_request(url, method='PUT', data=codebook_data).json()

def get_user_info():
    url = "https://api.nettskjema.no/v3/me"
    return api_request(url).json()

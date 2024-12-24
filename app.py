
import requests, os, yaml, signal
import pandas as pd
from flask import Flask, request, render_template, render_template_string, redirect, url_for
from hubspot import HubSpot
# Import the airbyte_app function from airbyte_hub.py
from Airbyte_HubSpot import airbyte_app


yml_path = os.getcwd() + '\\tokens.yaml'


app = Flask(__name__)

# OAuth 2.0 credentials of hubspot
CLIENT_ID = '46a9699b-6de9-4e5a-aef4-6e38aaeffb22'
CLIENT_SECRET = '742140b0-f917-4a75-830b-e7c178a43c63'
INSTALL_URL = f'https://app.hubspot.com/oauth/authorize?client_id=46a9699b-6de9-4e5a-aef4-6e38aaeffb22&redirect_uri=http://localhost:5000&scope=crm.objects.line_items.read%20content%20crm.schemas.deals.read%20crm.objects.carts.read%20media_bridge.read%20marketing-email%20automation%20crm.pipelines.orders.read%20crm.objects.subscriptions.read%20timeline%20oauth%20crm.objects.owners.read%20forms%20transactional-email%20crm.objects.users.read%20tickets%20crm.objects.users.write%20e-commerce%20crm.objects.marketing_events.read%20crm.schemas.custom.read%20crm.objects.custom.read%20crm.objects.feedback_submissions.read%20sales-email-read%20crm.objects.goals.read%20crm.objects.companies.read%20crm.lists.read%20crm.objects.deals.read%20crm.schemas.contacts.read%20crm.objects.contacts.read%20crm.schemas.companies.read'

# Function to load data from a YAML file
def load_yaml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file) or []
    except FileNotFoundError:
        return []
    except yaml.YAMLError as e:
        print(f"Error reading YAML file: {e}")
        return []

# Function to save data to a YAML file
def save_to_yaml_file(data, filename):
    """Helper function to save data to a YAML file."""
    if not data:
        return
    
    existing_data = load_yaml_file(filename)
    existing_hub_ids = {row['hub_id'] for row in existing_data}
    
    # Update existing data
    for row in data:
        for existing_row in existing_data:
            if existing_row['hub_id'] == row['hub_id']:
                existing_row.update(row)
                break
        else:
            existing_data.append(row)

    with open(filename, 'w') as file:
        yaml.safe_dump(existing_data, file)

def is_yaml_empty():
    data = load_yaml_file(yml_path)
    return len(data) == 0
# Function to get new access token using refresh token
def get_new_access_token(refresh_token):
    url = 'https://api.hubapi.com/oauth/v1/token'
    
    data = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token
    }
    
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        updated_data = response.json()
        return updated_data
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Function to get access token info
def get_access_token_info(token):
    url = f"https://api.hubapi.com/oauth/v1/access-tokens/{token}"
    
    headers = {
        'accept': "application/json",
        'authorization': f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to fetch access token info. Status Code: {response.status_code}")
        print("Response:", response.text)
        return None

# Function to get tokens using authorization code
def get_tokens(authorization_code):
    url = 'https://api.hubspot.com/oauth/v1/token'
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': 'http://localhost:5000',
        'code': authorization_code
    }

    response = requests.post(url, data=data)
    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Route for the home page
@app.route('/')
def home():

    authorization_code = request.args.get('code')
    print('authorization_code get when', authorization_code)
    if authorization_code:
        tokens = get_tokens(authorization_code)
        if tokens:
            access_token = tokens['access_token']
            refresh_token = tokens['refresh_token']
            # hubspot_client = HubSpot(access_token=access_token)
            access_token_info = get_access_token_info(access_token)
            if access_token_info:
                user = access_token_info['user']
                hub_id = access_token_info['hub_id']
            # Convert hub_id to string
                hub_id_str = str(hub_id)
                user_name = user.split('@')[0]
                
                # Concatenate user and hub_id_str
                name = user_name + '_' + hub_id_str
                user_data = [{
                    'hub_id': hub_id,
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': user,
                    'naming_convention': name
                }]
                save_to_yaml_file(user_data, yml_path)
                print('inside')
                airbyte_app(refresh_token)

                return render_template('success.html', user_data=user_data)

        return render_template('success.html', user_data=[])
    else:
        # Load stored data from YAML
        user_data = load_yaml_file(yml_path)
        return render_template('home.html', authorization_url=INSTALL_URL, user_data=user_data)

# Route to process user selections
@app.route('/process_selection', methods=['POST'])
def process_selection():
    print('airbyte_app')
    selected_hub_ids = request.form.getlist('fetch_now')
    print('selected_hub_ids', selected_hub_ids)
    all_user_data = load_yaml_file(yml_path)    
    # Track if any changes were made
    data_updated = False

    for row in all_user_data:
        if str(row['hub_id']) in selected_hub_ids:
            refresh_token = row.get('refresh_token')
            print('refresh_token', refresh_token)
            if refresh_token:
                airbyte_app(refresh_token)

    if data_updated:
        # Re-save the updated tokens to the YAML file only if updates occurred
        save_to_yaml_file(all_user_data, yml_path)

    return render_template('success.html', user_data=[row for row in all_user_data if str(row['hub_id']) in selected_hub_ids])


if __name__ == '__main__':
    print('starting')
    app.run(debug=True)
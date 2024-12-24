import requests
import json, os
import yaml

# Load environment variables
from dotenv import load_dotenv
load_dotenv()  # This will load the variables from a .env file

yaml_file_path = os.getcwd() + '\\tokens.yaml'
json_file_path = os.getcwd() + '\\user_data.json'

# Replace with your Airbyte web app URL
WEBAPP_URL = os.getenv('WEBAPP_URL')  # Use environment variable for URL

# Your client_id and client_secret of airbyte
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

HUBSPOT_CLIENT_ID = os.getenv('HUBSPOT_CLIENT_ID')
HUBSPOT_CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_BUCKET_REGION = os.getenv('S3_BUCKET_REGION')
S3_BUCKET_ACCESS_KEY = os.getenv('S3_BUCKET_ACCESS_KEY')
S3_BUCKET_SECRET_KEY = os.getenv('S3_BUCKET_SECRET_KEY')

# Source and Destination IDs
SOURCE_DEF_ID = os.getenv('SOURCE_DEF_ID')
DESTINATION_DEF_ID = os.getenv('DESTINATION_DEF_ID')
WORKSPACE_ID = os.getenv('WORKSPACE_ID')

def get_access_token():
    token_url = f"{WEBAPP_URL}/api/v1/applications/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(token_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        return access_token
    else:
        print(f"Failed to get access token: {response.status_code}")
        return None

def get_sources(access_token, workspace_id):
    source_url = f"{WEBAPP_URL}/api/v1/sources/list"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "workspaceId": workspace_id
    }
    response = requests.post(source_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        sources = response.json().get('sources', [])
        return sources
    else:
        print(f"Failed to retrieve sources: {response.status_code}")
        return []

def get_destinations(access_token, workspace_id):
    destination_url = f"{WEBAPP_URL}/api/v1/destinations/list"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "workspaceId": workspace_id
    }
    response = requests.post(destination_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        destinations = response.json().get('destinations', [])
        return destinations
    else:
        print(f"Failed to retrieve destinations: {response.status_code}")
        return []

def get_connections(access_token, workspace_id):
    connection_url = f"{WEBAPP_URL}/api/v1/connections/list"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "workspaceId": workspace_id
    }
    response = requests.post(connection_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        connections = response.json().get('connections', [])
        # Save connections to file
        with open('connections.json', 'w') as json_file:
            json.dump(connections, json_file, indent=4)
        return connections
    else:
        print(f"Failed to retrieve connections: {response.status_code}")
        return []

def create_source(access_token, refresh_token, name):
    existing_sources = get_sources(access_token, WORKSPACE_ID)
    if any(src['name'] == name for src in existing_sources):
        print(f"Source with name '{name}' already exists.")
        return
    
    source_url = f"{WEBAPP_URL}/api/public/v1/sources"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        'authorization': f"Bearer {access_token}"
    }

    payload = {
        "sourceDefinitionId": SOURCE_DEF_ID,
        "name": name,
        "workspaceId": WORKSPACE_ID,
        "configuration": {
            "sourceType": "hubspot",
            "credentials": {
                "client_id": HUBSPOT_CLIENT_ID,
                "client_secret": HUBSPOT_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "credentials_title": 'OAuth Credentials'
            },
            "enable_experimental_streams": True
        }
    }

    response = requests.post(source_url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"Source '{name}' created successfully.")
    else:
        print(f"Failed to create source '{name}': {response.status_code} - {response.text}")

def create_destination(access_token, name, s3_bucket_path):
    existing_destinations = get_destinations(access_token, WORKSPACE_ID)
    if any(dest['name'] == name for dest in existing_destinations):
        print(f"Destination with name '{name}' already exists.")
        return
    
    destination_url = f"{WEBAPP_URL}/api/public/v1/destinations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        'authorization': f"Bearer {access_token}"
    }

    payload = {
        "definitionId": DESTINATION_DEF_ID,
        "workspaceId": WORKSPACE_ID,
        "name": name,
        "configuration": {
            "destinationType": 's3',
            "s3_bucket_region": S3_BUCKET_REGION,
            "access_key_id": S3_BUCKET_ACCESS_KEY,
            "secret_access_key": S3_BUCKET_SECRET_KEY,
            "s3_bucket_name": S3_BUCKET_NAME,
            "s3_bucket_path": s3_bucket_path,
            "format": {
                "format_type": "Parquet"
            }
        }
    }

    response = requests.post(destination_url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"Destination '{name}' created successfully.")
    else:
        print(f"Failed to create destination '{name}': {response.status_code} - {response.text}")

def run_connection(access_token, connection_id):
    
    connection_url = f"{WEBAPP_URL}/api/public/v1/connections/{connection_id}"
    print(connection_url)
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
    }

    payload = {
     "schedule": {
        "scheduleType": "cron"
    },
    "namespaceFormat": None
}
    response = requests.patch(connection_url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"Connection '{connection_id}' scheduled successfully.")
    else:
        print(f"Failed to scheduled connection '{connection_id}': {response.status_code} - {response.text}")

def create_connection(access_token, source_id, destination_id, name):
         # Retrieve all existing connections
    existing_connections = get_connections(access_token, WORKSPACE_ID)
    if any(conn['name'] == name for conn in existing_connections):
        print(f"Connection with name '{name}' already exists.")
        return
    
    connection_url = f"{WEBAPP_URL}/api/public/v1/connections"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        'authorization': f"Bearer {access_token}"
    }
    payload = {
    "sourceId": source_id,
    "destinationId": destination_id,
    "name": name,
    "workspaceId": WORKSPACE_ID,
    "status": "active",
    "configurations": {"streams": [
            {
                "syncMode": "full_refresh_append",
                "name": "campaigns"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "companies",
            },
            {
                "syncMode": "full_refresh_append",
                "name": "contact_lists"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "contacts",
            },
            {
                "syncMode": "full_refresh_append",
                "name": "contacts_form_submissions"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "contacts_list_memberships",
            },
            {
                "syncMode": "full_refresh_append",
                "name": "deal_pipelines",
            },
            {
                "syncMode": "full_refresh_append",
                "name": "deals_archived"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "deals",
            },
            {
                "syncMode": "full_refresh_append",
                "name": "form_submissions"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "engagements",
            },
            {
                "syncMode": "full_refresh_append",
                "name": "engagements_emails"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "forms"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "goals"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "line_items"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "owners"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "products"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "tickets"
            },
            {
                "syncMode": "full_refresh_append",
                "name": "workflows"
            }
        ] },
      "schedule": {
        "scheduleType": "cron",
        "cronExpression": "0 00 7 * * ?"
    },
    "dataResidency": "auto",
    "namespaceFormat": None,
    "nonBreakingSchemaUpdatesBehavior": "ignore"
}


    response = requests.post(connection_url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"Connection '{name}' created successfully.")
    else:
        print(f"Failed to create connection '{name}': {response.status_code} - {response.text}")

def yaml_to_json(yaml_data):
    if yaml_data is None:
        raise ValueError("yaml_data is None")
    json_data = {}
    
    # Process each item in the list
    for item in yaml_data:
        # Assuming each item in the list is a dictionary with 'naming_convention' key
        if isinstance(item, dict):
            user = item.get('naming_convention', '')
            
            if user:
                # Define names based on the user
                source_name = f"{user}_HubSpot"
                des_name = f"{user}_S3"
                con_name = f"{user}_HubSpot_S3"
                
                # Add the JSON structure to the json_data dictionary
                json_data[user] = {
                    "sources": {
                        "refresh_token": item.get('refresh_token'),
                        "name": source_name
                    },
                    "destination": {
                        "name": des_name,
                        "s3_bucket_path": f"{user}/${{YEAR}}/${{MONTH}}/${{DAY}}"
                    },
                    "connections": {
                        "name": con_name
                    }
                }
    
    return json_data
def load_yaml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            if data is None:
                print(f"Warning: The file {file_path} is empty or contains invalid YAML.")
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except yaml.YAMLError as e:
        print(f"Error reading YAML file: {e}")
        return []

# Function to read YAML file and convert to JSON format
def process_yaml_to_json(yaml_file_path, json_file_path):
    # Load YAML data
    yaml_data = load_yaml_file(yaml_file_path)
    if yaml_data is None:
        print(f"No data found in {yaml_file_path}")
        return
    
    # Convert YAML data to JSON format
    json_data = yaml_to_json(yaml_data)
    
    # Write JSON data to a file
    with open(json_file_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)

# Test load_yaml_file
yaml_data = load_yaml_file(yaml_file_path)

# Test yaml_to_json
if yaml_data is not None:
    json_data = yaml_to_json(yaml_data)

    # Save JSON data
    with open(json_file_path, 'w') as json_file:
        json.dump(json_data, json_file)


def airbyte_app(refresh_token):
    print('start airbyte new_refresh_token')

    access_token = get_access_token()
    if access_token:
        workspace_id = WORKSPACE_ID
        print('read file')
        process_yaml_to_json(yaml_file_path, json_file_path)
        with open('user_data.json', 'r') as file:
            user_data = json.load(file)

        # Create sources and destinations
        for user, data in user_data.items():
            exist_user = refresh_token

            source_params = data.get('sources', {})
            if source_params:
                if source_params.get('refresh_token') == refresh_token:
                    name = data['sources'].get('name', '')
                    print('target name', name)
                    create_source(access_token, exist_user, name)

            destination_params = data.get('destination', {})
            if destination_params:
                if source_params.get('refresh_token') == refresh_token:
                    create_destination(access_token, destination_params.get("name", ""), destination_params.get("s3_bucket_path", ""))

        # Get sources and destinations after creation
        source_list = get_sources(access_token, workspace_id)
        destination_list = get_destinations(access_token, workspace_id)

        # Create connections if needed
        for user, data in user_data.items():
            # Move extraction of parameters inside the loop
            source_params = data.get('sources', {})
            destination_params = data.get('destination', {})
            connection_params = data.get('connections', {})

            if source_params.get('refresh_token') == refresh_token:
                source_token = source_params.get('refresh_token')
                print('source_token', source_token)
                print('refresh_token', refresh_token)

                if connection_params:
                    source_name = source_params.get("name", "")
                    destination_name = destination_params.get("name", "")
                    connection_name = connection_params.get("name", "")

                    result = {
                        "connection_name": connection_params.get("name", ""),
                        "source_name": source_params.get("name", ""),
                        "destination_name": destination_params.get("name", "")
                    }

                    print('result', result)

                    # Find source and destination IDs
                    source_id = next((src['sourceId'] for src in source_list if src['name'] == source_name), None)
                    destination_id = next((dest['destinationId'] for dest in destination_list if dest['name'] == destination_name), None)

                    if source_id and destination_id:
                        create_connection(access_token, source_id, destination_id, connection_name)
                    else:
                        print(f"Source ID or Destination ID not found for '{source_name}' or '{destination_name}'")

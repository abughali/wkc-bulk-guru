import requests
import urllib3
import os
import csv
from dotenv import load_dotenv
urllib3.disable_warnings()

load_dotenv()  # take environment variables from .env.

cpd_host = os.environ.get('CPD_HOST')
api_key = os.environ.get('API_KEY')
catalog_id = os.environ.get('CATALOG_ID')
username = os.environ.get('USERNAME')
password = os.environ.get('PASSWORD')
env_type = os.environ.get('ENV_TYPE','SW') # Default is Software

"""
This function generates an IBM Cloud Pak for Data bearer token using the provided credentials from the env variables above.

It determines whether the environment is a cloud-based service (SaaS) or an on-premises deployment (SW) based on the `env_type` variable.
If the environment is a cloud-based service, the function constructs an API key-based authorization URL and makes a POST request to generate a bearer token.
If the environment is an on-premises deployment, the function constructs an authorization URL and payload, and makes a POST request to generate a bearer token.
If the request is successful, the function extracts the bearer token from the response and sets the `Authorization` header of the `headers` dictionary
to include the bearer token in the subsequent API calls.

"""

def authorize():
    """
    Generate a bearer token from provided CPD credentials.

    https://cloud.ibm.com/apidocs/cloud-pak-data#getauthorizationtoken
    """

    if env_type == "SAAS":

        url = f"https://iam.cloud.ibm.com/identity/token?grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}"

        try:
            response = session.post(url, verify=False)
        except:
            raise ValueError(f"Error authenticating...")      

    else:

        url = f"https://{cpd_host}/icp4d-api/v1/authorize"

        payload = {
            "username": username,
            "password": password
        }

        try:
            response = session.post(url, json=payload, verify=False)
        except:
            raise ValueError(f"Error authenticating...")
        
    if response.status_code == 200:
            
        access_token = response.json()['access_token'] if env_type == "SAAS" else response.json()['token']
        headers['Authorization'] = f"Bearer {access_token}"
            
    else:
        raise ValueError(f"Error authenticating...\nResponse code: {response.status_code}\nResponse text:{response.text}")



def scanCatalogDataAssets(catalog_id):
    catalog_assets = []
    remaining_assets_to_get = -1
    next_param = None

    while True:
        url = f"https://{cpd_host}/v2/asset_types/data_asset/search?catalog_id={catalog_id}"
        if next_param:
            url += f"&bookmark={next_param}"
        payload = {
            "query":"*:*",
            "limit":200
        }
        response = session.post(url, headers=headers, json=payload, verify=False)

        if response.status_code != 200:
            raise ValueError(f"Error scanning catalog: {response.text}")
        else:
            if 'next' in response.json():
                next_param = response.json()['next']['bookmark']

        if remaining_assets_to_get == -1:
            remaining_assets_to_get = response.json()['total_rows']
            catalog_assets.extend(response.json()['results'])
            if remaining_assets_to_get <= payload['limit']:
                break
            else:
                remaining_assets_to_get -= len(response.json()['results'])
        elif remaining_assets_to_get < payload['limit']:
            catalog_assets.extend(response.json()['results'][remaining_assets_to_get*-1:])
            break
        elif remaining_assets_to_get == payload['limit']:
            catalog_assets.extend(response.json()['results'])
            break
        else:
            catalog_assets.extend(response.json()['results'])
            remaining_assets_to_get -= len(response.json()['results'])
    
    return catalog_assets

def scanDataAsset(catalog_id, asset_id):
    asset_columns = []

    url =  f"https://{cpd_host}/v2/data_assets/{asset_id}/columns/?catalog_id={catalog_id}"

    response = session.get(url, headers=headers, verify=False)

    if response.status_code != 200:
        raise ValueError(f"Error scanning asset: {response.text}")
    else:
        asset_columns.extend(response.json()['resources'])
    return asset_columns


headers = {
    'Content-Type': "application/json",
    }

session = requests.Session()
authorize()
assets = scanCatalogDataAssets(catalog_id)

with open('csv_file.csv', 'w') as f:
    writer = csv.writer(f)
    for asset in assets:
        #print(asset['metadata']['asset_id'] + "," + asset['metadata']['name'])
        asset_columns = scanDataAsset(catalog_id, asset['metadata']['asset_id'])
        for column in asset_columns:
            try:
                row = [asset['metadata']['name'] , column['data_asset']['columns'][0]['name'] , column['column_info'][f"{column['data_asset']['columns'][0]['name']}"]['column_description']]
            except KeyError:
                row = [asset['metadata']['name'] , column['data_asset']['columns'][0]['name'] , None]
            writer.writerow(row)

session.close()    
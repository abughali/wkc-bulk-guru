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
headers = {
    'Content-Type': "application/json",
    }

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
        except requests.RequestException as e:
            raise SystemExit("Error Authenticating : " + str(e))  

    else:

        url = f"https://{cpd_host}/icp4d-api/v1/authorize"

        payload = {
            "username": username,
            "password": password
        }

        try:
            response = session.post(url, json=payload, verify=False)
        except requests.RequestException as e:
            raise SystemExit("Error Authenticating : " + str(e))
        
    if response.status_code == 200:
            
        access_token = response.json()['access_token'] if env_type == "SAAS" else response.json()['token']
        headers['Authorization'] = f"Bearer {access_token}"
            
    else:
        raise ValueError(f"Error authenticating...\nResponse code: {response.status_code}\nResponse text:{response.text}")

"""
Description: Deletes assets by their IDs using an HTTP DELETE request.
Parameters:
 - ids: A list of asset IDs to be deleted, comma separated, max 20 ids at a time, currently we are passing only one by one from csv.
Returns: None

"""

def deleteAssetById(id):
    asset_id = ""

    url = f"https://{cpd_host}/v2/assets/bulk?catalog_id={catalog_id}&asset_ids={id}"

    response = session.delete(url, headers=headers, verify=False)

    if response.status_code != 207:
        raise ValueError(f"Error deleting catalog: {response.text}")
    else:
        print ("Asset deletion response: " + response.text)



session = requests.Session()
authorize()


with open('assets_to_delete.csv') as csvfile:
    reader = csv.reader(csvfile, skipinitialspace=True, delimiter=',')
    for row in reader:
       for column in row:
            deleteAssetById (column)

session.close()
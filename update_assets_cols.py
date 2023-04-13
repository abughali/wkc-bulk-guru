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
This function retrieves the ID of an asset in a catalog based on its name.

Parameters:
- name (str): The name of the asset to search for.

Returns:
- asset_id (str): The ID of the asset with the specified name, if it exists in the catalog.

The `json` parameter of the request is set to a payload that contains a query to search for the asset by name, along with a limit of 20 result.

Checks the response to ensure that at exactly one asset was found, otherwise it raises an error

"""

def getAssetByName(name):
    asset_id = ""

    url = f"https://{cpd_host}/v2/asset_types/data_asset/search?catalog_id={catalog_id}"

    payload = {
            "query":f"asset.name:{name}",
            "limit":20
    }
    response = session.post(url, headers=headers, json=payload, verify=False)

    if response.status_code != 200:
        raise ValueError(f"Error scanning catalog: {response.text}")
    else:
        assert response.json()['total_rows'] == 1, f'Asset {name} is either not found or duplicated'
        asset_id = response.json()['results'][0]['metadata']['asset_id']
    
    return asset_id

"""
This function constructs a JSON patch element for assigning a description to a column of a data asset.

Parameters:
- column (str): The name of the column to assign a description to.
- description (str): The description to assign to the column.

Returns:
- payload_element (dict): A dictionary that represents the JSON patch element for the column description assignment.

The `op` field of the element is set to `'add'`, indicating that a new value should be added to the specified path.
The function returns the `payload_element` dictionary, which is used as part of a larger JSON patch payload for updating the column descriptions of a data asset.
"""

def assignDescriptionToColumn(column, description):
    payload_element = {
      'op': 'add',
      'path': f'/{column}/column_description',
      'value': f'{description}'
    }
    return payload_element

"""
This function updates the columns descriptions of an asset in a catalog.
It takes three parameters: asset_id, which is the ID of the asset to be updated, asset_name,
which is the name of the asset, and payload, which is the new description to be added to the asset.
"""    

def updateDescr(asset_id, asset_name, payload):

    url = f"https://{cpd_host}/v2/assets/{asset_id}/attributes/column_info?catalog_id={catalog_id}"
    
    response = session.patch(url, headers=headers, json=payload, verify=False)

    print("Asset " + asset_name + " : " + str(response.status_code))


"""
This code iterates over the rows of the CSV file and adds the values to a nested dictionary
where the first column is the outer key and the second and third columns are the inner keys and values, respectively.

Sample.csv (No Header: Asset Name, Column Name, Column Description)
STUDENTS,ID, Student Identifier
STUDENTS,NAME,Student Name
STUDENTS,JOBROLE,Student Job Role

"""
with open('descr_all_assets.csv') as csvfile:
    reader = csv.reader(csvfile, skipinitialspace=True, delimiter=',')
    data = {}
    for row in reader:
        if row[0] not in data:
            data[row[0]] = {}
        data[row[0]][row[1]] = row[2]


headers = {
    'Content-Type': "application/json",
    }

session = requests.Session()
authorize()

"""
This block of code updates the descriptions of assets columns in the catalog.
The code loops through a dictionary called `data` from above, which contains the names of the assets, their columns and the descriptions to be added to each column.
For each asset in the dictionary, the code calls the `getAssetByName` function to get the asset ID,
and then loops through the descriptions and calls the `assignDescriptionToColumn` function to create a payload of column descriptions.
Finally, the code calls the `updateDescr` function to update the asset's columns descriptions.
If there's an error during the update process, the code prints an error message to the console.
"""

for key, value in data.items():
    try:
        asset_id =  getAssetByName(key)
        payload = []
        for col_name, col_descr in value.items():
            payload.append(assignDescriptionToColumn( col_name, col_descr))
        updateDescr(asset_id, key, payload)    
    except AssertionError as msg:
        print ("ERROR: " + str(msg))

session.close()
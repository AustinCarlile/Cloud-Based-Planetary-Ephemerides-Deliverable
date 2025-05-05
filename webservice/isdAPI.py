from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
import boto3
import brotli
import hashlib
import pvl
import json
import os
import shutil
import sys

app = FastAPI()

# Set AWS access parameters from environmental variables
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
region_name = os.environ.get('AWS_REGION', 'us-west-2')  # Default to 'us-west-2' if not set

# Initialize DynamoDB client
# This allows us to get the list of DynamoDB tables
client = boto3.client(
    'dynamodb',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

# Initialize DynamoDB resource
# This allows us to interact with a specific DynamoDB table
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id = aws_access_key_id,
    aws_secret_access_key = aws_secret_access_key,
    region_name=region_name
)

# Get DynamoDB table name from client, returns first table
response = client.list_tables()
table_name = response['TableNames'][0]

# Reference the DynamoDB table
table = dynamodb.Table(table_name)

# Pydantic model for item input validation
class Item(BaseModel):
    ID: str
    Isd: str

# Adapted from Microsoft Copilot generated code
# Recursive function to parse string number values from isd dictionary into integers or floats
def parse_number_string(isd_dict):
    
    # If dictionary, search through each value in every key
    if isinstance(isd_dict, dict):
        return {key: parse_number_string(value) for key, value in isd_dict.items()}
        
    # If list, search through every item
    elif isinstance(isd_dict, list):
        return [parse_number_string(item) for item in isd_dict]
    
    # If string, parse it
    elif isinstance(isd_dict, str):
        
        # Try to convert string to integer
        try:
            return int(isd_dict)
        except ValueError: 
            try:                              # If error, try to conver to float
                return float(isd_dict)
            except ValueError:                # If error, return original string
                return isd_dict

# End of adapted code
        
# Create a mini label string from a label file
def create_mini_label(input_file):
    
    # Opening label file
    with open(input_file, 'r') as label_file:
        label_dict = pvl.load(label_file)

    # Populate miniLabelDict with acceptable groups
    mini_label_dict = {key:label_dict['IsisCube'][key] for key in ['Core', 'Instrument', 'BandBin', 'Kernels']}

    # Add Label object to mini label dictionary
    mini_label_dict['Label'] = label_dict['Label']

    # Convert mini label dictionary to string
    mini_label_string = str(mini_label_dict)

    return mini_label_string
   
# Create a hash from a mini label string 
def create_hash(mini_label_string):

    # Creating hash of encoded MiniLabel string
    hash_data = hashlib.sha256(mini_label_string.encode())

    # Creating hexidecimal version of hash
    hash_hex = hash_data.hexdigest()

    return hash_hex
   
# API Endpoint for sending label file and receiving isd back
@app.post("/getIsd")
async def get_isd(request: Request):
    
    # Get request from client, then decompress and decode it
    label = await request.body()
    label_uncompress = brotli.decompress(label)
    label_string = label_uncompress.decode()
    
    temp_file = 'temp.lbl'
    
    # Write label string to file to use for isd generation
    with open(temp_file, 'w') as label_file:
        label_file.write(label_string)
    
    # Set spiceinit variable
    spiceinit_cmd = f'spiceinit from={temp_file}'
    os.system (spiceinit_cmd)
    
    # Create a mini label and hash from label file
    mini_label = create_mini_label(temp_file)
    isd_hash = create_hash(mini_label)
    
    # Check if isd exists by searching database with hash
    serverResponse = table.get_item(
            Key = {
                'id': isd_hash
            }
        )
    
    # If serverResponse dictionary only has one item (a metadata item) that means no isd returned, generate isd
    if(len(serverResponse) == 1):
        
        # Generate an isd from label file
        requested_isd = os.system(f'isd_generate {temp_file} -v')

        # Reads isd file as dictionary
        with open('temp.json', 'r') as isd_file:
            isd_dict = json.load(isd_file, parse_int = str, parse_float = str)
            
        # Sends item with hash id and isd value to table, then saves response
        table.put_item(
            Item = {
                'id': isd_hash,
                'isd': isd_dict
            }
        )

        # Get isd back from server
        serverResponse = table.get_item(
            Key = {
                'id': isd_hash
            }
        )
        
    # Remove temporary label file
    os.remove(temp_file)
    
    # Remove server response metadata, return isd key values only
    output_dict = {key:serverResponse['Item'][key] for key in ['isd']}
    
    # Remove isd key, only have inner values
    output_dict = output_dict['isd']
    
    # Parse string values in isd dictionary and convert into int or float when applicable
    output_dict = parse_number_string(output_dict)
    
    # Load output_dict as a json string
    output_string = json.dumps(output_dict)
    
    # Encode and compress isd json string
    output_encode = output_string.encode()
    output_compress = brotli.compress(output_encode)
    
    # Send isd back to client
    return Response(content = output_compress, media_type = "application/octet-stream")

# Run the app with: uvicorn isdAPI:app --reload

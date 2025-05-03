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

# Create DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url='http://localhost:8000')

# Create ISD table if it does not exist already
try:
    response = dynamodb.create_table(
        TableName='ISD',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )
except: # if it does exist, skip
    pass

# Variable to access ISD table
table = dynamodb.Table('ISD')

# Pydantic model for item input validation
class Item(BaseModel):
    ID: str
    Isd: str

# adapted from Microsoft Copilot generated code
# recursive function to parse string number values from isd dictionary into integers or floats
def parse_number_string(isd_dict):
    
    # if dictionary, search through each value in every key
    if isinstance(isd_dict, dict):
        return {key: parse_number_string(value) for key, value in isd_dict.items()}
        
    # if list, search through every item
    elif isinstance(isd_dict, list):
        return [parse_number_string(item) for item in isd_dict]
    
    # if string, parse it
    elif isinstance(isd_dict, str):
        
        # Try to convert string to integer
        try:
            return int(isd_dict)
        except ValueError: 
            try:                              # if error, try to conver to float
                return float(isd_dict)
            except ValueError:                # if error, return original string
                return isd_dict

# end of adapted code
        
# Create a mini label string from a label file
def create_mini_label(input_file):
    
    # opening label file
    with open(input_file, 'r') as label_file:
        label_dict = pvl.load(label_file)

    # populate miniLabelDict with acceptable groups
    mini_label_dict = {key:label_dict['IsisCube'][key] for key in ['Core', 'Instrument', 'BandBin', 'Kernels']}

    #  Add Label object to miniLabelDict
    mini_label_dict['Label'] = label_dict['Label']

    # convert mini label dictionary to string
    mini_label_string = str(mini_label_dict)

    return mini_label_string
   
# Create a hash from a mini label string 
def create_hash(mini_label_string):

    # creating hash of encoded MiniLabel string
    hashData = hashlib.sha256(mini_label_string.encode())

    # creating hexidecimal version of hash
    hashHex = hashData.hexdigest()

    # return hexidecimal hash
    return hashHex
    
@app.post("/getIsd")
async def get_isd(request: Request):
    
    # get request from client, then decompress and decode it
    label = await request.body()
    label_uncompress = brotli.decompress(label)
    label_string = label_uncompress.decode()
    
    temp_file = 'temp.lbl'
    
    # write label string to file to use for isd generation
    with open(temp_file, 'w') as label_file:
        label_file.write(label_string)
    
    # set spiceinit variable
    spiceinit_cmd = f'spiceinit from={temp_file} web=true'
    os.system (spiceinit_cmd)
    
    # create a mini label and hash from label file
    mini_label = create_mini_label(temp_file)
    isd_hash = create_hash(mini_label)
    
    # check if isd exists by searching database with hash
    serverResponse = table.get_item(
            TableName='ISD',
            Key = {
                'id': isd_hash
            }
        )
    
    # if serverResponse dictionary only has one item (a metadata item) that means no isd returned, generate isd
    if(len(serverResponse) == 1):
        
        # generate an isd from label file
        requested_isd = os.system(f'isd_generate {temp_file} -v')

        # reads isd file as dictionary
        with open('temp.json', 'r') as isd_file:
            isd_dict = json.load(isd_file, parse_int = str, parse_float = str)
            
        # sends item with hash id and isd value to table, then saves response
        table.put_item(
            TableName='ISD',
            Item = {
                'id': isd_hash,
                'isd': isd_dict
            }
        )

        # get isd back from server
        serverResponse = table.get_item(
            TableName='ISD',
            Key = {
                'id': isd_hash
            }
        )
        
    os.remove(temp_file)
    
    # remove server response metadata, return isd key values only
    output_dict = {key:serverResponse['Item'][key] for key in ['isd']}
    
    # remove isd key, only have inner values
    output_dict = output_dict['isd']
    
    # parse string values in isd dictionary and convert into int or float when applicable
    output_dict = parse_number_string(output_dict)
    
    # load output_dict as a json string
    output_string = json.dumps(output_dict)
    
    # encode and compress isd json string
    output_encode = output_string.encode()
    output_compress = brotli.compress(output_encode)
    
    # send isd back to client
    return Response(content = output_compress, media_type = "application/octet-stream")

# Run the app with: uvicorn isdAPI:app --port=8080 --reload

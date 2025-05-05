import brotli
import json
import os
import pathlib
import requests
import sys

# Get label file name and url (ip and port) from user
inLabel = sys.argv[1]
url = sys.argv[2]

# Find path to currect program and create a returned_isds folder if it doesnt exist yet
path = pathlib.Path(__file__).parent.resolve()
os.makedirs(f'{path}/returned_isds', exist_ok=True)

# Send a label file and getting an ISD called "test_isd.json" back
def test_send(inLabel, url):
    
    # Add /getIsd endpoint to url
    url += "/getIsd"
    
    # Read label file into a byte stream
    with open(inLabel, 'r', errors = 'ignore') as label_file:
        label_bytes = label_file.read()
    
    # Encode and compress label byte stream
    label_encode = label_bytes.encode()
    label_compress = brotli.compress(label_encode)
    
    # Send compressed label byte stream to server and get response back
    response = requests.post(url, data = label_compress)
    
    # Uncompress and decode isd response
    response_uncompress = brotli.decompress(response.content)
    decode_response = response_uncompress.decode()                           
    
    # Create an output file for isd
    outputFile = f"{path}/returned_isds/test_isd.json"
    
    # Load isd response as dictionary
    isd_dict = json.loads(decode_response)
    
    # Serializes dictionary to json object and writes to file
    with open(outputFile, 'w') as isd_output:
        json.dump(isd_dict, isd_output, indent = 2)
    
if __name__ == "__main__":
    
    # Test every file in data directory
    #for file in os.listdir(f'{path}/data/'):
    #     test_send(f'{path}/data/{file}')
    
    # Test a single file input by user
    test_send(f"{path}/{inLabel}", url)

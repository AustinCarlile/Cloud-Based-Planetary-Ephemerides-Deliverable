import brotli
import json
import os
import pathlib
import requests
import sys

# get label file name and url (ip and port) from user
inLabel = sys.argv[1]
url = sys.argv[2]

# find path to currect program and create a returned_isds folder if it doesnt exist yet
path = pathlib.Path(__file__).parent.resolve()
os.makedirs(f'{path}/returned_isds', exist_ok=True)

# sending a label file and getting an isd back
def test_send(inLabel, url):
    
    # add /getIsd endpoint to url
    url += "/getIsd"
    
    # read label file into a byte stream
    with open(inLabel, 'r', errors = 'ignore') as label_file:
        label_bytes = label_file.read()
    
    # encode and compress label byte stream
    label_encode = label_bytes.encode()
    label_compress = brotli.compress(label_encode)
    
    # send compressed label byte stream to server and get response back
    response = requests.post(url, data = label_compress)
    
    # uncompress and decode isd response
    response_uncompress = brotli.decompress(response.content)
    decode_response = response_uncompress.decode()                           
    
    # create an output file for isd
    outputFile = f"{path}/returned_isds/test_isd.json"
    
    # load isd response as dictionary
    isd_dict = json.loads(decode_response)
    
    # serializes dictionary to json object and writes to file
    with open(outputFile, 'w') as isd_output:
        json.dump(isd_dict, isd_output, indent = 2)
    
if __name__ == "__main__":
    
    # test every file in data directory
    #for file in os.listdir(f'{path}/data/'):
    #     test_send(f'{path}/data/{file}')
    
    # test a single file input by user
    test_send(f"{path}/{inLabel}", url)

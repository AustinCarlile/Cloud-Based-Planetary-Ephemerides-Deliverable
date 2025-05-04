from fastapi.testclient import TestClient
from isdAPI import app
import brotli
import os
import pathlib
import json
import sys

# create test client
test_client = TestClient(app)

# get label file name
inLabel = sys.argv[1]

# find path to currect program and create a returned_isds folder if it doesnt exist yet
path = pathlib.Path(__file__).parent.resolve()
os.makedirs(f'{path}/returned_isds', exist_ok=True)

# sending a label file and getting an isd back
def test_send(inLabel):
    
    # read label file into a byte stream
    with open(inLabel, 'r', errors = 'ignore') as label_file:
        label_bytes = label_file.read()
    
    # encode and compress label byte stream
    label_encode = label_bytes.encode()
    label_compress = brotli.compress(label_encode)
    
    # send compressed label byte stream to server and get response back
    response = test_client.post("/getIsd", content = label_compress)
    
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
    
    assert response.status_code == 200
    
if __name__ == "__main__":
    
    # test every file in data directory
    #for file in os.listdir(f'{path}/data/'):
    #     test_send(f'{path}/data/{file}')
    
    # test a single file input by user
    test_send(f"{path}/{inLabel}")

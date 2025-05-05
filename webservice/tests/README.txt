The webservice/tests directory includes an tester client, test_client.py

This tester client is left as a code reference for creating or adapting any clients to interact with the Web Service.

The tester client can also be used to test and debug the Web Service. 
Give it a label file path and Web Service ip:port and it will return an ISD, test_isd.json, in a generated webservice/tests/returned_isds directory.

To use the tester client, you can run it from the linux terminal like so: "python test_client.py path/to/label_file.lbl web_service_ip:port"

For example: "python test_client.py data/f00a47_isis3.lbl http://127.0.0.1:8000"
# Cloud-Based Planetary Ephemerides Manual

[Environment Setup](#to-set-up-the-necessary-environment-for-operation-of-the-web-service)

[AWS Account Setup](#to-set-up-your-Amazon-AWS-account-for-deploying-the-dynamodb-instance)

[Web Service Setup](#to-set-up-the-web-service)

[Configuration and Daily Operation](##configuration-and-daily-operation)

[Maintenance](#maintenance)

[Troubleshooting](#troubleshooting)

## Installation

### To set up the necessary environment for operation of the Web Service:


1. [Install Miniforge](https://github.com/conda-forge/miniforge)


2. [Install ISIS](https://astrogeology.usgs.gov/docs/how-to-guides/environment-setup-and-maintenance/installing-isis-via-anaconda/) and set environment variables:

_NOTE: Make sure to install ISIS data for any missions you are using label files from._

For example, if you are going to use viking1 label files, run: 
```
downloadIsisData viking1 $ISISDATA
```
Or for all missions:
```
downloadIsisData all $ISISDATA
```


3. Navigate to a directory for the Web Service and clone github repo:
```
sudo apt install git && git clone https://github.com/AustinCarlile/Cloud-Based-Planetary-Ephemerides-Deliverable.git
```


4. Install Python-pip and necessary dependencies:
```
conda install fastapi && \
conda install boto3 && \
conda install brotli && \
conda install pvl && \
conda install uvicorn && \
pip install mkl && \
conda install requests
```


### To set up your Amazon AWS account for deploying the DynamoDB instance:

1. [Set up an AWS Account](https://docs.aws.amazon.com/accounts/latest/reference/manage-acct-creating.html)

2. [Set up an IAM User account](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html)

3. [Create IAM User Access Key](https://docs.aws.amazon.com/keyspaces/latest/devguide/create.keypair.html)

4. Give IAM User AmazonDynamoDBFullAccess permissions:

[Permissions instructions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_manage-attach-detach.html)

[AmazonDynamoDBFullAccess Docs](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AmazonDynamoDBFullAccess.html)


5. [Deploy DynamoDB CloudFormation stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-create-stack.html)

The [DynamoDB CloudFormation file](cloudformation/dynamo.yml) is found in the cloudformation directory of the GitHub repository.


### To set up the Web Service:

1. Set your IAM User access keys and region to environment variables in your .bashrc:
```
AWS_ACCESS_KEY_ID=”IAM USER ACCESS KEY”; export AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=”IAM USER SECRET ACCESS KEY”; export AWS_SECRET_ACCESS_KEY
AWS_REGION=”AWS REGION RESOURCE IS HOSTED IN”; export AWS_REGION
```


2. After setting environment variables in .bashrc, run: 
```
exec bash
```
then: 
```
mamba activate isis
```


3. Run uvicorn command to start Web Service:
```
uvicorn isdAPI:app --reload
```


The Web Service is now running and listening for HTTP requests on 127.0.0.1:8000.


## Configuration and Daily Operation

Make sure to download all isis data needed for mission label files. If you use “web=true” in the spiceinit section of the web service, it will segfault and core dump. The web service will still be operational but will save junk data to memory.


If you already have the AWS CLI set up, you can use the ~/.aws/credentials file instead of setting the access keys and region to environment variables:
```
[default]
aws_access_key_id=IAM USER ACCESS KEY
aws_secret_access_key=IAM USER SECRET ACCESS KEY
aws_region=AWS REGION RESOURCE IS HOSTED IN
```


If you want to to dynamically get AWS credentials, you can use AWS STS:

https://docs.aws.amazon.com/code-library/latest/ug/python_3_sts_code_examples.html

https://botocore.amazonaws.com/v1/documentation/api/latest/reference/services/sts.html


Configuration for end-user:

* Interact programmatically with the REST API to access endpoints


Workflow for end-user:

* Submit a request by sending the web service a .lbl file for the target image

* Receive a freshly generated ISD or an ISD from the cache


## Maintenance

The Web Service automatically generates a print.prt log file that chronicles all ISD generation actions that have taken place. Periodically, the user may want to erase or delete this file to prevent its size from growing too large.

The Web Service will also automatically create a “temp.json” file when generating an ISD, this is overwritten each time and will not grow in size. The user may want to automatically remove this file if they do not want to have it in memory at all times.


## Troubleshooting

The following are a list of possible issues you may encounter when deploying and running the Web Service and DynamoDB instance, as well as their potential solutions.


Improper File Format:
  
* Ensure the label file being submitted is formatted correctly
  
Improper installation of ISIS:

* A lack of drivers or sufficient ISIS data will result in failures during ISD generation
  
Incorrect Environment:
  
* Make sure directories and paths are correct when attempting to generate an ISD
  
Error deploying CloudFormation file:
  
* Check the error given during the CloudFormation deployment in the AWS console. Make sure that the user has permissions required.

Web Service Segmentation fault:
  
* Make sure that you have downloaded the mission data for any mission label file you send the Web Service.
  
* For example, if you are going to use viking1 label files, run: 
```
downloadIsisData viking1 $ISISDATA
```
* Or for all missions:
```
downloadIsisData all $ISISDATA
```
_NOTE: A segmentation fault will happen if you add “web=true” to the spiceinit command in isdAPI.py_

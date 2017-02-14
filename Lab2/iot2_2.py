import boto
import boto.dynamodb2
from boto.dynamodb2.fields import HashKey, RangeKey, KeysOnlyIndex, GlobalAllIndex
from boto.dynamodb2.table import Table
from boto.dynamodb2.types import NUMBER
import time

ACCOUNT_ID = '768104751743'
IDENTITY_POOL_ID = 'us-east-1:bc86890e-31dc-4faf-89fb-1723c76063f0'
ROLE_ARN = 'arn:aws:iam::768104751743:role/Cognito_edisonDemoKinesisUnauth_Role'
# Use cognito to get an identity.
cognito = boto.connect_cognito_identity()
cognito_id = cognito.get_id(ACCOUNT_ID, IDENTITY_POOL_ID)
oidc = cognito.get_open_id_token(cognito_id['IdentityId'])
 
# Further setup your STS using the code below
sts = boto.connect_sts()
assumedRoleObject = sts.assume_role_with_web_identity(ROLE_ARN, "XX", oidc['Token'])


DYNAMODB_TABLE_NAME = 'edisonDemoDynamo'

# DYNAMODB_TABLE_NAME2 = 'edisonDemoDynamo2'

# Prepare DynamoDB client
client_dynamo = boto.dynamodb2.connect_to_region(
        'us-east-1',
        aws_access_key_id=assumedRoleObject.credentials.access_key,
        aws_secret_access_key=assumedRoleObject.credentials.secret_key,
        security_token=assumedRoleObject.credentials.session_token)
 
users = Table(DYNAMODB_TABLE_NAME, connection=client_dynamo)

# new_users = Table.create(DYNAMODB_TABLE_NAME2, schema=[HashKey('iteration'), RangeKey('temp')], global_indexes=[GlobalAllIndex('EverythingIndex', parts=[HashKey('time')])], connection=client_dynamo)
time.sleep(2)

def aws_add(name, CUID, users):
    users.put_item(data={'name': name, 'CUID': CUID})
    time.sleep(2)

def aws_delete(name, CUID, users):
    users.delete_item(name=name, CUID=CUID)
    time.sleep(2)

def aws_view(users):
    allUsers = users.scan()
    print "Name:  CUID:"
    for record in allUsers:
        print record['name'] + " " + record['CUID']
    time.sleep(2)

def aws_search(name, users):
    result = users.query_2(name__eq=name)
    print "Name:  CUID:"
    for record in result:
        print record['name'] + " " + record['CUID']
    time.sleep(2)

print "Press Ctrl+C to escape..."
try:
    while (1):
        print("Input Format:")
        print("1. add name CUID")
        print("2. delete name CUID")
        print("3. view")
        print("4. search name")
        userIn = raw_input(">>> Input: ")
        splitIn = userIn.split()
        print splitIn
        
        if splitIn[0] == "add" and len(splitIn) == 3:
            aws_add(splitIn[1], splitIn[2], users)
        
        elif splitIn[0] == "delete" and len(splitIn) == 3:
            aws_delete(splitIn[1], splitIn[2], users)
        
        elif splitIn[0] == "view" and len(splitIn) == 1:
            aws_view(users)
        
        elif splitIn[0] == "search" and len(splitIn) == 2:
            aws_search(splitIn[1], users)
        
        else :
            print("wrong input format!")

except KeyboardInterrupt:
        exit


import boto
import boto.dynamodb2

ACCOUNT_ID = '768104751743'
IDENTITY_POOL_ID = 'us-east-1:bc86890e-31dc-4faf-89fb-1723c76063f0'
ROLE_ARN = 'arn:aws:iam::768104751743:role/Cognito_edisonDemoKinesisUnauth_Role'
DYNAMODB_TABLE_NAME = 'edisonDemoDynamo'
KINESIS_STREAM_NAME = 'edisonDemoKinesis'

# Use cognito to get an identity.
cognito = boto.connect_cognito_identity()
cognito_id = cognito.get_id(ACCOUNT_ID, IDENTITY_POOL_ID)
oidc = cognito.get_open_id_token(cognito_id['IdentityId'])
 
# Further setup your STS using the code below
sts = boto.connect_sts()
assumedRoleObject = sts.assume_role_with_web_identity(ROLE_ARN, "XX", oidc['Token'])

# Prepare DynamoDB client
client_dynamo = boto.dynamodb2.connect_to_region(
    'us-east-1',
    aws_access_key_id=assumedRoleObject.credentials.access_key,
    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
    security_token=assumedRoleObject.credentials.session_token)
 
from boto.dynamodb2.table import Table
table_dynamo = Table(DYNAMODB_TABLE_NAME, connection=client_dynamo)

'''
IMPORTANT NOTE: When following the tutorial, please be sure to include the 
"connection=client_dynamo" in your function call as above.
For example, when creating a Table, be sure to add the above.
users = Table.create('users', schema=[HashKey('username')], 
connection=client_dynamo)
IMPORTANT NOTE: After creating the table, be sure to put a small delay (~10-20sec) 
right after the Table.create(....) command, so as to allow Amazon to actual create & 
configure the table.
'''


# Prepare Kinesis client
client_kinesis = boto.connect_kinesis(
    aws_access_key_id=assumedRoleObject.credentials.access_key,
    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
    security_token=assumedRoleObject.credentials.session_token)




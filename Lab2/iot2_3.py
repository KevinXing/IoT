import boto
import boto.dynamodb2
from boto import kinesis
from boto.kinesis.exceptions import ResourceNotFoundException
from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey, KeysOnlyIndex, GlobalAllIndex
from boto.dynamodb2.types import NUMBER
import mraa
import time
import pyupm_i2clcd as lcd
#import threading

import pexpect
import sys
import time
 
switch_pin_number=8
# Configuring the switch and buzzer as GPIO interfaces
switch = mraa.Gpio(switch_pin_number)

# Initialize Jhd1313m1 at 0x3E (LCD_ADDRESS) and 0x62 (RGB_ADDRESS)
myLcd = lcd.Jhd1313m1(0, 0x3E, 0x62)
 
myLcd.setCursor(0,0)
# RGB Blue
myLcd.setColor(53, 39, 249)
 
# Configuring the switch and buzzer as input & output respectively
switch.dir(mraa.DIR_IN)

chooseDB = True
lcdPrint = 'DynamoDB Mode'

curTemp = 0
num = 0

# address of WICED
bluetoothAdr = '00:10:18:01:39:26'
# lock for curTemp
# tempLock = threading.Lock();
shard_id = 0
#----------------------------------------------------------------
# AWS config
ACCOUNT_ID = '768104751743'
IDENTITY_POOL_ID = 'us-east-1:bc86890e-31dc-4faf-89fb-1723c76063f0'
ROLE_ARN = 'arn:aws:iam::768104751743:role/Cognito_edisonDemoKinesisUnauth_Role'
DYNAMODB_TABLE_NAME = 'edisonDemoDynamo2'
KINESIS_STREAM_NAME = 'edisonDemoKinesis'



# Use cognito to get an identity.
cognito = boto.connect_cognito_identity()
cognito_id = cognito.get_id(ACCOUNT_ID, IDENTITY_POOL_ID)
oidc = cognito.get_open_id_token(cognito_id['IdentityId'])
 
# Further setup your STS using the code below
sts = boto.connect_sts()
assumedRoleObject = sts.assume_role_with_web_identity(ROLE_ARN, "XX", oidc['Token'])

# Prepare Kinesis client
kinesis = boto.connect_kinesis(
    aws_access_key_id=assumedRoleObject.credentials.access_key,
    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
    security_token=assumedRoleObject.credentials.session_token)

#----------------------------------------------------------------
#DB
client_dynamo = boto.dynamodb2.connect_to_region(
        'us-east-1',
        aws_access_key_id=assumedRoleObject.credentials.access_key,
        aws_secret_access_key=assumedRoleObject.credentials.secret_key,
        security_token=assumedRoleObject.credentials.session_token)
users = Table(DYNAMODB_TABLE_NAME, connection=client_dynamo)
#----------------------------------------------------------------



def initBluetooth():
    tool.expect('\[LE\]>')
    print "Preparing to connect. You might need to press the side button..."
    tool.sendline('connect')
    # test for success of connect
    tool.expect('Connection successful')
    tool.sendline('char-write-req 0x2b 0x01')
    tool.expect('\[LE\]>') 
    print "connect successful"

def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
        pass
    return t


def readTemp():
    global num
    global curTemp
    try:
        tool.expect('Notification handle = 0x002a value: 34.*')
        rval = tool.after.split()
        num1 = floatfromhex(rval[10])
        num2 = floatfromhex(rval[11])
        #tempLock.acquire()
        curTemp = (num1 + num2 * 256) / 10
        num = num + 1
        print "curTemp = " + str(curTemp)
        #tempLock.release()
        time.sleep(1)
    except KeyboardInterrupt:
        exit

def kinesisInit():
        # Create a new stream
        # kinesis.create_stream(KINESIS_STREAM_NAME, 1)

        # Wait for the stream to be ready
        print("kinesis init...")
        tries = 0
        while tries < 10:
            tries += 1
            time.sleep(1)
            response = kinesis.describe_stream(KINESIS_STREAM_NAME)

            if response['StreamDescription']['StreamStatus'] == 'ACTIVE':
                shard_id = response['StreamDescription']['Shards'][0]['ShardId']
                break
        else:
            raise TimeoutError('Stream is still not active, aborting...')

def createKinesisData():
    global num
    global curTemp
    res = ''
    #tempLock.acquire()
    #tempLock.release()
    localtime = time.asctime(time.localtime(time.time()))
    res += "measurement times: " + str(num) + " current temperature: " + str(curTemp) + " local time: " + localtime
    return res

def kinesisWait():
    # Wait for the data to show up
    tries = 0
    num_collected = 0
    num_expected_records = 1
    collected_records = []
    response = kinesis.get_shard_iterator(KINESIS_STREAM_NAME, str(shard_id), 'TRIM_HORIZON')
    shard_iterator = response['ShardIterator']
    while tries < 15:
        tries += 1
        time.sleep(1)

        response = kinesis.get_records(shard_iterator)
        shard_iterator = response['NextShardIterator']
        for record in response['Records']:
            if 'Data' in record:
                collected_records.append(record['Data'])
                num_collected += 1
            if num_collected >= num_expected_records:
                break
        else:
            raise TimeoutError('No records found, aborting...')


myLcd.setCursor(0, 0)
myLcd.write(lcdPrint)
tool = pexpect.spawn('gatttool -b ' + bluetoothAdr + ' -I')
initBluetooth()
kinesisInit()

# start temperature reading thread
#t = threading.Thread(target = readTemp)
#t.start()

print "Press Ctrl+C to escape..."
try:
        while (1):
            if (switch.read()):     # check if switch pressed
                chooseDB = not chooseDB
            readTemp()
            #curTemp =23
            #measureNum = 10 
            if (chooseDB):
                lcdPrint = 'DynamoDB Mode'
                myLcd.setCursor(0, 0)
                myLcd.write(lcdPrint)
                #db code
                print time.strftime("%Y-%m-%d %A %X %Z", time.localtime())
                users.put_item(data={'iteration': str(num), 'temp': str(curTemp), 'time': time.strftime("%Y-%m-%d %A %X %Z", time.localtime())})
            else:
                lcdPrint = 'kinesis Mode '
                myLcd.setCursor(0, 0)
                myLcd.write(lcdPrint)
                #kinesis code
                try:
                    res = createKinesisData()
                    response = kinesis.put_record(KINESIS_STREAM_NAME, res, res)
                    print("Put data:" + res)
                except Exception as e:
                    sys.stderr.write("encountered an exception while trying to put data" + str(e))
                #kinesisWait()
			
	    time.sleep(2) # puts system to sleep for 0.2sec before switching
    				

except KeyboardInterrupt:
        exit



import boto3
import json
from boto3.dynamodb.conditions import Key
T=boto3.resource('dynamodb',region_name='us-east-1').Table('autowar-reports')
for eid in ['eval-e2e-20260115-002','eval-e2e-20260115-003']:
    resp=T.query(KeyConditionExpression=Key('pk').eq(eid))
    print('---',eid,'---')
    print(json.dumps(resp.get('Items',[]),indent=2, default=str))

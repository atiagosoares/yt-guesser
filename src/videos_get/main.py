import json
import boto3
import os

VIDEOS_TABLE_NAME = os.environ['VIDEOS_TABLE_NAME']

def handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(VIDEOS_TABLE_NAME)

    response = table.scan()

    return {
        'statusCode': 200,
        'body': json.dumps(response['Items'])
    }
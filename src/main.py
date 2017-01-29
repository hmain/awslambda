from __future__ import print_function

import json
import urllib
import boto3
import datetime
import os

print('Loading function')

# S3
s3 = boto3.resource('s3')

# SNS
sns = boto3.client('sns')
# SNS Subject
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
sns_subject = os.environ['sns_subject'] + now
# SNS topic
sns_topic = os.environ['sns_topic']


def lambda_handler(event, context):
    # See the whole event message
    # print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and get its content
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'])
    instance_id = "Instance ID:" + " " + key.split("/")[2]
    object = s3.Object(bucket, key)
    try:
        object_contents = object.get()["Body"].read().decode('utf-8')
        # Print the content of the object
        # print("OBJECT CONTENTS: " + object_contents)

        # Send the content as an SNS message
        sns.publish(TopicArn=sns_topic, Message=instance_id + "\n\n\n\n" + object_contents, Subject=sns_subject)

    except Exception as e:
        print(e)
        print(
            'Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(
                key, bucket))
        raise e

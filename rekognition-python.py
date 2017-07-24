from __future__ import print_function

import boto3
import json
import urllib

print('Loading function')

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')
ses = boto3.client('ses')


# --------------- Helper Functions to call Rekognition APIs ------------------


def detect_faces(bucket, key):
    response = rekognition.detect_faces(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    return response


def detect_labels(bucket, key):
    response = rekognition.detect_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}})

    # Sample code to write response to DynamoDB table 'MyTable' with 'PK' as Primary Key.
    # Note: role used for executing this Lambda function should have write access to the table.
    #table = boto3.resource('dynamodb').Table('MyTable')
    #labels = [{'Confidence': Decimal(str(label_prediction['Confidence'])), 'Name': label_prediction['Name']} for label_prediction in response['Labels']]
    #table.put_item(Item={'PK': key, 'Labels': labels})
    return response


def index_faces(bucket, key):
    # Note: Collection has to be created upfront. Use CreateCollection API to create a collecion.
    #rekognition.create_collection(CollectionId='BLUEPRINT_COLLECTION')
    response = rekognition.index_faces(Image={"S3Object": {"Bucket": bucket, "Name": key}}, CollectionId="BLUEPRINT_COLLECTION")
    return response


# --------------- Main handler ------------------


def lambda_handler(event, context):
    '''Demonstrates S3 trigger that uses
    Rekognition APIs to detect faces, labels and index faces in S3 Object.
    '''
    print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    try:
        # Calls rekognition DetectLabels API to detect labels in S3 object
        response_rekognition = detect_labels(bucket, key)

        # Print response to console.
        print(response_rekognition)

        # Detect human
        human_labels = ["Human", "People", "Person", "Selfie", "Face", "Portrait", "Child", "Kid"]
        human_detected = False
        for label in response_rekognition["Labels"]:
            if label["Name"] in human_labels and label["Confidence"] > 99.:
                human_detected = True
                break


        # Move the image to the archive folder
        target_bucket = "rpizero-smart-camera-archive"
        target_key = "human/{}".format(key) if human_detected else "false_positive/{}".format(key)
        copy_source = {'Bucket':bucket, 'Key':key}
        response_s3 = s3.copy(Bucket=target_bucket, Key=target_key, CopySource=copy_source)
        print(response_s3)
        response_s3 = s3.delete_object(Bucket=bucket, Key=key)
        print(response_s3)

        target_url = s3.generate_presigned_url('get_object', Params = {'Bucket': target_bucket, 'Key': target_key}, ExpiresIn = 24*3600)
        print(target_url)


        # Send e-mail notification
        if human_detected:
            email_from = ""
            email_to = ""
            response_ses = ses.send_email(
               Source = email_from,
                Destination={
                    'ToAddresses': [
                        email_to,
                     ],
                },
                Message={
                    'Subject': {
                        'Data': "human_detected = {}".format(human_detected)
                    },
                    'Body': {
                        'Text': {
                            'Data': "{}\n{}".format(json.dumps(response_rekognition, indent=2), target_url)
                        }
                    }
                }
            )
            print(response_ses)

        return response_rekognition
    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(key, bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
        raise e

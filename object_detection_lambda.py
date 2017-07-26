from __future__ import print_function

import boto3
import json
import urllib
import os
import sys
import zipfile
import uuid

s3 = boto3.client('s3')
ses = boto3.client('ses')


# Donwload dependencies from S3
bucket = "rpizero-smart-camera-archive"
key = "vendored.zip"
download_path = '/tmp/{}'.format(key)
response_s3 = s3.download_file(bucket, key, download_path)
print(response_s3)
zip_ref = zipfile.ZipFile("/tmp/vendored.zip", 'r')
zip_ref.extractall("/tmp")
zip_ref.close()

# Location of the dependencies
sys.path.append("/tmp/vendored")

# Now that the script knows where to look, we can safely import our objects
import numpy as np
import tensorflow as tf
from PIL import Image
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util


# Path to frozen detection graph. This is the actual model that is used for the object detection.
MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017'
HERE = os.path.dirname(os.path.realpath(__file__))
PATH_TO_CKPT = os.path.join(HERE, MODEL_NAME, 'frozen_inference_graph.pb')

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join('/tmp/vendored', 'object_detection', 'data', 'mscoco_label_map.pbtxt')

NUM_CLASSES = 90

# Loading label map
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                            use_display_name=True)
category_index = label_map_util.create_category_index(categories)


def detect_objects(image_np, sess, detection_graph):
    # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
    image_np_expanded = np.expand_dims(image_np, axis=0)
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

    # Each box represents a part of the image where a particular object was detected.
    boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

    # Each score represent the level of confidence for each of the objects.
    # Score is shown on the result image, together with the class label.
    scores = detection_graph.get_tensor_by_name('detection_scores:0')
    classes = detection_graph.get_tensor_by_name('detection_classes:0')
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')

    # Actual detection.
    (boxes, scores, classes, num_detections) = sess.run(
        [boxes, scores, classes, num_detections],
        feed_dict={image_tensor: image_np_expanded})

    # Visualization of the results of a detection.
    vis_util.visualize_boxes_and_labels_on_image_array(
        image_np,
        np.squeeze(boxes),
        np.squeeze(classes).astype(np.int32),
        np.squeeze(scores),
        category_index,
        use_normalized_coordinates=True,
        line_thickness=8)
    return scores, classes, image_np


def lambda_handler(event, context):
    '''Demonstrates S3 trigger that uses
    Rekognition APIs to detect faces, labels and index faces in S3 Object.
    '''
    print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))

    # Load image
    download_path = '/tmp/{}{}'.format(uuid.uuid4(), key)
    response_s3 = s3.download_file(bucket, key, download_path)
    print(response_s3)
    image = Image.open(download_path)
    (im_width, im_height) = image.size
    image_np = np.array(image.getdata()).reshape(
        (im_height, im_width, 3)).astype(np.uint8)

    # Load a (frozen) Tensorflow model into memory.
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

        sess = tf.Session(graph=detection_graph)

    # Detect human
    human_detected = False
    scores, classes, image_with_labels = detect_objects(image_np, sess, detection_graph)
    print("\n".join("{0:<20s}: {1:.1f}%".format(category_index[c]['name'], s*100.) for (c, s) in zip(classes[0], scores[0])))
    for (c, s) in zip(classes[0], scores[0]):
        if category_index[c]['name'] == 'person' and s > 0.5:
            human_detected = True
            break

    sess.close()

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
                        'Data': "{}\n{}".format(
                            "\n".join("{0:<20s}: {1:.1f}%".format(category_index[c]['name'], s*100.) for (c, s) in zip(classes[0], scores[0])),
                            target_url)
                    }
                }
            }
        )
        print(response_ses)

    return human_detected

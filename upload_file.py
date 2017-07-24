#!/usr/bin/env python
import boto3
import os

# Create an S3 client
s3 = boto3.client('s3')

# Find the latest image
img_dir = '/home/pi/motion'
files = os.listdir(img_dir)
full_paths = [os.path.join(img_dir, basename) for basename in files]
filename_local = max(full_paths, key=os.path.getctime)

# Filename that will appear in S3
# Strip the first three characters that stand for the image number
# as we want the file name to start with a date.
# For example 04-20170724114420-00.jpg will become 20170724114420-00.jpg
# The last two digits stand for the frame number.
# http://htmlpreview.github.io/?https://github.com/Motion-Project/motion/blob/master/motion_guide.html#picture_filename
# http://htmlpreview.github.io/?https://github.com/Motion-Project/motion/blob/master/motion_guide.html#conversion_specifiers
filename_s3 = os.path.basename(filename_local)[3:]
bucket_name = 'rpizero-smart-camera-upload'

# Uploads the given file using a managed uploader, which will split up large
# files automatically and upload parts in parallel.
print("Uploading file {} to Amazon S3".format(filename_s3))
s3.upload_file(filename_local, bucket_name, filename_s3)

# Remove the image from the local file system
print("Removing file {}".format(filename_local))
os.remove(filename_local)

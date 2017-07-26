# Smart security camera with Raspberry Pi Zero and AWS

This repository shows how to turn Raspberry Pi Zero into a smart security camera with the help of Amazon Web Services. The solution is based on the following two key components:
* use of available **Motion** software to detect movement,
* use of **Amazon Lambda** functions with deep learning models to identify humans in images and thus reduce the rate of false positives. The models are provided either by **Amazon Rekognition** or **TensorFlow Object Detection API**.

The installation procedure is documented here https://github.com/salekd/rpizero_smart_camera/wiki

![](https://github.com/salekd/rpizero_smart_camera/blob/master/camera.JPG)

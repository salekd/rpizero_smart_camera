# Smart security camera with Raspberry Pi Zero and AWS

https://www.bouvet.no/bouvet-deler/utbrudd/building-a-motion-activated-security-camera-with-the-raspberry-pi-zero

### Motion

http://htmlpreview.github.io/?https://github.com/Motion-Project/motion/blob/master/motion_guide.html
https://github.com/Motion-Project/motion/releases

```
wget https://github.com/Motion-Project/motion/releases/download/release-4.0.1/pi_jessie_motion_4.0.1-1_armhf.deb
sudo apt-get install gdebi-core
sudo gdebi pi_jessie_motion_4.0.1-1_armhf.deb
```

```
mkdir .motion
cp /etc/motion/motion.conf .motion/
```

```
motion -c .motion/motion.conf
```

http://192.168.2.15:8081/

rc.local, cron job to delete pictures regularly


### AWS

https://www.bouvet.no/bouvet-deler/utbrudd/smarten-up-your-pi-zero-web-camera-with-image-analysis-and-amazon-web-services-part-2

There are many software development kits (SDK) available for AWS: https://aws.amazon.com/tools/
I choose to use Python SDK.

https://boto3.readthedocs.io/en/latest/guide/quickstart.html

```
sudo apt-get install python-pip
sudo pip install boto3
```

### AWS Credentials

From the Identity and Access Management (IAM) Console, generate an access key (Access Keys -> Create New Access Key)

https://console.aws.amazon.com/iam/home#/security_credential

Download the AWS Command Line Interface (CLI)
https://aws.amazon.com/cli/

```
sudo apt-get install libyaml-dev libpython2.7-dev
sudo pip install awscli
```

Configure the AWS access using the command line interace
https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration

Specify the access key and the secret access key. For region put eu-west-1 which corresponds to EU (Ireland)
http://docs.aws.amazon.com/general/latest/gr/rande.html

```
aws configure
```

### S3 buckets

Create S3 bucket called `rpizero-smart-camera-upload` from
https://s3.console.aws.amazon.com/s3/home

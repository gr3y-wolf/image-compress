import json
from webbrowser import get
from PIL import Image, ImageFile
import boto3
import os
from io import BytesIO
import urllib.parse
from helpers import get_file_extension, get_file_name

print("Loading function...")
BUCKET = os.environ.get("BUCKET", "api-test-xana")
IMAGE_LIST = [".jpg", ".jpeg", ".png", ".gif", ".webp"]

s3 = boto3.client("s3")


def process_image(event, context):
    try:
        print("Received event: " + json.dumps(event, indent=2))
        print(type(event))
        # if type(event) == "str":
        #     body = json.loads(event)
        # else:
        #     body = event

        # dump = body["Records"][0]["body"]

        # print(type(dump))
        # if type(dump) == "str":
        #     dump = json.loads(dump)

        # ip_file = dump["Message"]["s3Data"]
        # print(ip_file)

        # print("Getting file from bucket...")

        # key = ip_file["Key"]
        # print(ip_file["Key"])

        bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )

        file_name = get_file_name(key)
        ext = get_file_extension(key)

        print(f"file is : {file_name}", f"extension is =>> {ext}")
        response = s3.get_object(Bucket=bucket, Key=key)

        print(response)
        bytesStream = BytesIO(response["Body"].read())
        picture = Image.open(bytesStream)

        picture.load()

        print(" IMage format is:  ", picture.format)
        print("the mode of image is :", picture.mode)

        compressed = compressor(picture, ext)

        store_to_s3(compressed, BUCKET, key)

        return json.dumps(response, default=str)
    except Exception as e:
        print("an error occured")
        print(e)
        raise (e)


# process_image(open('event.json'),0)


def compressor(pi_img, ext, size=512):
    print("compressing image...")
    out_img = BytesIO()
    width, height = pi_img.size

    print(f"width  =>> {width}, height ==>>> {height}")

    pi_img.save(out_img, format=pi_img.format, quality=70, optimize=True)
    out_img.seek(0)

    if out_img.getbuffer().nbytes > 1:
        print(" now we can send object stream to s3")
        return out_img
    else:
        print("something happened, cant create obj stream")


def store_to_s3(stream, bucket, obj_key):
    print(" bucket is : ", bucket)
    print(" file name is : ", obj_key)

    final_path = obj_key.replace("input/images", "test/Defaults")

    print("storing files to :", final_path)
    try:
        new_img = s3.put_object(Bucket=bucket, Key=final_path, Body=stream)
        print(new_img)
        print("completed conversion")
    except Exception as e:
        print(e)
        raise (e)

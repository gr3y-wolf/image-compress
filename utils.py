from io import BytesIO
import boto3
import PIL
from PIL import Image


s3 = boto3.resource("s3")
s3client = boto3.client('s3')


def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper byte format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


def resized_image_url(resized_key, bucket):
    # return f"https://{bucket}.s3.amazonaws.com/{resized_key}"
    return f'https://cdn.xana.net/{resized_key}'


def get_file_from_s3(bucket_name, key):
    try:
        obj = s3.Object(bucket_name=bucket_name, key=key)
        obj_res = obj.get()
        obj_body = obj_res["Body"].read()
        obj_length = obj_res["ContentLength"]
        print('original file size is => ', get_size_format(obj_length))
        return obj_body, obj_length
    except Exception as e:
        print(e)
        raise (e)


def pillow_optimize(obj_stream, size_split):
    try:
        img = Image.open(BytesIO(obj_stream))
        img = img.resize((int(size_split[0]), int(size_split[1])), PIL.Image.ANTIALIAS)
        buffer = BytesIO()
        img.save(buffer, "JPEG", optimize=True, quality=70)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(e)
        raise (e)


def upload_file_to_s3(buffer, bucket_name, key):
    try:
        obj = s3.Object(bucket_name=bucket_name, key=key)
        obj.put(Body=buffer)
        # print("uploaded compressed file to s3")
        print("uploaded compressed file to location : ", key)
        return key
    except Exception as e:
        print(e)
        raise (e)

def push_to_s3(stream, bucket, final_path):
    print(" bucket is : ", bucket)
    print(" file name is : ", final_path)

    # final_path = obj_key.replace("input/images", DEST_DIR)

    print("storing files to :", final_path)
    try:
        s3client.put_object(
            Bucket=bucket,
            Key=final_path,
            Body=stream,
            ACL="public-read"
            # Metadata={"compressed": True},
        )
        print("uploaded compressed file to location : ", final_path)
        return final_path
    except Exception as e:
        print(e)
        raise (e)


def has_transparency(img):
    if img.info.get("transparency", None) is not None:
        return True
    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True

    return False
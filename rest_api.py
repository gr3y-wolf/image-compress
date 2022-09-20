import json
import sys
import traceback
import urllib.parse
from helpers import get_file_extension, get_file_name, get_s3_input_path, get_s3_output_path
from utils import get_file_from_s3, resized_image_url, upload_file_to_s3
from compress import compress_img

DEST_DIR = "Defaults"
# BUCKET = os.environ.get("BUCKET", "api-test-xana")
QUALITY = 55

def get_compressed(event, context):
    print("Function called...!!!")
    # print(json.dumps(event, indent=1))
    try:
        img =  urllib.parse.unquote_plus(event["pathParameters"]["img_path"])
        stage = event['pathParameters']['stage']
        if stage == 'dev':
            BUCKET = 'api-test-xana'
        elif stage == 'prod':
            BUCKET = 'xana-prod-item'     
        # print(img)
        key = get_s3_input_path(string=img, stage=stage)
        print("[*] key requested  ==>> ", key)
        file_name = get_file_name(key)
        ext = get_file_extension(key)
        print(f"[*] file is : {file_name}")
        print(f"[*] extension is =>> {ext}")
        
        obj_body, obj_length = get_file_from_s3(bucket_name=BUCKET, key=key)
       
        compressed, to_jpg = compress_img(blob=obj_body,filename=file_name, ext=ext, image_size=obj_length, quality=QUALITY, new_size_ratio=1)
        
        exts_to_jpg = ['.heic', '.heif']
        if ext in exts_to_jpg:
            key = file_name + '.jpg'
        if to_jpg == True:
            key = file_name + '.jpg'
        
        final_path = get_s3_output_path(string=key, dest=DEST_DIR)
        
        compressed_path = upload_file_to_s3(buffer=compressed, bucket_name=BUCKET, key=final_path)
        url = resized_image_url(resized_key=compressed_path,bucket=BUCKET)
        print('[*] compressed url ======>>>>>   ',url)
        
        response = { 'statusCode': 200, 'body': json.dumps({  'compressed_link': url  }) }
        return response

    except Exception as e:

    # Get current system exception
        ex_type, ex_value, ex_traceback = sys.exc_info()

    # Extract unformatter stack traces as tuples
        trace_back = traceback.extract_tb(ex_traceback)

    # Format stacktrace
        stack_trace = list()

        for trace in trace_back:
            stack_trace.append("File : %s , Line : %d, Func.Name : %s, Message : %s" % (trace[0], trace[1], trace[2], trace[3]))

        print("Exception type : %s " % ex_type.__name__)
        print("Exception message : %s" %ex_value)
        print("Stack trace : %s" %stack_trace)
        
        if str(ex_type.__name__) == 'NoSuchKey':
            return {
            'statusCode': 400, 'body' : json.dumps({ 'error': str(ex_type.__name__), 'msg' : str(ex_value) }) 
            }
        else:
            print(sys.exc_info())
            return {
                'statusCode': 500, 'body': json.dumps({
                    'error': str(ex_type.__name__), 'msg': str(ex_value)
                })
            }

#!/usr/bin/env python
import json
import os
import boto3
import tempfile
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# VIDEO_LIST = [".mp4", ".flv", ".m3u8", ".ts", ".MP2T", ".3gp", ".mov", ".avi", ".wmv"]
VIDEO_LIST = [".flv", ".m3u8", ".3gp", ".mov", ".wmv"]
thumbnail_width = int(os.environ["THUMBNAIL_SIZE"])
large_with = int(os.environ["LARGE_SIZE"])
mediaConvertRole = os.environ["MEDIA_CONVERT_ROLE"]
mediaJobSettingFolder = os.environ["MEDIA_JOB_SETTING"]
jobSettingTemplateFile = os.environ["MEDIA_TEMPLATE_NAME"] + '.json'
# jobSettingTemplateFile = "single-output.json"
region = os.environ["REGION"]
sourceS3Bucket = os.environ["BUCKET_NAME"]
stage = os.environ['ENV']
if stage == 'prod':
    bucket_prefix = 'xanaprod/'
else:
    bucket_prefix = 'apitestxana/'

s3client = boto3.client("s3")
# get the account-specific mediaconvert endpoint for this region
mediaconvert_client = boto3.client("mediaconvert", region_name=region)
endpoints = mediaconvert_client.describe_endpoints()
# add the account-specific endpoint to the client session
client = boto3.client(
    "mediaconvert",
    region_name=region,
    endpoint_url=endpoints["Endpoints"][0]["Url"],
    verify=False,
)


def get_file_extension(s3_input_path):
    index = s3_input_path.rfind(".")
    # return ext i.e: .mp4
    return s3_input_path[index:]


def get_file_name(s3_input_path):
    index = s3_input_path.rfind(".")
    # retunr file name with out ext
    return s3_input_path[:index]


def get_user_id(s3_input_path):
    arr = s3_input_path.split("/")
    if len(arr) < 2:
        print("Cannot found user id in s3 path")
        return 0
    return arr[2]


def check_seconde_path_map(s3_input_path, compare_key):
    arr = s3_input_path.split("/")
    if arr[1] == compare_key:
        return True
    return False


def get_s3_tag_by_key(arr_dict, key):
    for item in arr_dict:
        if item["Key"] == key:
            return item["Value"]
    return None


def generate_s3_key(s3_input_key, suffixId, ext):
    arr = s3_input_key.split("/")
    # arr.pop(0)  # remove first item 'input' and add first item 'Default' for output
    if 'input' in arr : arr.remove('input')
    if 'videos' in arr : arr.remove('videos')
    prefix = "Defaults"
    # prefix = "test"
    if ext == ".json":
        # remove 'input' then remove 'nft-media'
        arr.pop(0)
    else:
        arr.insert(1, prefix)

    # remove file name from path
    fileName = arr.pop()

    # get file name with out ext
    fileNameWithoutExt = get_file_name(fileName)
    # add json file name to path
    fullName = fileNameWithoutExt + ext
    suff = str(suffixId)
    if suff != "" and suff != "0":
        fullName = fileNameWithoutExt + "_" + suff + ext
    arr.append(fullName)
    return "/".join(arr)


def convert(event, context):

    print("event", event)
    for s3_record in event["Records"]:
        print("s3_record:" + str(s3_record))
        # input path has format ''
        s3_input_key = s3_record["s3"]["object"]["key"]
        print("s3_input_path:" + s3_input_key)
        sourceS3Bucket = s3_record["s3"]["bucket"]["name"]

        # mediaIndex=s3_input_key.find('nft-media',0)
        filePath, fileName = os.path.split(s3_input_key)
        fileNameWithoutExt = os.path.splitext(fileName)[0]
        fileExt = get_file_extension(s3_input_key)

        # if mediaIndex<0:
        #     print('not process for video update != nft-media ')
        #     return
        if fileExt.lower() not in VIDEO_LIST:
            print("not processing for object type:" + fileExt)
            return
        s3_output_job_setting = generate_s3_key(s3_input_key, 0, ".json")
        logger.info(s3_output_job_setting)

        # beacause media convert will auto add .mp4 so that don't need append here
        # s3_output_key = generate_s3_key(s3_input_key,'')
        # logger.info(s3_output_key)

        sourceS3 = "s3://" + sourceS3Bucket + "/" + s3_input_key
        # s3://sota-nft-image/output/nft/1/xxx.mp4
        # destinationS3 = 's3://' + sourceS3Bucket + '/' + s3_output_key


        # Use MediaConvert SDK UserMetadata to tag jobs with the assetID
        # Events from MediaConvert will have the assetID in UserMedata
        jobMetadata = {}

        jobMetadata["inputPath"] = s3_input_key
        jobMetadata["isImport"] = "0"

        print(jobMetadata, "jobMetadata")

        try:
            # download template job setting from s3
            tmp_file = tempfile.NamedTemporaryFile(suffix=".json")
            print("create tmp file for download template job setting:" + tmp_file.name)

            # download job setting from s3
            s3_job_template_key = bucket_prefix + mediaJobSettingFolder + "/" + jobSettingTemplateFile
            print('setting path to download  ======>>>> ', s3_job_template_key )
            with open(tmp_file.name, "wb") as tmpFile:
                print("download file from s3...")
                print("sourceS3Bucket s3:::", sourceS3Bucket)
                print("s3_job_template_key :::", s3_job_template_key)
                print("tmpFile :::", tmpFile)

                s3client.download_fileobj(sourceS3Bucket, s3_job_template_key, tmpFile)
                print("download template job setting done.")

            # build job setting from template setting
            jobSetting = {}
            with open(tmp_file.name) as json_file:
                print('===>>>>   Reading settings file.....')
                jobSetting = json.load(json_file)

                # update file input
                jobSetting["Inputs"][0]["FileInput"] = sourceS3
                # update file output to destination
                index = len(jobSetting["OutputGroups"])
                print("Length of output:", index)
                for outputGroup in jobSetting["OutputGroups"]:

                    logger.info(
                        "outputGroup['OutputGroupSettings']['Type'] == %s",
                        outputGroup["OutputGroupSettings"]["Type"],
                    )

                    suffixType = outputGroup["CustomName"]
                    s3_full_path = generate_s3_key(s3_input_key, suffixType, "")
                    
                    print(s3_full_path)

                    destinationS3 = "s3://" + sourceS3Bucket + "/" + s3_full_path
                    print('file output destination ====>>>>',destinationS3)

                    if (
                        outputGroup["OutputGroupSettings"]["Type"]
                        == "FILE_GROUP_SETTINGS"
                    ):
                        # because media convert will auto append .mp4 so that we don't put file type to function
                        # s3_full_path = generate_s3_key(s3_input_key, index, "")
                        
                        s3_full_path = (
                            generate_s3_key(s3_input_key, index, "")
                            if index > 1
                            else generate_s3_key(s3_input_key, "", "")
                        )
                        
                        outputGroup["OutputGroupSettings"]["FileGroupSettings"][
                            "Destination"
                        ] = ("s3://" + sourceS3Bucket + "/" + s3_full_path)
                        if suffixType == "Large MP4":
                            outputGroup["Outputs"][0]["VideoDescription"][
                                "Width"
                            ] = large_with
                        if suffixType == "Thumbnail":
                            outputGroup["Outputs"][0]["VideoDescription"][
                                "Width"
                            ] = thumbnail_width
                    elif (
                        outputGroup["OutputGroupSettings"]["Type"]
                        == "HLS_GROUP_SETTINGS"
                    ):
                        outputGroup["OutputGroupSettings"]["HlsGroupSettings"][
                            "Destination"
                        ] = destinationS3

                    elif (
                        outputGroup["OutputGroupSettings"]["Type"]
                        == "DASH_ISO_GROUP_SETTINGS"
                    ):
                        outputGroup["OutputGroupSettings"]["DashIsoGroupSettings"][
                            "Destination"
                        ] = destinationS3

                    elif (
                        outputGroup["OutputGroupSettings"]["Type"]
                        == "DASH_ISO_GROUP_SETTINGS"
                    ):

                        outputGroup["OutputGroupSettings"]["DashIsoGroupSettings"][
                            "Destination"
                        ] = destinationS3

                    elif (
                        outputGroup["OutputGroupSettings"]["Type"]
                        == "MS_SMOOTH_GROUP_SETTINGS"
                    ):

                        outputGroup["OutputGroupSettings"]["MsSmoothGroupSettings"][
                            "Destination"
                        ] = destinationS3

                    elif (
                        outputGroup["OutputGroupSettings"]["Type"]
                        == "CMAF_GROUP_SETTINGS"
                    ):

                        outputGroup["OutputGroupSettings"]["CmafGroupSettings"][
                            "Destination"
                        ] = destinationS3
                    else:
                        logger.error(
                            "Exception: Unknown Output Group Type %s",
                            outputGroup["OutputGroupSettings"]["Type"],
                        )

                    index = index - 1
                logger.info('************************------------dumping job settings-8---------**********************')
                logger.info(json.dumps(jobSetting))
                # create job
                # Convert the video using AWS Elemental MediaConvert
                print('Creating job for media convert...')
                job = client.create_job(
                    Role=mediaConvertRole, UserMetadata=jobMetadata, Settings=jobSetting
                )
                # store job setting to s3

                # s3_job_setting_path = (
                #     mediaJobSettingFolder + "/" + s3_output_job_setting
                # )
                print('created job process.....')
                # print(s3_job_setting_path)
                ## Upload tmpfile setting to s3
                # with open(tmp_job_setting.name, "w", encoding="utf-8") as f:
                #     json.dump(jobSetting, f, ensure_ascii=False, indent=200)
                #     s3client.upload_file(
                #         tmp_job_setting.name, sourceS3Bucket, s3_job_setting_path
                #     )

            print("done process for media convert")

        except Exception as e:
            logger.error("Exception: %s", e)
            statusCode = 500
            raise

    print("lambda finish job")

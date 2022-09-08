def get_file_extension(s3_input_path):
    index = s3_input_path.rfind(".")
    return s3_input_path[index :]


def get_file_name(s3_input_path):
    index = s3_input_path.rfind(".")
    return s3_input_path[:index]
    # return s3_input_path.split(".",1)[1]


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


# print(get_size_format(3682977))


def is_valid_path(key):
    bucket_names = ["apitestxana/", "xanaprod/"]

    res = key.startsWith(tuple(bucket_names))
    print(res)
    return res


def get_s3_input_path(string, stage):
    print(string)
    if stage == 'dev':
        prefix = "apitestxana/input/images/"
    elif stage == 'prod':
        prefix = 'xanaprod/input/images/'    
    key = prefix + string
    return key


def get_s3_output_path(string,stage):
    print(string)
    # if stage == 'dev':
    #     prefix = "apitestxana/"
    # elif stage == 'prod':
    #     prefix = 'xanaprod/'    
    key = string.replace('input/images', 'Defaults')
    return key
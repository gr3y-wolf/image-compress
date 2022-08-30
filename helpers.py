def get_file_extension(s3_input_path):
    index = s3_input_path.rfind(".")
    return s3_input_path[index:]


def get_file_name(s3_input_path):
    index = s3_input_path.rfind(".")
    return s3_input_path[:index]


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

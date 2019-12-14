import json

## Settings panel posisions
class HORIZONTAL:
    TEXT = 20
    TEXT_CTRL = 130


class VERTICAL:
    FIRST_LINE = 0
    SECOND_LINE = 30
    THIRD_LINE = 60
    FORTH_LINE = 90

PORT_VALID_CHARS = '0123456789'

def check_valid_data(data, valid_chars):
    """
    :param data: (string) the data to check
    :param valid_chars: (string/list) of valid chars
    """
    if all(x in valid_chars for x in data.strip()):
        return data
    return None

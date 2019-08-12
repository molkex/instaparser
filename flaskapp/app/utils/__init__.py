import codecs


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


class Constants:
    api_throttle_delay = 30
    api_error_delay = 5
    invalid_user = "invalid_user"
    bad_password = "bad_password"
    error_wrong_username = "WrongUsername"
    error_wrong_password = "WrongPassword"
    error_checkpoint_required = "CheckpointRequired"
    error_flagged_for_spam = "FlaggedForSpam"

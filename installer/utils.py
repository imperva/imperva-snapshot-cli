import re
import boto3
import botocore


def is_mail_valid(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # pass the regular expression
    # and the string into the fullmatch() method
    if re.fullmatch(regex, email):
        return True
    else:
        return False


def is_profile_valid(profile):
    try:
        boto3.session.Session(profile_name=profile)
        return True
    except botocore.exceptions.ProfileNotFound:
        return False

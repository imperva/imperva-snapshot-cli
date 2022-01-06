#!/usr/bin/python

import os
from rds_bo import RDSBO, DatabaseError, SnapshotError
from cf_bo import CFBO
import utils as ut
import requests
import sys
import getopt

EULA_PROMPT_MSG = "Type OK (case sensitive) to accept the EULA: "

EULA_INFO_MSG = "Please read the EULA: https://www.imperva.com/legal/license-agreement/"

EULA_ERROR_MSG = "Accepting the EULA is required to proceed with Imperva Snapshot scanning"

INLINE_ERROR_MSG = "You didn't ask for interactive mode (-i) nor specified the params!"

DATABASE_PROMPT_MSG = "Enter your database name [leave empty to get a list of available databases]: "

REGION_PROMPT_MSG = "Enter your region [click enter to to get the list of supported Regions]: "

EMAIL_PROMPT_MSG = "Enter your Email [the report will be sent to the specified mailbox]: "

EMAIL_PROMPT_VALID_MSG = "Repeat your Email: "

EMAILS_NOTEQUAL_MSG = "***** Emails are not equal, please try again"

EMAIL_ERROR_MSG = "***** Email is not valid, please try again"

REG_URL = "https://mbb6dhvsy0.execute-api.us-east-1.amazonaws.com/stage/register"

TEMPLATE_URL = "https://labyrinth-cloudformation-staging.s3.amazonaws.com/impervasnapshot-root-cf.yml"

ACCEPT_EULA_VALUE = "OK"

DEFAULT_TIMEOUT = 80

TIMEOUT_PROMPT_MSG = "CloudFormation Stack Timeout (default is " + str(
    DEFAULT_TIMEOUT) + " minutes, leave empty to use default): "

TIMEOUT_ERROR_MSG = "Timeout must be a natural number"

SUPPORTED_REGIONS = ["eu-north-1", "eu-west-3", "eu-west-2", "eu-west-1", "us-west-2", "ap-southeast-2",
                     "ap-northeast-2", "sa-east-1", "ap-northeast-1", "ap-south-1", "us-east-1", "us-east-2",
                     "ap-southeast-1", "us-west-1", "eu-central-1", "ca-central-1"]

options = {"profile": "", "role_assume": "", "region": "", "database_name": "", "email": "", "timeout": "",
           "accept_eula": ""}
options_not_required = ["role_assume", "timeout"]


class TokenError(Exception):
    pass


def get_token(email):
    return "4612e8da-051d-40f7-89ce-d5a47c6ded48"
    headers = {'Accept-Encoding': '*', 'content-type': 'application/x-www-form-urlencoded'}
    data = '{"eULAConsent": "True", "email": "' + email + '", "get_token": "true"}'

    response = requests.post(REG_URL, data=data,
                             headers=headers)
    if response.status_code != 200:
        raise TokenError(str(response.status_code) + ":" + response.text)
    print("Authentication Token: " + response.text)
    return response.text


def print_supported_regions():
    print("List of supported regions:")
    for r in SUPPORTED_REGIONS:
        print("* " + r)


def validate_region(region):
    if region not in SUPPORTED_REGIONS:
        print("## Region " + region + " not supported ##")
        return False
    return True


def print_list_dbs():
    RDSBO_inst = RDSBO(options["region"], os.environ["AWS_PROFILE"])
    RDSBO_inst.print_list_dbs()


def validate_database_name(database_name):
    if not database_name:  # need to check manually because if we send an empty string it will return the first database
        return False
    try:
        RDSBO(options["region"], os.environ["AWS_PROFILE"]).extract_database_name(database_name)
        return True
    except DatabaseError as e:
        print(e)
        return False


def validate_email(email):
    if ut.is_mail_valid(email):
        return True
    print(EMAIL_ERROR_MSG)
    return False


def validate_timeout(timeout):
    if isinstance(timeout, int) or timeout.isnumeric():
        return True
    print(TIMEOUT_ERROR_MSG)
    return False


def fill_options_inline(opts):
    if not opts:
        print(INLINE_ERROR_MSG)
        exit(1)
    options["timeout"] = DEFAULT_TIMEOUT  # set the default value just in case option '-t' is not specified
    for opt in opts:
        if opt in ('-p', "--profile"):
            options["profile"] = opts[opt]
            os.environ["AWS_PROFILE"] = options["profile"]
        if opt in ('-a', "--role"):
            options["role_assume"] = opts[opt]
        if opt in ('-d', "--database"):  # database_name relies on region, so we check it before we get it
            if '-r' in list(opts.keys()):
                r_opt = '-r'
            elif "--region" in list(opts.keys()):
                r_opt = "--region"
            else:
                break
            if not validate_region(opts[r_opt]):
                print_supported_regions()
                break
            options["region"] = opts[r_opt]
            if not validate_database_name(opts[opt]):
                print_list_dbs()
                break
            options["database_name"] = opts[opt]
        if opt in ('-m', "--email"):
            if not validate_email(opts[opt]):
                break
            options["email"] = opts[opt]
        if opt in ('-t', "--timeout"):
            if validate_timeout(opts[opt]):
                options["timeout"] = int(opts[opt])
        if opt == "--accepteula":
            options["accept_eula"] = ACCEPT_EULA_VALUE
    for option in options.keys():
        if not options[option] and option not in options_not_required:
            print("Option " + option + " is invalid or missing")
            exit(1)


def fill_options_interactive():
    options["profile"] = input("Enter your profile: ")
    os.environ["AWS_PROFILE"] = options["profile"]
    options["role_assume"] = input("Enter role to assume(optional): ")
    while not options["region"]:
        region = input(REGION_PROMPT_MSG)
        options["region"] = region if validate_region(region) else print_supported_regions()
    while not options["database_name"]:
        database_name = input(DATABASE_PROMPT_MSG)
        options["database_name"] = database_name if validate_database_name(database_name) else print_list_dbs()
    while not options["timeout"]:
        timeout = input(TIMEOUT_PROMPT_MSG) or DEFAULT_TIMEOUT
        options["timeout"] = int(timeout) if validate_timeout(timeout) else False
    while not options["email"]:
        email = input(EMAIL_PROMPT_MSG)
        is_email_valid = validate_email(email)
        if is_email_valid:
            email2 = input(EMAIL_PROMPT_VALID_MSG)
            if email2 == email:
                options["email"] = email
            else:
                print(EMAILS_NOTEQUAL_MSG)
                options["email"] = False
    print(EULA_INFO_MSG)
    options["accept_eula"] = input(EULA_PROMPT_MSG)
    if options["accept_eula"] != ACCEPT_EULA_VALUE:
        print(EULA_ERROR_MSG)
        exit(1)


def create_stack():
    stack_info = CFBO(options["region"], os.environ["AWS_PROFILE"]).create_stack("ImpervaSnapshot", TEMPLATE_URL,
                                                                                 options["database_name"],
                                                                                 get_token(options["email"]),
                                                                                 options["role_assume"],
                                                                                 options["timeout"])
    if not stack_info:
        exit(1)
    stack_id = stack_info["StackId"]
    print("------------------------------")
    print("Imperva Snapshot Stack created successfully (stack id: " + stack_id + ")")
    print("The report will be sent to this mailbox: " + options["email"])
    print("NOTE: Imperva Snapshot Stack will be deleted automatically on scan completion")
    stack_url = "https://console.aws.amazon.com/cloudformation/home?region=" + \
                options["region"] + \
                "#/stacks/stackinfo?filteringStatus=active&filteringText=&viewNested=true&hideStacks=false&stackId=" + \
                stack_id
    print("Click here to see the progress: " + stack_url)


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ip:a:r:d:m:t:",
                                   ["interactive", "profile=", "role=", "region=", "database=", "email=", "timeout=",
                                    "accept_eula"])
        opts = dict(opts)
        keys_list = list(opts.keys())
        if "-i" not in keys_list and "--interactive" not in keys_list:
            fill_options_inline(opts)
        else:
            fill_options_interactive()
        create_stack()
    except getopt.GetoptError as e:
        print(e)
        exit(2)

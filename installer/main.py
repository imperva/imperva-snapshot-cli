#!/usr/bin/python

import os
from rds_bo import RDSBO, InstanceError, SnapshotError
from cf_bo import CFBO
import utils as ut
import requests
import sys
import getopt

EULA_PROMPT_MSG = "Type OK (case sensitive) to accept the EULA: "

EULA_INFO_MSG = "Please read the EULA: https://www.imperva.com/legal/license-agreement/"

EULA_ERROR_MSG = "Accepting the EULA is required to proceed with Imperva Snapshot scanning"

INLINE_ERROR_MSG = "You didn't ask for interactive mode (-i) nor specified the params!"

INSTANCE_PROMPT_MSG = "Enter your instance name [leave empty to get a list of available RDS Instances]: "

REGION_PROMPT_MSG = "Enter your region [click enter to to get the list of supported Regions]: "

EMAIL_PROMPT_MSG = "Enter your Email [the report will be sent to the specified mailbox]: "

EMAIL_ERROR_MSG = "***** Email is not valid, please try again"

REG_URL = "https://mbb6dhvsy0.execute-api.us-east-1.amazonaws.com/stage/register"

TEMPLATE_URL = "https://labyrinth-cloudformation-staging.s3.amazonaws.com/impervasnapshot-root-cf.yml"

ACCEPT_EULA_VALUE = "OK"

DEFAULT_TIMEOUT = 80

TIMEOUT_PROMP_MSG = "CloudFormation Stack Timeout (default is " + str(
    DEFAULT_TIMEOUT) + " minutes, leave empty to use default): "

TIMEOUT_ERROR_MSG = "Timeout must be a natural number"

SUPPORTED_REGIONS = ["eu-north-1", "eu-west-3", "eu-west-2", "eu-west-1", "us-west-2", "ap-southeast-2",
                     "ap-northeast-2", "sa-east-1", "ap-northeast-1", "ap-south-1", "us-east-1", "us-east-2",
                     "ap-southeast-1", "us-west-1", "eu-central-1", "ca-central-1"]

options = {"profile": "", "role_assume": "", "region": "", "instance_name": "", "email": "", "timeout": "",
           "accept_eula": ""}
options_not_required = ["role_assume", "timeout"]


class TokenError(Exception):
    pass


def get_token(email):
    headers = {'Accept-Encoding': '*', 'content-type': 'application/x-www-form-urlencoded'}
    data = '{"eULAConsent": "True", "email": "' + email + '", "get_token": "true"}'

    response = requests.post(REG_URL, data=data,
                             headers=headers)
    if response.status_code != 200:
        raise TokenError(str(response.status_code) + ":" + response.text)
    print("Authentication Token: " + response.text)
    return response.text


def validate_region(region):
    if region not in SUPPORTED_REGIONS:
        print("## Region " + region + " not supported ##")
        print("List of supported regions:")
        for r in SUPPORTED_REGIONS:
            print("* " + r)
        return False
    return True


def validate_instance_name(instance_name):
    RDSBO_inst = RDSBO(options["region"], os.environ["AWS_PROFILE"])
    if not instance_name:  # need to check manually because if we send an empty string it will return the first instance
        RDSBO_inst.print_list_rds()
        return False
    try:
        RDSBO_inst.extract_rds_instance_name(instance_name)
        return True
    except InstanceError as e:
        print(e)
        RDSBO_inst.print_list_rds()
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
    for opt, arg in opts:
        if opt in ('-p', "--profile"):
            options["profile"] = arg
            os.environ["AWS_PROFILE"] = options["profile"]
        if opt in ('-a', "--role"):
            options["role_assume"] = arg
        if opt in ('-r', "--region"):
            if not validate_region(arg):
                break
            options["region"] = arg
        if opt in ('-n', "--instance") and options["region"]:  # instance_name relies on region, so we check it exists
            if not validate_instance_name(arg):
                break
            options["instance_name"] = arg
        if opt in ('-m', "--email"):
            if not validate_email(arg):
                break
            options["email"] = arg
        if opt in ('-t', "--timeout"):
            if validate_timeout(arg):
                options["timeout"] = int(arg)
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
        options["region"] = region if validate_region(region) else False
    while not options["instance_name"]:
        instance_name = input(INSTANCE_PROMPT_MSG)
        options["instance_name"] = instance_name if validate_instance_name(instance_name) else False
    while not options["timeout"]:
        timeout = input(TIMEOUT_PROMP_MSG) or DEFAULT_TIMEOUT
        options["timeout"] = int(timeout) if validate_timeout(timeout) else False
    while not options["email"]:
        email = input(EMAIL_PROMPT_MSG)
        options["email"] = email if validate_email(email) else False
    print(EULA_INFO_MSG)
    options["accept_eula"] = input(EULA_PROMPT_MSG)
    if options["accept_eula"] != ACCEPT_EULA_VALUE:
        print(EULA_ERROR_MSG)
        exit(1)


def create_stack():
    stack_info = CFBO(options["region"], os.environ["AWS_PROFILE"]).create_stack("ImpervaSnapshot", TEMPLATE_URL,
                                                                                 options["instance_name"],
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
        opts, args = getopt.getopt(sys.argv[1:], "ip:a:r:n:m:t:",
                                   ["interactive", "profile=", "role=", "region=", "instance=", "email=", "timeout=",
                                    "accepteula"])
        if not [item for item in opts if item[0] in ['-i', "--interactive"]]:
            fill_options_inline(opts)
        else:
            fill_options_interactive()
        create_stack()
    except getopt.GetoptError as e:
        print(e)
        exit(2)

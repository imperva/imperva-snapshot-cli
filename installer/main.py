#!/usr/bin/python

import os
from rds_bo import RDSBO, InstanceError, SnapshotError
from cf_bo import CFBO
import utils as ut
import requests
import sys
import getopt

EULA_INFO_MSG = "Please read the EULA: https://www.imperva.com/legal/license-agreement/"

EULA_ERROR_MSG = "Accepting the EULA is required to proceed with ImpervaSnapshot scanning"

INLINE_ERROR_MSG = "You didn't ask for interactive mode (-i) nor specified the params!"

INSTANCE_PROMPT_MSG = "Enter your instance name [leave empty to get a list of available RDS Instances]: "

REGION_PROMPT_MSG = "Enter your region [click enter to to get the list of supported Regions]: "

EMAIL_PROMPT_MSG = "Enter your Email [the report will be sent to the specified mailbox]: "

EMAIL_ERROR_MSG = "***** Email is not valid, please try again"

REG_URL = "https://mbb6dhvsy0.execute-api.us-east-1.amazonaws.com/stage/register"

TEMPLATE_URL = "https://labyrinth-cloudformation-staging.s3.amazonaws.com/impervasnapshot-root-cf.yml"

ACCEPT_EULA_VALUE = "OK"

SUPPORTED_REGIONS = ["eu-north-1", "eu-west-3", "eu-west-2", "eu-west-1", "us-west-2", "ap-southeast-2",
                     "ap-northeast-2", "sa-east-1", "ap-northeast-1", "ap-south-1", "us-east-1", "us-east-2",
                     "ap-southeast-1", "us-west-1", "eu-central-1", "ca-central-1"]

options = {"profile": "", "role_assume": "", "region": "", "instance_name": "", "email": "", "accept": ""}
options_not_required = ["role_assume"]


def get_token(email):
    headers = {'Accept-Encoding': '*', 'content-type': 'application/x-www-form-urlencoded'}
    data = '{"eULAConsent": "True", "email": "' + email + '", "get_token": "true"}'

    response = requests.post(REG_URL, data=data,
                             headers=headers)
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
    try:
        RDSBO_inst = RDSBO(options["region"], os.environ["AWS_PROFILE"])
        instance_name = RDSBO_inst.extract_rds_instance_name(instance_name)
        # print("✅ Selected RDS: " + instance_name)
        return True
    except InstanceError as e:
        print(e)
        return False


# def get_snapshot(instance_name):
#     try:
#         RDSBO_inst = RDSBO(options["region"], os.environ["AWS_PROFILE"])
#         snap_name = RDSBO_inst.get_snap_name(instance_name)
#         print("✅ Snapshot found: " + snap_name)
#         return instance_name
#     except InstanceError as e:
#         print(e)
#         return False


def print_list_rds():
    RDSBO_inst = RDSBO(options["region"], os.environ["AWS_PROFILE"])
    RDSBO_inst.print_list_rds()


def validate_email(email):
    if ut.is_mail_valid(email):
        return True
    print(EMAIL_ERROR_MSG)
    return False


def fill_options_inline(opts):
    if not opts:
        print(INLINE_ERROR_MSG)
        exit(1)
    for opt, arg in opts:
        if opt in ('-p', "--profile"):
            options["profile"] = arg
            os.environ["AWS_PROFILE"] = options["profile"]
        if opt in ('-a', "--role"):
            options["role_assume"] = arg
        if opt in ('-r', "--region"):
            options["region"] = arg if validate_region(arg) else False
            if not options["region"]:
                break
        if opt in ('-n', "--instance") and options["region"]:  # instance_name relies on region, so we check it exists
            if not arg:
                print_list_rds()
                break
            is_instance_valid = validate_instance_name(arg)
            if not is_instance_valid:
                print_list_rds()
                break
            options["instance_name"] = arg
            if not options["instance_name"]:
                break
        if opt in ('-m', "--email"):
            options["email"] = arg if validate_email(arg) else False
            if not options["email"]:
                break
        if opt == "--accept":
            options["accept"] = ACCEPT_EULA_VALUE
    for option in options.keys():
        if not options[option] and option not in options_not_required:
            print("Option " + option + " is invalid or missing")
            exit(1)


def fill_options_interactive():
    options["profile"] = input("Enter your profile: ")
    os.environ["AWS_PROFILE"] = options["profile"]
    options["role_assume"] = input("Enter RoleArn to assume: ")
    while not options["region"]:
        region = input(REGION_PROMPT_MSG)
        options["region"] = region if validate_region(region) else False
    while not options["instance_name"]:
        instance_name = input(INSTANCE_PROMPT_MSG)
        if not instance_name:
            print_list_rds()
            continue
        is_instance_valid = validate_instance_name(instance_name)
        if not is_instance_valid:
            print_list_rds()
            continue
        else:
            options["instance_name"] = instance_name
    while not options["email"]:
        email = input(EMAIL_PROMPT_MSG)
        options["email"] = email if validate_email(email) else False
    print(EULA_INFO_MSG)
    options["accept"] = input("Type OK (case sensitive) to accept the EULA: ")
    if options["accept"] != ACCEPT_EULA_VALUE:
        print(EULA_ERROR_MSG)
        exit(1)


def create_stack():
    stack_info = CFBO(options["region"], os.environ["AWS_PROFILE"]).create_stack("ImpervaSnapshot", TEMPLATE_URL,
                                                                                 options["instance_name"],
                                                                                 get_token(options["email"]),
                                                                                 options["role_assume"], 80)
    if not stack_info:
        exit(1)
    stack_id = stack_info["StackId"]
    print("------------------------------")
    print("ImpervaSnapshot Stack created successfully (stack id: " + stack_id + ")")
    print("The report will be sent to this mailbox: " + options["email"])
    print("NOTE: ImpervaSnapshot Stack will be deleted automatically on scan completion")
    stack_url = "https://console.aws.amazon.com/cloudformation/home?region=" + \
                options["region"] + \
                "#/stacks/stackinfo?filteringStatus=active&filteringText=&viewNested=true&hideStacks=false&stackId=" + \
                stack_id
    print("Click here to see the progress: " + stack_url)


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ip:a:r:n:m:",
                                   ["interactive", "profile=", "role=", "region=", "instance=", "email=",
                                    "accept"])
        if not [item for item in opts if item[0] in ['-i', "--interactive"]]:
            fill_options_inline(opts)
        else:
            fill_options_interactive()
        create_stack()
    except getopt.GetoptError as e:
        print(e)
        exit(2)

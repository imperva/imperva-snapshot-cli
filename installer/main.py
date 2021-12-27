#!/usr/bin/python

import os
from rds_bo import RDSBO
from cf_bo import CFBO
import utils as ut
import requests
import sys
import getopt

EULA_INFO_MSG = "Please read the EULA: https://www.imperva.com/legal/license-agreement/"

EULA_ERROR_MSG = "Accepting the EULA is required to proceed with ImpervaSnapshot scanning"

INLINE_ERROR_MSG = "You didn't ask for interactive mode (-i) nor specified the params!"

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


def get_token(email):
    headers = {'Accept-Encoding': '*', 'content-type': 'application/x-www-form-urlencoded'}
    data = '{"eULAConsent": "True", "email": "' + email + '", "get_token": "true"}'

    response = requests.post(REG_URL, data=data,
                             headers=headers)
    print("Authentication Token: " + response.text)
    return response.text


def extract_region(region="", inline=False):  # problem with print, prints error msg even in interactive
    if not inline:
        region = input(REGION_PROMPT_MSG)
    while not region or region not in SUPPORTED_REGIONS:
        print("## Region " + region + " not supported ##")
        print("List of supported regions:")
        for r in SUPPORTED_REGIONS:
            print("* " + r)
        if inline:
            return False
        region = input(REGION_PROMPT_MSG)
    return region


def extract_instance_name(instance_name="", inline=False):  # problem with print, prints error msg even in interactive
    RDSBO_inst = RDSBO(options["region"], options["profile"])
    instance_name = RDSBO_inst.extract_rds_instance_name(instance_name, inline)
    if instance_name:
        snap_name = RDSBO_inst.get_snap_name(instance_name)  # no use, why define?
    return instance_name


def extract_mail(email="", inline=False):  # problem with print, prints error msg even in interactive
    if not inline:
        email = input(EMAIL_PROMPT_MSG)
    while not ut.is_mail_valid(email):
        print(EMAIL_ERROR_MSG)
        if inline:
            return False
        email = input(EMAIL_PROMPT_MSG)
    return email


def fill_options_inline(opts):
    if not opts:
        print(INLINE_ERROR_MSG)
        exit(1)
    error = False
    for opt, arg in opts:
        if opt in ('-p', "--profile"):
            options["profile"] = arg
        if opt in ('-a', "--role"):
            options["role_assume"] = arg
        if opt in ('-r', "--region"):
            options["region"] = extract_region(arg, True)
            if not options["region"]:
                break
        if opt in ('-n', "--instance"):
            options["instance_name"] = extract_instance_name(arg, True)
            if not options["instance_name"]:
                break
        if opt in ('-m', "--email"):
            options["email"] = extract_mail(arg, True)
            if not options["email"]:
                break
        if opt == "--accept":
            options["accept"] = ACCEPT_EULA_VALUE
    for option in options.keys():
        if not options[option]:
            print("Option " + option + " is invalid or missing")
            error = True
            break
    if error:
        exit(1)


def fill_options_interactive():
    options["profile"] = input("Enter your profile: ")
    options["role_assume"] = input("Enter RoleArn to assume: ")
    options["region"] = extract_region()
    options["instance_name"] = extract_instance_name()
    options["email"] = extract_mail()
    print(EULA_INFO_MSG)
    options["accept"] = input("Type OK (case sensitive) to accept the EULA: ")
    if options["accept"] != ACCEPT_EULA_VALUE:
        print(EULA_ERROR_MSG)
        exit(1)


def create_stack():
    stack_info = CFBO(options["region"], options["profile"]).create_stack("ImpervaSnapshot", TEMPLATE_URL,
                                                                          options["instance_name"], token,
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
    # print('Number of arguments:', len(sys.argv), 'arguments.')
    # print('Argument List:', str(sys.argv))
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ip:a:r:n:m:",
                                   ["interactive", "profile=", "role=", "region=", "instance=", "email=",
                                    "accept"])
    except getopt.GetoptError as e:
        print(e)
        sys.exit(2)
    if not [item for item in opts if item[0] in ['-i', "--interactive"]]:
        fill_options_inline(opts)
    else:
        fill_options_interactive()

    os.environ["AWS_PROFILE"] = options["profile"]  # why is it defined? whats the purpose of it
    token = "4612e8da-051d-40f7-89ce-d5a47c6ded48"  # get_token(REG_URL, options["email"])

    create_stack()

#!/usr/bin/python

import os
from rds_bo import RDSBO
from cf_bo import CFBO
import utils as ut
import requests
import sys

def get_supported_regions():
    list = ["eu-north-1", "eu-west-3", "eu-west-2", "eu-west-1", "us-west-2", "ap-southeast-2",
            "ap-northeast-2", "sa-east-1", "ap-northeast-1", "ap-south-1", "us-east-1", "us-east-2",
            "ap-southeast-1", "us-west-1", "eu-central-1", "ca-central-1"]
    return list


def get_token(regurl, email):
    headers = {'Accept-Encoding': '*', 'content-type': 'application/x-www-form-urlencoded'}
    data = '{"eULAConsent": "True", "email": "' + email + '", "get_token": "true"}'

    response = requests.post(regurl, data=data,
                             headers=headers)
    print("Authentication Token: " + response.text)
    return response.text


def extract_region():
    REGION_FOUND = False
    while not REGION_FOUND:
        region = input("Enter your region [click enter to to get the list of supported Regions]: ")
        supported_regions = get_supported_regions()
        if not region or region not in supported_regions:
            print("## Region " + region + " not supported ##")
            print("List of supported regions:")
            for r in supported_regions:
                print("* " + r)
        else:
            REGION_FOUND = True
    return region


def extract_mail():
    MAIL_VALID = False
    while not MAIL_VALID:
        email = input("Enter your Email [the report will be sent to the specified mailbox]: ")
        is_valid = ut.Utils.is_mail_valid(email)
        if is_valid:
            MAIL_VALID = True
        else:
            print("***** Email is not valid, please try again")
    return email


class Main:

    if __name__ == "__main__":
        print('Number of arguments:', len(sys.argv), 'arguments.')
        print('Argument List:', str(sys.argv))
        template_url = "https://labyrinth-cloudformation-staging.s3.amazonaws.com/impervasnapshot-root-cf.yml"
        reg_url = "https://mbb6dhvsy0.execute-api.us-east-1.amazonaws.com/stage/register"

        profile = input("Enter your profile: ")
        os.environ["AWS_PROFILE"] = profile
        role_assume = input("Enter RoleArn to assume: ")

        region = extract_region()
        RDSBO_inst = RDSBO(region, profile)
        instance_name = RDSBO_inst.extract_rds_instance_name()
        snap_name = RDSBO_inst.get_snap_name(instance_name)
        email = extract_mail()

        print("Please read the EULA: https://www.imperva.com/legal/license-agreement/")
        eula_agree = input("Type OK (case sensitive) to accept the EULA: ")
        if eula_agree != "OK":
            print("Accepting the EULA is required to proceed with ImpervaSnapshot scanning")
            exit(1)

        token = get_token(reg_url, email)

        stack_info = CFBO(region, profile).create_stack("ImpervaSnapshot", template_url, instance_name, token,
                                                        role_assume, 80)
        if not stack_info:
            exit(1)

        stack_id = stack_info["StackId"]
        print("------------------------------")
        print("ImpervaSnapshot Stack created successfully (stack id: " + stack_id + ")")
        print("The report will be sent to this mailbox: " + email)
        print("NOTE: ImpervaSnapshot Stack will be deleted automatically on scan completion")
        stack_url = "https://console.aws.amazon.com/cloudformation/home?region=" + region + "#/stacks/stackinfo?filteringStatus=active&filteringText=&viewNested=true&hideStacks=false&stackId=" + stack_id
        print("Click here to see the progress: " + stack_url)
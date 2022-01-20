import boto3
import botocore


class CFBO:
    def __init__(self, region):
        self.region = region
        self.cf_client = boto3.client('cloudformation', region_name=region)

    def create_stack(self, stack_name, template_url, database_name, token, role_assume, timeout):
        print("Creating 'ImpervaSnapshot' Stack - DBIdentifier: " + database_name + ", AuthenticationToken: " + token)
        try:
            if role_assume:
                stack_info = self.cf_client.create_stack(StackName=stack_name, TemplateURL=template_url, Parameters=[
                    {
                        'ParameterKey': 'AuthenticationToken',
                        'ParameterValue': token
                    },
                    {
                        'ParameterKey': 'DBIdentifier',
                        'ParameterValue': database_name
                    }
                ], TimeoutInMinutes=timeout, Capabilities=[
                    'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'
                ], RoleARN=role_assume)
            else:
                stack_info = self.cf_client.create_stack(StackName=stack_name, TemplateURL=template_url, Parameters=[
                    {
                        'ParameterKey': 'AuthenticationToken',
                        'ParameterValue': token
                    },
                    {
                        'ParameterKey': 'DBIdentifier',
                        'ParameterValue': database_name
                    }
                ], TimeoutInMinutes=timeout, Capabilities=[
                    'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'
                ])
            return stack_info
        except Exception as e:
            print("***** ERROR - Oops something happened while trying to run the Stack:")
            print(e)

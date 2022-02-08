# Imperva Snapshot™ CLI

Imperva Snapshot CLI is a Command Line tool designed to interact with Imperva Snapshot™. 
Imperva Snapshot is a fast and easy-to use cloud data security posture assessment service for Amazon RDS managed databases.
Imperva Snapshot delivers a detailed assessment report to your email with these findings:

- Misconfiguration & Bad Practices - A review of your cloud environment settings and database-specific configurations
- Known Vulnerabilities - Identifies and catalogs database vulnerabilities according to publicly disclosed CVEs
- Privacy & Compliance - Classifies sensitive content that may have a privacy impact

On-boarding takes seconds. A report will land in your inbox within 15-20 minutes

Imperva Snapshot can be also installed via [Imperva Snapshot official page](https://www.imperva.com/resources/free-cyber-security-testing-tools/imperva-snapshot-cloud-data-security-posture/): 

Here we will cover how to install it via CLI.

# CloudFormation
Imperva Snapshot CLI works by invoking AWS CloudFormation's Create Stack request on your account.
Behind the scenes, Imperva Snapshot CLI collects all the information needed in order to satisfy [Imperva Snapshot CloudFormation Templates](https://labyrinth-cloudformation.s3.amazonaws.com/impervasnapshot-root-cf.yml).

## CF Parameters
The CloudFormation requires only 3 parameter:
- StackName: The name of the CF stack. Which automatically is set by the CLI to 'Imperva Snapshot'
- AuthenticationToken: This is an autogenerated Token that identifies and authenticates users. In order to get the Authentication Token to your inbox, please register [here](https://www.imperva.com/resources/free-cyber-security-testing-tools/imperva-snapshot-cloud-data-security-posture/)
- DBIdentifier: For Classic RDS, use your DB instance ID. For Aurora, use your DB Cluster ID. You can extract your Identifiers from your [aws account page](https://console.aws.amazon.com/rds/home?#databases)

# Authentication
Imperva Snapshot uses 'boto' Credentials search order mechanism. There are 3 options to set your AWS permissions, and we will search for them in this order:
1. AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables
2. AWS_PROFILE environment variable
3. Default profile (can be found in ~/.aws/credentials)

You can see more about this [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)

# How to use it
To initiate an Imperva Snapshot scan you need to perform 4 simple steps:
1. git clone https://github.com/imperva/imperva-snapshot-cli.git
2. cd imperva-snapshot-cli
3. pip install -r requirements.txt
4. python3 ./installer/main.py -i

* You'll need to run `aws configure --profile name_of_your_profile` before you run the CLI

After running the shell script, the interactive CLI will help you fill in the required CF Parameters.

#Interactive vs Inline Mode 
To address all use cases, Imperva Snapshot CLI supports two modes: Interactive and Inline mode.

The Interactive Mode runs by using the -i parameter “python3 ./installer/main.py -i”. With this mode the CLI helps the user to validate the input parameters, listing all available RDS Instances per region & making sure the selected RDS Instance or Aurora Cluster are available in the selected region.

With the inline mode you can expect to get the same set of parameters but in an “inline mode”, for example:

`python3 ./installer/main.py token=YOUR_AUTH_TOKEN region=THE-LOCATION-OF-THE-RDS database=INSTANCE/CLUSTER-ID  accept_eula=OK`

This mode enables multiple option within the tool. To run periodically. To be integrated with any CI/CD process. Or to run immediately with a creation of new Databases

# AWS Roles
The ["roles-templates" folder in this project](https://github.com/imperva/imperva-snapshot-cli/tree/master/roles-templates) contains samples of AWS IAM Roles installed in your account. These Roles are automatically removed upon a scan success or failure.

## Running Imperva Snapshot with Minimal Permissions

To run an Imperva Snapshot scan, one needs to have the following permission, for example: 
- Create/Delete networking assets
- Restore a DB from a snapshot
- Create/Delete the new restored DB
- Save essential info in customer’s S3 buckets
- more...

In order to meet the “least privilege” principle Imperva Snapshot restricts the role permissions to the required minimum::
- The tool can delete only the DB we created
- The tool can restore only from the snapshot selected by the user
- The tool can only delete the VPC we have created 
- so forth 

Yet, one needs to have the specific list of roles to run the tool or have Admin permissions.

### Problem

There are times when the user running the tool doesn’t have Admin permissions and the Security team might not be willing to grant the above permissions (although the mentioned restrictions).
How can we help anyone to run the tool without the need to grant all restricted permissions or Admin privileges?

### Solution
The following is a technical description of the solution including some snippets.

#### Step 1
Security team creates a Role that enables users to assume it, with the following permissions [let’s call it: impv_snapshot_run_minimum_role]:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "iam:DeleteRole",
                "iam:CreateRole",
                "iam:CreatePolicy",
                "iam:DeletePolicy",
                "iam:GetPolicyVersion",
                "iam:GetPolicy",
                "iam:GetRolePolicy",
                "iam:GetRole",
                "iam:PutRolePolicy",
                "iam:AttachRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:DetachRolePolicy",
                "iam:PassRole"
            ],
            "Resource": [
                "arn:aws:iam::*:role/*labyrinth-root-role",
                "arn:aws:iam::*:role/*labyrinth-sandbox-role",
                "arn:aws:iam::*:role/*labyrinth-setup-role",
                "arn:aws:iam::*:role/*labyrinth-scanner-role",
                "arn:aws:iam::*:role/*labyrinth-reporter-role"
            ]
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "lambda:GetFunction",
                "lambda:DeleteFunction",
                "lambda:CreateFunction",
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:*:*:function:*labyrinth-setup-lambda",
                "arn:aws:lambda:*:*:function:*labyrinth-sandbox-lambda"
            ]
        },
        {
            "Sid": "VisualEditor3",
            "Effect": "Allow",
            "Action": [
                "s3:Get*"
            ],
            "Resource": [
                "arn:aws:s3:::*labyrinth-code*/*",
                "arn:aws:s3:::*labyrinth-code*"
            ]
        },
        {
            "Sid": "VisualEditor4",
            "Effect": "Allow",
            "Action": [
                "ec2:CreateVpc",
                "ec2:DescribeVpcs"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor40",
            "Effect": "Allow",
            "Action": [
                "ec2:ModifyVpcAttribute"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor5",
            "Effect": "Allow",
            "Action": [
                "ec2:DeleteVpc"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "ec2:ResourceTag/Proj": "impervasnapshot"
                }
            }
        },
        {
            "Sid": "VisualEditor6",
            "Effect": "Allow",
            "Action": [
                "ec2:CreateTags"
            ],
            "Resource": "arn:aws:ec2:*:*:*/*",
            "Condition": {
                "StringEquals": {
                    "ec2:ResourceTag/aws:cloudformation:logical-id": "SandboxVpc"

                }
            }
   
    ]
}
```


This set of permissions are the minimal permissions needed in order to make use of Imperva Snapshot's specific Roles, Functions, Buckets, VPCs.
As we can see, the roles are restricted to solely effect Imperva Snapshot assets.

This set of permissions will be assumed by the AWS User that requests to run the tool.


In addition, the AWS Role Trust Relationship should be set to `cloudformation.amazonaws.com service`.
This will assure that the AWS Role is assumable only via CloudFormation service.

#### Step 2
The Security team needs to create an AWS Policy that allows the user to:
1. ONLY assume the above role: `impv_snapshot_run_minimum_role`
2. Create and Run a CloudFormation Stack:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "arn:aws:iam::<ACCOUNT>:role/impv_snapshot_run_minimum_role"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::*labyrinth-code"
            ]
        },
        {
            "Sid": "VisualEditor4",
            "Effect": "Allow",
            "Action": "cloudformation:*",
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "cloudformation:TemplateUrl": [
                        "https://labyrinth-cloudformation.s3.amazonaws.com/impervasnapshot-root-cf.yml",
                        "https://labyrinth-cloudformation.s3.amazonaws.com/impervasnapshot-setup-cf.yml",
                        "https://labyrinth-cloudformation.s3.amazonaws.com/impervasnapshot-installer-cf.yml",
                    ]
                }
            }
        },
        {
            "Sid": "VisualEditor2",
            "Effect": "Allow",
            "Action": [
                "cloudformation:List*",
                "cloudformation:Describe*",
                "cloudformation:GetTemplateSummary"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor25",
            "Effect": "Allow",
            "Action": "cloudformation:DeleteStack",
            "Resource": "arn:aws:cloudformation:*:<ACCOUNT>:stack/ImpervaSnapshot/*"
        },
        {
            "Effect": "Allow",
            "Action": "iam:ListRoles",
            "Resource": "*"
        }
    ]
}
```

This policy only allows the user to allow Cloudformation to:
1. Assume `impv_snapshot_run_minimum_role` Role
2. Access to get Imperva Snapshot Code from Imperva's Buckets
3. Be able to run Imperva Snapshot specific CloudFormation Template
4. Delete Imperva Snapshot specific Stack

#### Step 3
Once the user is granted with these permissions, they can instruct CloudFormation to assume the “impv_snapshot_run_minimum_role” Role.

### Recap
There are 3 sets of permissions:
1. The “impv_snapshot_run_minimum_role” AWS Role which contains the restricted permissions needed to run Imperva Snapshot CloudFormation
2. The new policy attached to the user which enables them to instruct CloudFormation to assume the above role
3. The actual restricted Permissions granted to our assets to perform the scan

This way the Security team can create the “impv_snapshot_run_minimum_role” Role once, then each user that requests to run Imperva Snapshot will be granted with the AWS Policy that allows then to run only our template without having the permissions themselves 

# Your PDF report is on its way
Once the CF Stack is successfully created, Imperva Snapshot™ starts to create all the resources required in order to safely scan you RDS.
Upon scan completion a PDF report will be generated and sent to your mailbox.

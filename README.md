# Imperva Snapshot™ CLI

Imperva Snapshot CLI is a Command Line tool designed to interact with Imperva Snapshot™. 
Imperva Snapshot is a free, fast and easy-to use cloud data security posture assessment service for Amazon RDS managed databases.
Imperva Snapshot will deliver a detailed assessment report to your email with these findings:

- Misconfiguration & Bad Practices - Reviews cloud environment settings and database-specific configurations
- Known Vulnerabilities - Identifies and catalogs database vulnerabilities according to publicly disclosed CVEs
- Privacy & Compliance - Classifies sensitive content that may have a privacy impact
- On-boarding takes seconds, and a report will land in your inbox within 15-20 minutes

Imperva Snapshot can be also installed via [ImpervaSnapshot official page](https://www.imperva.com/resources/free-cyber-security-testing-tools/imperva-snapshot-cloud-data-security-posture/): 

Here we will cover how to install it via CLI.

# CloudFormation
imperva-snapshot-cli works by invoking AWS CloudFormation's Create Stack request on your account.
Behind the scenes, imperva-snapshot-cli collects all the information needs in order to satisfy [ImpervaSnapshot CloudFormation Templates](https://labyrinth-cloudformation.s3.amazonaws.com/impervasnapshot-root-cf.yml).

## CF Parameters
The CloudFormation requires only 3 parameter:
- StackName: The name of the CF stack. This is set to 'ImpervaSnapshot' automatically by the CLI
- AuthenticationToken: This is an autogenerated Token that identify and authenticate users. In case you already have one you can input it via the CLI, otherwise the CLI will automatically generate a new one for you
- DBIdentifier: For Classic RDS, use your DB instance ID. For Aurora, use your DB Cluster ID. You can extract your Identifiers from your [aws account page](https://console.aws.amazon.com/rds/home?#databases)

# How to use it
To initiate an Imperva Snapshot Scan you need to perform 4 simple steps:
1. git clone https://github.com/imperva/imperva-snapshot-cli.git
2. cd imperva-snapshot-cli
3. pip install -r requirements.txt
4. chmod +x installer/main.py
5. python3 ./installer/main.py -i

* You'll need to run `aws configure --profile name_of_your_profile` before you run the CLI

After running the shell script, the interactive CLI will help you fill in the required CF Parameters.

#Interactive vs Inline Mode 
In order to enable all the use-cases this CLI accepts two modes, the Interactive and the Inline mode.

The Interactive Mode run by using the -i parameter “python3 ./installer/main.py -i”. With this mode the CLI will help the user validate the input parameters, listing all available RDS Instances per region & making sure the selected RDS Instance or Aurora Cluster are available in the selected region.

The inline mode expects to get the same set of parameters but in an “inline mode”, for example:

python3 ./installer/main.py profile=MY-AWS-PROFILE region=THE-LOCATION-OF-THE-RDS database=INSTANCE/CLUSTER-ID email=REPORT-RECIPIENT  accept_eula=OK

This mode enables the tool to be run periodically or integrated with any CI/CD process or upon creation of new Databases

# AWS Roles
The "roles-templates" folder in this project contains samples of AWS IAM Roles installed in your account. These Roles are automatically removed upon success or failure.

# Your PDF report is on its way
Once the CF Stack will be successfully created, Imperva Snapshot™ will start to create all the resources required in order to safely scan you RDS.
At the end a PDF report will be generated and sent to your mailbox.

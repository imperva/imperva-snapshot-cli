import boto3
import botocore


class RDSBO:
    def __init__(self, region, profile):
        self.region = region
        try:
            self.rds_client = boto3.client('rds', region_name=region)
        except botocore.exceptions.ProfileNotFound:
            print("***** ERROR: AWS Profile " + profile + " doesn't exist")
            exit(1)

    def extract_rds_instance_name(self):
        RDS_FOUND = False
        while not RDS_FOUND:
            try:
                instance_name = input(
                    "Enter your instance name [leave empty to get a list of available RDS Instances]: ")
                if not instance_name:
                    self.print_list_rds()
                    continue
                rds_selected = self.rds_client.describe_db_instances(DBInstanceIdentifier=instance_name)
                instance_name = rds_selected["DBInstances"][0]["DBInstanceIdentifier"]
                print("✅ Selected RDS: " + instance_name)
                RDS_FOUND = True
                return instance_name
            except self.rds_client.exceptions.DBInstanceNotFoundFault:
                print("## DB " + instance_name + " NOT FOUND in region " + self.region + " ##")
                self.print_list_rds()
                # print("List of available instances in: " + self.region + ": ")
                # list_possible = self.rds_client.describe_db_instances()
                # for r in list_possible["DBInstances"]:
                #     print("* " + r["DBInstanceIdentifier"])

    def print_list_rds(self):
        print("List of available instances in: " + self.region + ": ")
        list_possible = self.rds_client.describe_db_instances()
        for r in list_possible["DBInstances"]:
            print("* " + r["DBInstanceIdentifier"])

    def get_snap_name(self, instance_name):
        try:
            snap_selected = self.rds_client.describe_db_snapshots(DBInstanceIdentifier=instance_name)
            snap_name = snap_selected["DBSnapshots"][0]["DBSnapshotIdentifier"]
            print("✅ Snapshot found: " + snap_name)
            return snap_name
        except self.rds_client.exceptions.DBSnapshotNotFoundFault:
            print("***** ERROR: DB Snapshot NOT FOUND for instance: " + instance_name + " in region: " + self.region)
            exit(1)

import sys

import boto3
import botocore


class ProfileError(Exception):
    pass


class InstanceError(Exception):
    pass


class SnapshotError(Exception):
    pass


class RDSBO:
    def __init__(self, region, profile):
        self.region = region
        try:
            self.rds_client = boto3.client('rds', region_name=region)
        except botocore.exceptions.ProfileNotFound:
            raise ProfileError("***** ERROR: AWS Profile " + profile + " doesn't exist")

    def extract_rds_instance_name(self, instance_name):
        try:
            rds_selected = self.rds_client.describe_db_instances(DBInstanceIdentifier=instance_name)
            instance_name = rds_selected["DBInstances"][0]["DBInstanceIdentifier"]
            return instance_name
        except self.rds_client.exceptions.DBInstanceNotFoundFault:
            raise InstanceError("## DB " + instance_name + " NOT FOUND in region " + self.region + " ##")

    def print_list_rds(self):
        print("List of available instances in " + self.region + ": ")
        list_possible = self.rds_client.describe_db_instances()
        for r in list_possible["DBInstances"]:
            print("* " + r["DBInstanceIdentifier"])

    def get_snap_name(self, instance_name):
        try:
            snap_selected = self.rds_client.describe_db_snapshots(DBInstanceIdentifier=instance_name)
            snap_name = snap_selected["DBSnapshots"][0]["DBSnapshotIdentifier"]
            return snap_name
        except self.rds_client.exceptions.DBSnapshotNotFoundFault:
            raise SnapshotError(
                "***** ERROR: DB Snapshot NOT FOUND for instance: " + instance_name + " in region: " + self.region)

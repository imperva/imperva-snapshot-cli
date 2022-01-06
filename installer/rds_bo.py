import sys

import boto3
import botocore


class ProfileError(Exception):
    pass


class DatabaseError(Exception):
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

    def extract_database_name(self, database_name):
        try:
            return self.extract_rds_instance_name(database_name)
        except DatabaseError as e:
            return self.extract_aurora_cluster_name(database_name)

    def print_list_dbs(self):
        self.print_list_rds()
        self.print_list_aurora()

    def extract_rds_instance_name(self, instance_name):
        try:
            rds_selected = self.rds_client.describe_db_instances(DBInstanceIdentifier=instance_name)
            instance_name = rds_selected["DBInstances"][0]["DBInstanceIdentifier"]
            return instance_name
        except self.rds_client.exceptions.DBInstanceNotFoundFault:
            raise DatabaseError("## DB " + instance_name + " NOT FOUND in region " + self.region + " ##")

    def print_list_rds(self):
        print("List of available instances (rds) in " + self.region + ": ")
        list_possible = self.rds_client.describe_db_instances()
        for r in list_possible["DBInstances"]:
            if "DBClusterIdentifier" not in r.keys():
                print("* " + r["DBInstanceIdentifier"])

    def extract_aurora_cluster_name(self, cluster_name):
        try:
            rds_selected = self.rds_client.describe_db_clusters(DBClusterIdentifier=cluster_name)
            cluster_name = rds_selected["DBClusters"][0]["DBClusterIdentifier"]
            return cluster_name
        except self.rds_client.exceptions.DBClusterNotFoundFault:
            raise DatabaseError("## DB " + cluster_name + " NOT FOUND in region " + self.region + " ##")

    def print_list_aurora(self):
        print("List of available clusters (aurora) in " + self.region + ": ")
        list_possible = self.rds_client.describe_db_clusters()
        for r in list_possible["DBClusters"]:
            print("* " + r["DBClusterIdentifier"])

    def get_snap_name(self, instance_name):
        try:
            snap_selected = self.rds_client.describe_db_snapshots(DBInstanceIdentifier=instance_name)
            snap_name = snap_selected["DBSnapshots"][0]["DBSnapshotIdentifier"]
            return snap_name
        except self.rds_client.exceptions.DBSnapshotNotFoundFault:
            raise SnapshotError(
                "***** ERROR: DB Snapshot NOT FOUND for instance: " + instance_name + " in region: " + self.region)

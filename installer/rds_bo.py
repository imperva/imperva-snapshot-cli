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
    def __init__(self, region):
        self.region = region
        self.rds_client = boto3.client('rds', region_name=region)
        self.lst_rds = self.get_list_rds()
        self.lst_aurora = self.get_list_aurora()
        self.lst_db = self.lst_rds + self.lst_aurora

    def print_list_dbs(self):
        print("List of available instances (rds) in " + self.region + ": ")
        for (i, item) in enumerate(self.lst_rds, start=1):
            print(str(i) + " - " + item)
        print("List of available clusters (aurora) in " + self.region + ": ")
        for (i, item) in enumerate(self.lst_aurora, start=len(self.lst_rds) + 1):
            print(str(i) + " - " + item)

    def extract_database_name(self, database_name):
        try:
            if (isinstance(database_name, int) or database_name.isnumeric()) and int(database_name) != 0:
                return self.lst_db[int(database_name) - 1]
            elif database_name in self.lst_db:
                return database_name
            else:
                raise DatabaseError("## DB " + database_name + " NOT FOUND in region " + self.region + " ##")
        except IndexError:
            raise DatabaseError("## DB " + database_name + " NOT FOUND in region " + self.region + " ##")

    def get_list_rds(self):
        lst = []
        list_possible = self.rds_client.describe_db_instances()
        for r in list_possible["DBInstances"]:
            if "DBClusterIdentifier" not in r.keys():
                lst.append(r["DBInstanceIdentifier"])
        return lst

    def get_list_aurora(self):
        lst = []
        list_possible = self.rds_client.describe_db_clusters()
        for r in list_possible["DBClusters"]:
            if r["Engine"] not in ("neptune", "docdb") and r["EngineMode"] != "serverless":
                lst.append(r["DBClusterIdentifier"])
        return lst

    def get_snap_name(self, instance_name):
        try:
            snap_selected = self.rds_client.describe_db_snapshots(DBInstanceIdentifier=instance_name)
            snap_name = snap_selected["DBSnapshots"][0]["DBSnapshotIdentifier"]
            return snap_name
        except self.rds_client.exceptions.DBSnapshotNotFoundFault:
            raise SnapshotError(
                "***** ERROR: DB Snapshot NOT FOUND for instance: " + instance_name + " in region: " + self.region)

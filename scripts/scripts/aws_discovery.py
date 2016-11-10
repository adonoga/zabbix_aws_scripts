#!/usr/bin/python
import boto3
import ConfigParser
import json
import sys


class Discoverer:


    def __init__(self, config, account, service, region):
        aws_key = config.get(account, "key")
        aws_secret = config.get(account, "secret")
        self._methods = {
                         "rds": self._get_rds_instances,
                         "emr": self._get_emr_clusters,
                         "ec2": self._get_ec2_instances,
                         "elb": self._get_elb_balancers,
        }
        if not region:
            region = self.get_aws_region()
        self.client = boto3.client(
            service,
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name=region)
        self.service = service

    def get_instances(self):
        discovery_method = self._methods[self.service]
        data = discovery_method()
        return json.dumps({"data": data})

    def _get_rds_instances(self):
        response = self.client.describe_db_instances()
        data = list()
        for instance in response["DBInstances"]:
            ldd = {
                    "{#STORAGE}": int(instance["AllocatedStorage"]) * pow(1024, 3),
                    "{#RDS_ID}": instance["DBInstanceIdentifier"]
            }
            data.append(ldd)
        return data

    def _get_ec2_instances(self):
        response = self.client.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["running"] }])
        instances = list()
        for reservation in response["Reservations"]:
            instances.extend(reservation["Instances"])
        data = list()
        for instance in instances:
            name = ""
            ldd = {
                    "{#INSTANCE_ID}":   instance["InstanceId"],
                    "{#PRIVATE_IP}":    instance["PrivateIpAddress"]
            }
            for tag in instance["Tags"]:
                if tag["Key"] == "Name":
                    name = tag["Value"] if tag["Value"] else ldd["{#INSTANCE_ID}"]
                if not name:
                    name = instance["InstanceId"]
                ldd["{#NAME}"] = name
            data.append(ldd)
        return data

    def _get_emr_clusters(self):
        response = self.client.list_clusters(ClusterStates=["RUNNING", "WAITING",
                                    "STARTING", "BOOTSTRAPPING"])
        data = list()
        for cluster in response["Clusters"]:
            ldd = {
                    "{#CLUSTER_ID}":      cluster["Id"],
                    "{#CLUSTER_NAME}":    cluster["Name"],
            }
            data.append(ldd)
        return data

    def _get_elb_balancers(self):
        response = self.client.describe_load_balancers()
        data = list()
        for balancer in response["LoadBalancerDescriptions"]:
            ldd = {
                    "{#BALANCER_NAME}": balancer["LoadBalancerName"]
            }
            data.append(ldd)
        return data

if __name__ == "__main__":
    config = ConfigParser.ConfigParser()
    config.readfp(open("/usr/lib/zabbix/scripts/conf/aws.conf"))
    region, service, account = sys.argv[1:]
    d = Discoverer(config, account, service, region)
    print d.get_instances()

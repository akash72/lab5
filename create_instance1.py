#!/usr/bin/env python

# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example of using the Compute Engine API to create and delete instances.

Creates a new compute engine instance and uses it to apply a caption to
an image.

    https://cloud.google.com/compute/docs/tutorials/python-guide

For more information, see the README.md under /compute.
"""

import argparse
import os
import time

import googleapiclient.discovery
from six.moves import input
from pprint import pprint
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import google.oauth2.service_account as service_account

# [START list_instances]
def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None
# [END list_instances]


# [START create_instance]
def create_instance(compute, project, zone, name, bucket):
    # Get the latest Debian Jessie image.
    image_response = compute.images().getFromFamily(
        project='ubuntu-os-cloud', family='ubuntu-1804-lts').execute()
    source_disk_image = image_response['selfLink']

    # Configure the machine
    machine_type = "zones/%s/machineTypes/n1-standard-1" % zone
    startup_script = open(
        os.path.join(
            os.path.dirname(__file__), 'startup-script1.sh'), 'r').read()
    service_cred = open(
        os.path.join(
            os.path.dirname(__file__), 'service-credentials.json'), 'r').read()
    image_url = "http://storage.googleapis.com/gce-demo-input/photo.jpg"
    image_caption = "Ready for dessert?"

    config = {
        'name': name,
        'machineType': machine_type,

        # Specify the boot disk and the image to use as a source.
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                }
            }
        ],

        # Specify a network interface with NAT to access the public
        # internet.
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],

        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_write',
                'https://www.googleapis.com/auth/logging.write'
            ]
        }],

        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        'metadata': {
            'items': [{
                # Startup script is automatically executed by the
                # instance upon startup.
                'key': 'service-cred',
                'value': service_cred
            }, {  
                'key': 'startup-script1',
                'value': startup_script
            }, {
                'key': 'url',
                'value': image_url
            }, {
                'key': 'text',
                'value': image_caption
            }, {
                'key': 'bucket',
                'value': bucket
            }]
        }
    }

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()
# [END create_instance]


# [START delete_instance]
def delete_instance(compute, project, zone, name):
    return compute.instances().delete(
        project=project,
        zone=zone,
        instance=name).execute()
# [END delete_instance]


# [START wait_for_operation]
def wait_for_operation(compute, project, zone, operation):
    print('Waiting for operation to finish...')
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result

        time.sleep(1)
# [END wait_for_operation]


# [START run]
def main(project, bucket, zone, instance_name, wait=True):
    compute = googleapiclient.discovery.build('compute', 'v1')

    print('Creating instance.')

    operation = create_instance(compute, project, zone, instance_name, bucket)
    wait_for_operation(compute, project, zone, operation['name'])

    instances = list_instances(compute, project, zone)

    print('Instances in project %s and zone %s:' % (project, zone))
    for instance in instances:
        print('-' + instance['name'])
      #  print(' For accessing the ' + instance['name'] +' VM use the following link')
      #  print('http://{}:5000'.format(instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']))
        

    print("""
Instance created.
It will take a minute or two for the instance to complete work.
Check this URL: http://storage.googleapis.com/{}/output.png
Once the image is uploaded press enter to delete the instance.
""".format(bucket))

   # if wait:
    #    input()

    #print('Deleting instance.')

    #operation = delete_instance(compute, project, zone, instance_name)
    #wait_for_operation(compute, project, zone, operation['name'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('project_id', help='Your Google Cloud project ID.')
    parser.add_argument(
        'bucket_name', help='Your Google Cloud Storage bucket name.')
        
    parser.add_argument(
        '--zone',
        default='us-west1-b',
        help='Compute Engine zone to deploy to.')
    parser.add_argument(
        '--name', default='demo1-instance', help='New instance name.')

    args = parser.parse_args()
    credentials = service_account.Credentials.from_service_account_file(filename='service-credentials.json')
    project = os.getenv('GOOGLE_CLOUD_PROJECT') or 'assignment1-251518'
    service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

    # Project ID for this request.
    project = 'assignment1-251518'  # TODO: Update placeholder value.
    zone = 'us-west1-b'
    instance = 'demo1-instance'
    firewall_body = {
    "name": "allow-5000",
    "allowed": [
        {
        "IPProtocol": "tcp",
        "ports": [
            "5000"
        ],
        "targetTags": [
            "allow-5000"
        ],
        }
    ],
    }

    

    list_of_firewalls = service.firewalls().list(project=project)
    firewalls_list = list_of_firewalls.execute()
    firewall_name_list = []
    for firewall in firewalls_list['items']:
        firewall_name_list.append(firewall['name'])
    if("allow-5000" not in firewall_name_list):
        request = service.firewalls().insert(project=project, body=firewall_body)
        response = request.execute()
        pprint(response)
    else:
        pprint("allow-5000 is already there in the list.")

    
    main(args.project_id, args.bucket_name, args.zone, args.name)
    get_request = service.instances().get(project=project, zone=zone, instance=instance)
    get_response = get_request.execute()
    pprint(get_response['tags']['fingerprint'])
    fingerprint = get_response['tags']['fingerprint']

    tags_body = {
        "items": [
            "allow-5000"
        ],
        "fingerprint" : fingerprint
    }
    set_tag_request = service.instances().setTags(project=project, zone=zone, instance=instance,body=tags_body)
    set_tag_response = set_tag_request.execute()
    pprint(set_tag_response)

    pprint("External IP link of the created instance is")
    pprint("http://{}:5000".format(get_response['networkInterfaces'][0]['accessConfigs'][0]['natIP']))
# [END run]
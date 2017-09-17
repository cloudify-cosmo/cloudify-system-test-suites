########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

from time import time

from cloudify_rest_client import CloudifyClient


def test_tenants_with_resources(manager, resource_creator, request, logger):
    """
    Test how many tenants with resources a manager can handle
    """
    start_time = time()
    tenants_count = int(request.config.getoption('--tenants-count'))
    threads_count = 50
    tenants = resource_creator.create_tenants(tenants_count, threads_count)
    _create_tenants_resources(manager, resource_creator, tenants)
    resource_creator.delete_all_tenants(tenants, threads_count=10)
    end_time = time()
    logger.info('{0} took {1:.2f} seconds and created {2} tenants'
                .format('test_tenants_with_resources', end_time - start_time, tenants_count))


def test_many_tenants_creation(manager, resource_creator, logger):
    """
    Test how many tenants can be created on a manager
    """
    start_time = time()
    tenants_count = 10000
    tenants = resource_creator.create_tenants(tenants_count, threads_count=100)

    # Take only the first 1000 tenants
    tenants = tenants[:1000]
    _create_tenants_resources(manager, resource_creator, tenants)
    end_time = time()
    logger.info('{0} took {1:.2f} seconds and created {2} tenants'.format(
        'test_many_tenants_creation', end_time - start_time, tenants_count))


def _create_tenants_resources(manager, resource_creator, tenants):
    resource_creator.upload_plugins(tenants, threads_count=10)
    _change_blueprint_to_simple(manager, resource_creator)
    resource_creator.create_deployments_in_tenants(tenants, threads_count=50)
    client = CloudifyClient(
        host=manager.ip_address, username='admin', password='admin', tenant=tenants[0])

    # Only one deployment per tenant
    deployments = client.deployments.list()
    assert deployments.metadata.pagination.total == 1


def _change_blueprint_to_simple(manager, resource_creator):
    resource_creator.blueprint_example.blueprint_path = \
        'blueprint-examples/simple-blueprint.yaml'
    resource_creator.blueprint_example.inputs = {
        'host_ip': manager.ip_address,
        'agent_user': 'centos',
        'agent_private_key_path': manager.remote_private_key_path
    }

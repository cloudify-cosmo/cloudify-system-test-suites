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
from retrying import retry

from .constants import TERMINATED_STATE, PAGINATION_PARAMS


def check_disk_space(manager, logger):
    logger.info('The manager disk space :')
    with manager.ssh() as fabric_ssh:
        fabric_ssh.run('df -h /')


def get_resource_list(resource_client, resource_name, logger, all_tenants=False):
    start_time = time()
    resource_list = resource_client.list(_all_tenants=all_tenants,
                                         **PAGINATION_PARAMS)
    end_time = time()
    logger.info('{0} list took {1:.2f} seconds'.format(resource_name,
                                                       end_time - start_time))
    return resource_list


def create_one_deployment(resource_creator, blueprint_id, logger):
    logger.info('Creating 1 deployment...')
    start_time = time()
    deployment_id = resource_creator.create_deployment(blueprint_id=blueprint_id)
    _wait_for_deployment_executions(deployment_id, resource_creator.client, logger)
    resource_creator.deployments = None
    end_time = time()
    logger.info('Created 1 deploymet in {0:.2f} seconds'.format(end_time - start_time))


@retry(stop_max_attempt_number=10, wait_fixed=1000)
def _wait_for_deployment_executions(deployment_id, manager_client, logger):
    logger.info('Waiting for active executions of deployment_id {}'.format(deployment_id))
    executions = manager_client.executions.list(deployment_id=deployment_id,
                                                **PAGINATION_PARAMS)
    active_executions = [exe for exe in executions if
                         exe.status != TERMINATED_STATE]
    assert len(active_executions) == 0
    logger.info('The executions terminated successfully')

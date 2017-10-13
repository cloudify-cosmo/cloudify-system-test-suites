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

from .framework.constants import BLUEPRINT_TYPES


def test_agents(resource_creator, deployments_count, request, logger):
    """
    Test how agents affect the manager
    """
    blueprint_type = _init_blueprint_type(request)
    resource_creator.blueprint_example.blueprint_path = \
        'blueprint-examples/{}-blueprint.yaml'.format(blueprint_type)
    threads_count = deployments_count
    start_time = time()
    blueprint_id = resource_creator.upload_blueprint()
    resource_creator.create_deployments(deployments_count,
                                        threads_count,
                                        blueprint_id)
    resource_creator.install_deployments(deployments_count,
                                         threads_count)
    end_time = time()
    logger.info('{0} with {1} blueprint took {2:.2f} seconds'.format(
        'test_agents', blueprint_type, (end_time - start_time)))
    logger.info("For checking the manager's metrics in Datadog go to {}"
                .format('https://app.datadoghq.com/dash/host/328651819'))

    # Enable the user to check the manager's metrics in Datadog
    raw_input('Enter any key to end the test and destroy the manager : ')
    resource_creator.uninstall_all_deployments(threads_count)
    resource_creator.delete_all_deployments(threads_count)


def _init_blueprint_type(request):
    blueprint_type = request.config.getoption('--blueprint-type')
    if blueprint_type not in BLUEPRINT_TYPES:
        raise ValueError('blueprint_type is not valid, should be one of {}'.
                         format(', '.join(BLUEPRINT_TYPES)))
    return blueprint_type

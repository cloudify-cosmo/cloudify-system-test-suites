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

from framework import util


def test_many_deployments_creation(manager, resource_creator, deployments_count, logger):
    """
    Test many deployments creation
    """
    start_time = time()
    threads_count = 100
    deployments_count -= 1
    blueprint_id = resource_creator.upload_blueprint()
    util.check_disk_space(manager, logger)
    resource_creator.create_deployments(deployments_count,
                                        threads_count,
                                        blueprint_id,
                                        wait_after_action=10)

    # Creating one last deployment to see how much time it takes
    util.create_one_deployment(resource_creator, blueprint_id, logger)
    _nodes_list(manager.client, logger)
    _node_instances_list(manager.client, logger)
    util.check_disk_space(manager, logger)
    resource_creator.delete_all_deployments(threads_count)
    end_time = time()
    logger.info('{0} took {1:.2f} seconds'.format(
        'test_many_deployments_creation', end_time - start_time))


def test_many_deployments_creation_concurrent(resource_creator, deployments_count, logger):
    """
    Test many deployments creation simultaneously
    """
    start_time = time()
    threads_count = deployments_count
    blueprint_id = resource_creator.upload_blueprint()
    resource_creator.create_deployments(deployments_count,
                                        threads_count,
                                        blueprint_id)
    resource_creator.delete_all_deployments(threads_count)
    end_time = time()
    logger.info('{0} took {1:.2f} seconds'.format(
        'test_many_deployments_creation_concurrent', end_time - start_time))


def test_many_deployments_installs(resource_creator, deployments_count, logger):
    """
    Test many deployments installs simultaneously
    """
    start_time = time()
    threads_count = deployments_count
    blueprint_id = resource_creator.upload_blueprint()
    resource_creator.create_deployments(deployments_count,
                                        threads_count,
                                        blueprint_id)
    resource_creator.install_deployments(deployments_count,
                                         threads_count)
    resource_creator.uninstall_all_deployments(threads_count)
    resource_creator.delete_all_deployments(threads_count)
    end_time = time()
    logger.info('{0} took {1:.2f} seconds'.format(
        'test_many_deployments_installs', end_time - start_time))


def _nodes_list(client, logger):
    util.get_resource_list(client.nodes, 'Nodes', logger)


def _node_instances_list(client, logger):
    util.get_resource_list(client.node_instances, 'Nodes instances', logger)

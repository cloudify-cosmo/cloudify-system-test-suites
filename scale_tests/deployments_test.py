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


def test_many_deployments_creation(resource_creator, logger):
    """
    Test many deployments creation simultaneously
    """
    start_time = time()
    deployments_count = 300
    threads_count = 300
    blueprint_id = resource_creator.upload_blueprint()
    resource_creator.create_deployments(deployments_count,
                                        threads_count,
                                        blueprint_id)
    resource_creator.delete_all_deployments(threads_count)
    end_time = time()
    logger.info('{0} took {1:.2f} seconds'.format(
        'test_many_deployments_creation', end_time - start_time))


def test_many_deployments_installs(resource_creator, logger):
    """
    Test many deployments installs simultaneously
    """
    start_time = time()
    deployments_count = 10
    threads_count = 10
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

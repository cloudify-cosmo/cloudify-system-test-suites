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

import uuid
import itertools
from time import time, sleep
from multiprocessing.pool import ThreadPool as Pool

from retrying import retry

from constants import TERMINATED_STATE, PAGINATION_PARAMS


class ConcurrentResourceCreator(object):
    """Creates cloudify resources on a manager concurrently"""

    def __init__(self, manager_client, blueprint_example, logger):
        self.logger = logger
        self.client = manager_client
        self.blueprint_example = blueprint_example
        self.wait_after_action = 0
        self._deployments = None

    @property
    def deployments(self):
        if not self._deployments:
            start_time = time()
            self._deployments = self.client.deployments.list(**PAGINATION_PARAMS)
            end_time = time()
            self.logger.info('Deployments list took {0:.2f} seconds'
                             .format(end_time - start_time))
        return self._deployments

    def upload_blueprint(self, _=None):
        """
        Uploads a blueprint with random blueprint_id
        _ is unused argument because of the pool.map function signature
        """
        blueprint_id = uuid.uuid4().hex
        self.client.blueprints.upload(self.blueprint_example.blueprint_path,
                                      blueprint_id)
        return blueprint_id

    def upload_blueprints(self, blueprints_count, threads_count):
        elapsed_time = self._run_action_concurrently(threads_count,
                                                     self.upload_blueprint,
                                                     range(blueprints_count))
        self.logger.info('Uploaded {0} blueprints in {1:.2f} seconds'.format(
            blueprints_count, elapsed_time))
        self._assert_blueprints_count(blueprints_count)

    def create_deployments(
            self, deployments_count, threads_count, blueprint_id, wait_after_action=0):
        self.wait_after_action = wait_after_action
        self.logger.info('Creating {0} deployments...'.format(deployments_count))
        blueprint_ids = itertools.repeat(blueprint_id, deployments_count)
        elapsed_time = self._run_action_concurrently(threads_count,
                                                     self._create_deployment,
                                                     blueprint_ids)
        self.logger.info('Created {0} deployments in {1:.2f} seconds'.format(
            deployments_count, elapsed_time))
        self._assert_deployments_count(deployments_count)
        self._wait_for_active_executions()

    def install_deployments(self, deployments_count, threads_count):
        if len(self.deployments) < deployments_count:
            self.logger.error("There aren't enough deployments for installing "
                              "{} deployments".format(deployments_count))
            return

        self.logger.info('Installing {0} deployments...'.format(deployments_count))
        deployment_ids = [deployment.id for deployment in
                          self.deployments[:deployments_count]]
        elapsed_time = self._run_action_concurrently(threads_count,
                                                     self._install_deployment,
                                                     deployment_ids)
        self.logger.info('Installed {0} deployments in {1:.2f} seconds'.format(
            deployments_count, elapsed_time))
        self._wait_for_active_executions()

    def uninstall_all_deployments(self, threads_count):
        self.logger.info('Uninstalling {0} deployments...'.format(len(self.deployments)))
        deployment_ids = [deployment.id for deployment in self.deployments]
        elapsed_time = self._run_action_concurrently(
            threads_count, self._uninstall_deployment, deployment_ids)
        self.logger.info('Uninstalled {0} deployments in {1:.2f} seconds'
                         .format(len(deployment_ids), elapsed_time))
        self._wait_for_active_executions()

    def delete_all_deployments(self, threads_count):
        self.logger.info('Deleting {0} deployments...'.format(len(self.deployments)))
        deployment_ids = [deployment.id for deployment in self.deployments]
        elapsed_time = self._run_action_concurrently(
            threads_count, self._delete_deployment, deployment_ids)
        self.logger.info('Deleted {0} deployments in {1:.2f} seconds'.format(
            len(deployment_ids), elapsed_time))
        self._deployments = 0
        self._assert_deployments_count(0)

    def _run_action_concurrently(self, threads_count, function, iterable):
        pool = Pool(processes=threads_count)
        start_time = time()
        pool.map(function, iterable)
        pool.close()
        pool.join()
        end_time = time()
        return end_time - start_time

    @retry(stop_max_attempt_number=10, wait_fixed=60*1000)
    def _wait_for_active_executions(self):
        self.logger.info('Waiting for active executions')
        executions = self.client.executions.list(include_system_workflows=True,
                                                 **PAGINATION_PARAMS)
        active_executions = [exe for exe in executions if exe.status != TERMINATED_STATE]
        assert len(active_executions) == 0
        self.logger.info('All the executions terminated successfully')

    def _create_deployment(self, blueprint_id):
        self.client.deployments.create(blueprint_id,
                                       deployment_id=uuid.uuid4().hex,
                                       inputs=self.blueprint_example.inputs)
        sleep(self.wait_after_action)

    def _install_deployment(self, deployment_id):
        self.client.executions.start(deployment_id, 'install')

    def _uninstall_deployment(self, deployment_id):
        self.client.executions.start(deployment_id,
                                     'uninstall',
                                     parameters={'ignore_failure': True},
                                     allow_custom_parameters=True,
                                     force=True)

    def _delete_deployment(self, deployment_id):
        self.client.deployments.delete(deployment_id)

    def _assert_deployments_count(self, expected_count):
        assert self.deployments.metadata.pagination.total == expected_count

    def _assert_blueprints_count(self, expected_count):
        start_time = time()
        blueprints_list = self.client.blueprints.list()
        end_time = time()
        self.logger.info('Blueprints list took {0:.2f} seconds'.format(
            end_time - start_time))
        assert blueprints_list.metadata.pagination.total == expected_count

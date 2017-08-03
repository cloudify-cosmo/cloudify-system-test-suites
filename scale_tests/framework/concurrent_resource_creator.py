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
from time import time
from multiprocessing.pool import ThreadPool as Pool

from retrying import retry


class ConcurrentResourceCreator(object):
    """Creates cloudify resources on a manager concurrently"""

    def __init__(self, manager_client, blueprint_example, logger):
        self.logger = logger
        self.client = manager_client
        self.blueprint_example = blueprint_example

    def upload_blueprint(self):
        blueprint_id = uuid.uuid4().hex
        self.client.blueprints.upload(self.blueprint_example.blueprint_path,
                                      blueprint_id)
        return blueprint_id

    def create_deployments(
            self, deployments_count, threads_count, blueprint_id):
        blueprint_ids = itertools.repeat(blueprint_id, deployments_count)
        elapsed_time = self._run_action_concurrently(threads_count,
                                                     self._create_deployment,
                                                     blueprint_ids)
        self.logger.info('Created {0} deployments in {1:.2f} seconds'.format(
            deployments_count, elapsed_time))
        self._assert_deployments_count(deployments_count)

    def install_deployments(self, deployments_count, threads_count):
        self._waiting_for_active_executions()
        deployments = self.client.deployments.list()
        if len(deployments) < deployments_count:
            self.logger.error("There aren't enough deployments for installing "
                              "{} deployments".format(deployments_count))
            return

        deployment_ids = [deployment.id for deployment in
                          deployments[:deployments_count]]
        elapsed_time = self._run_action_concurrently(threads_count,
                                                     self._install_deployment,
                                                     deployment_ids)
        self.logger.info('Installed {0} deployments in {1:.2f} seconds'.format(
            deployments_count, elapsed_time))

    def uninstall_all_deployments(self, threads_count):
        self._waiting_for_active_executions()
        deployments = self.client.deployments.list()
        deployment_ids = [deployment.id for deployment in deployments]
        elapsed_time = self._run_action_concurrently(
            threads_count, self._uninstall_deployment, deployment_ids)
        self.logger.info('Uninstalled {0} deployments in {1:.2f} seconds'.format(
            len(deployments), elapsed_time))

    def delete_all_deployments(self, threads_count):
        self._waiting_for_active_executions()
        deployments = self.client.deployments.list()
        deployment_ids = [deployment.id for deployment in deployments]
        elapsed_time = self._run_action_concurrently(
            threads_count, self._delete_deployment, deployment_ids)
        self.logger.info('Deleted {0} deployments in {1:.2f} seconds'.format(
            len(deployments), elapsed_time))
        self._assert_deployments_count(0)

    def _run_action_concurrently(self, threads_count, function, iterable):
        pool = Pool(processes=threads_count)
        start_time = time()
        pool.map(function, iterable)
        pool.close()
        pool.join()
        end_time = time()
        return end_time - start_time

    @retry(stop_max_attempt_number=10,
           wait_fixed=60*1000)
    def _waiting_for_active_executions(self):
        self.logger.info('Waiting for active executions')
        active_or_failed = list(ExecutionState.STATES)
        active_or_failed.remove(ExecutionState.TERMINATED)
        executions = self.client.executions.list(include_system_workflows=True,
                                                 status=active_or_failed)
        assert len(executions.items) == 0

    def _create_deployment(self, blueprint_id):
        self.client.deployments.create(blueprint_id,
                                       deployment_id=uuid.uuid4().hex,
                                       inputs=self.blueprint_example.inputs)

    def _install_deployment(self, deployment_id):
        self.client.executions.start(deployment_id, 'install')

    def _uninstall_deployment(self, deployment_id):
        self.client.executions.start(deployment_id, 'uninstall', force=True)

    def _delete_deployment(self, deployment_id):
        self.client.deployments.delete(deployment_id)

    def _assert_deployments_count(self, expected_count):
        deployments_list = self.client.deployments.list()
        assert deployments_list.metadata.pagination.total == expected_count


class ExecutionState(object):
    TERMINATED = 'terminated'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    PENDING = 'pending'
    STARTED = 'started'
    CANCELLING = 'cancelling'
    FORCE_CANCELLING = 'force_cancelling'

    STATES = [TERMINATED, FAILED, CANCELLED, PENDING, STARTED,
              CANCELLING, FORCE_CANCELLING]

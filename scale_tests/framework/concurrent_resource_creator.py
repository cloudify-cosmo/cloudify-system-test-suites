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

from cloudify_rest_client import CloudifyClient

from util import get_resource_list
from constants import TERMINATED_STATE, PAGINATION_PARAMS


class ConcurrentResourceCreator(object):
    """Creates cloudify resources on a manager concurrently"""

    def __init__(self, manager, blueprint_example, logger):
        self.logger = logger
        self.manager = manager
        self.client = manager.client
        self.blueprint_example = blueprint_example
        self.wait_after_action = 0
        self._deployments = None

    @property
    def deployments(self):
        if not self._deployments:
            self._deployments = get_resource_list(
                self.client.deployments, 'Deployments', self.logger, all_tenants=True)
        return self._deployments

    @deployments.setter
    def deployments(self, deployments):
        self._deployments = deployments

    def upload_blueprint(self, _=None, client=None):
        """
        Uploads a blueprint with random blueprint_id
        _ is unused argument because of the pool.map function signature
        """
        client = client or self.client
        blueprint_id = uuid.uuid4().hex
        client.blueprints.upload(self.blueprint_example.blueprint_path, blueprint_id)
        return blueprint_id

    def upload_blueprints(self, blueprints_count, threads_count):
        self.logger.info('Uploading {0} blueprints...'.format(blueprints_count))
        elapsed_time = self._run_action_concurrently(threads_count,
                                                     self.upload_blueprint,
                                                     range(blueprints_count))
        self.logger.info('Uploaded {0} blueprints in {1:.2f} seconds'.format(
            blueprints_count, elapsed_time))
        self._assert_blueprints_count(blueprints_count)

    def create_deployment(self, blueprint_id, client=None):
        client = client or self.client
        deployment = client.deployments.create(blueprint_id,
                                               deployment_id=uuid.uuid4().hex,
                                               inputs=self.blueprint_example.inputs)

        sleep(self.wait_after_action)
        return deployment.id

    def create_deployments(self, deployments_count, threads_count, blueprint_id,
                           existing_deployments_count=0, wait_after_action=0):
        self.wait_after_action = wait_after_action
        self.logger.info('Creating {0} deployments...'.format(deployments_count))
        blueprint_ids = itertools.repeat(blueprint_id, deployments_count)
        elapsed_time = self._run_action_concurrently(threads_count,
                                                     self.create_deployment,
                                                     blueprint_ids)
        self.logger.info('Created {0} deployments in {1:.2f} seconds'.format(
            deployments_count, elapsed_time))
        self.wait_after_action = 0
        self._deployments = None
        self._wait_for_active_executions()
        self._assert_deployments_count(deployments_count + existing_deployments_count)

    def create_deployments_in_tenants(self, tenants, threads_count):
        deployments_cont = len(tenants)
        self.logger.info('Creating {0} deployments in different tenants...'
                         .format(deployments_cont))
        elapsed_time = self._run_action_concurrently(
            threads_count, self._create_deployment_in_tenant, tenants)
        self.logger.info('Created {0} deployments in different tenants in {1:.2f} seconds'.
                         format(deployments_cont, elapsed_time))
        self._wait_for_active_executions()
        self._assert_deployments_count(deployments_cont)
        self._assert_blueprints_count(deployments_cont)

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
        self._deployments = None
        self._assert_deployments_count(0)

    def upload_plugins(self, tenants, threads_count):
        plugins_count = len(tenants)
        self.logger.info('Uploading {0} plugins to different tenants...'.format(plugins_count))
        elapsed_time = self._run_action_concurrently(threads_count,
                                                     self._upload_plugin,
                                                     tenants)
        self.logger.info('Uploaded {0} plugins in {1:.2f} seconds'.
                         format(plugins_count, elapsed_time))
        self._assert_plugins_count(plugins_count + 1)

    def create_tenants(self, tenants_count, threads_count):
        self.logger.info('Creating {} tenants...'.format(tenants_count))
        tenants_names = ['tenant_{0}'.format(i) for i in range(tenants_count)]
        elapsed_time = self._run_action_concurrently(threads_count,
                                                     self._create_tenant,
                                                     tenants_names)
        self.logger.info('Created {0} tenants in {1:.2f} seconds'.format(
            tenants_count, elapsed_time))
        self._assert_tenants_count(tenants_count + 1)
        return tenants_names

    def delete_all_tenants(self, tenants, threads_count):
        self.logger.info('Deleting {0} tenants...'.format(len(tenants)))
        elapsed_time = self._run_action_concurrently(threads_count, self._delete_tenant, tenants)
        self.logger.info('Deleted {0} tenants in {1:.2f} seconds'
                         .format(len(tenants), elapsed_time))
        self._assert_tenants_count(1)

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
                                                 _all_tenants=True,
                                                 **PAGINATION_PARAMS)
        active_executions = [exe for exe in executions if exe.status != TERMINATED_STATE]
        assert len(active_executions) == 0
        self.logger.info('All the executions terminated successfully')

    def _create_deployment_in_tenant(self, tenant_name):
        client = CloudifyClient(host=self.manager.ip_address,
                                username='admin',
                                password='admin',
                                tenant=tenant_name)
        blueprint_id = self.upload_blueprint(client=client)
        self.create_deployment(blueprint_id, client)

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

    def _upload_plugin(self, tenant_name):
        # A small plugin for testing
        self.manager.upload_plugin('psutil_windows', tenant_name)

    def _create_tenant(self, tenant_name):
        self.client.tenants.create(tenant_name)

    def _delete_tenant(self, tenant_name):
        client = CloudifyClient(host=self.manager.ip_address,
                                username='admin',
                                password='admin',
                                tenant=tenant_name)
        self._delete_tenant_resources(client)
        self.client.tenants.delete(tenant_name)

    def _delete_tenant_resources(self, client):
        deployments = client.deployments.list()
        for deployment in deployments:
            client.deployments.delete(deployment.id)
            client.blueprints.delete(deployment.blueprint_id)

        plugins = client.plugins.list()
        for plugin in plugins:
            client.plugins.delete(plugin.id)

    def _assert_deployments_count(self, expected_count):
        assert self.deployments.metadata.pagination.total == expected_count

    def _assert_blueprints_count(self, expected_count):
        self._assert_resources_count(
            self.client.blueprints, 'Blueprints', expected_count, all_tenants=True)

    def _assert_tenants_count(self, expected_count):
        self._assert_resources_count(self.client.tenants, 'Tenants', expected_count)

    def _assert_plugins_count(self, expected_count):
        self._assert_resources_count(
            self.client.plugins, 'Plugins', expected_count, all_tenants=True)

    def _assert_resources_count(
            self, resource_client, resource_name, expected_count, all_tenants=False):
        resource_list = get_resource_list(
            resource_client, resource_name, self.logger, all_tenants=all_tenants)
        assert resource_list.metadata.pagination.total == expected_count

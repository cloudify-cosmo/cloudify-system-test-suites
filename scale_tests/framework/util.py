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
from constants import PAGINATION_PARAMS


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

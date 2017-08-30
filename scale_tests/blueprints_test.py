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

from framework.util import check_disk_space


def test_many_blueprints_uploads(manager, resource_creator, request, logger):
    """
    Test many blueprints uploads
    """
    start_time = time()
    threads_count = 50
    blueprints_count = int(request.config.getoption('--blueprints-count'))
    check_disk_space(manager, logger)
    resource_creator.upload_blueprints(blueprints_count, threads_count)
    check_disk_space(manager, logger)
    end_time = time()
    logger.info('{0} took {1:.2f} seconds'.format('test_many_blueprints_uploads',
                                                  end_time - start_time))

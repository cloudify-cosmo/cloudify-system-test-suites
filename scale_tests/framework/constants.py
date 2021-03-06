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

MONITORING_BLUEPRINT = 'monitoring'
NO_MONITORING_BLUEPRINT = 'no-monitoring'
AGENTLESS_BLUEPRINT = 'agentless'
BLUEPRINT_TYPES = [
    MONITORING_BLUEPRINT,
    NO_MONITORING_BLUEPRINT,
    AGENTLESS_BLUEPRINT
]

TERMINATED_STATE = 'terminated'

PAGINATION_PARAMS = {'_offset': 0, '_size': 1000}

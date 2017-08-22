########
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
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

import os
import yaml


class BlueprintExample(object):

    def __init__(self, attributes):
        self._inputs = None
        self._blueprint_path = None
        self._inputs_path = None
        self.blueprint_path = attributes.blueprint_path
        self.inputs_path = attributes.inputs_path
        self.attributes = attributes

    @property
    def blueprint_path(self):
        return self._blueprint_path

    @blueprint_path.setter
    def blueprint_path(self, value):
        self._blueprint_path = self._get_path(value)

    @property
    def inputs_path(self):
        return self._inputs_path

    @inputs_path.setter
    def inputs_path(self, value):
        self._inputs_path = self._get_path(value)

    @property
    def inputs(self):
        # Adding necessary inputs for openstack's blueprint
        if not self._inputs and os.path.isfile(self.inputs_path):
            with open(self.inputs_path) as inputs_file:
                self._inputs = yaml.load(inputs_file.read())
                self._inputs.update({
                    'floating_network_id': self.attributes.floating_network_id,
                    'key_pair_name': self.attributes.keypair_name,
                    'network_name': self.attributes.network_name,
                    'private_key_path': self.attributes.remote_private_key_path
                })

        return self._inputs

    @inputs.setter
    def inputs(self, blueprint_inputs):
        self._inputs = blueprint_inputs

    def _get_path(self, path):
        # Going up the directories to scale_tests because the path is relative
        # to resources directory
        dir_name = os.path.dirname(os.path.dirname(__file__))
        file_path = os.path.join(dir_name, 'resources', path)

        if os.path.isfile(file_path):
            return file_path
        else:
            raise ValueError('{} is not a valid file'.format(file_path))

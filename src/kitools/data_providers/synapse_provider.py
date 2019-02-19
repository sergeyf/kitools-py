# Copyright 2018-present, Bill & Melinda Gates Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .base_provider import BaseProvider


class SynapseProvider(BaseProvider):
    def name(self):
        return 'Synapse'

    def login(self, username, password, **kwargs):
        pass

    def create_project(self, name, **kwargs):
        pass

    def get_project(self, remote_uri):
        pass

    def data_pull(self, remote_uri, local_path, version=None, get_latest=True):
        pass

    def data_push(self, local_path):
        pass

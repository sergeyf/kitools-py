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

import pytest
import os
import tempfile
import shutil
import json
from src.kitools import Project, ProjectFile
from tests.synapse_test_helper import SynapseTestHelper

# Load Environment variables.
module_dir = os.path.dirname(os.path.abspath(__file__))

test_env_file = os.path.join(module_dir, 'private.test.env.json')

if os.path.isfile(test_env_file):
    with open(test_env_file) as f:
        config = json.load(f).get('test')

        # Validate required properties are present
        for prop in ['SYNAPSE_USERNAME', 'SYNAPSE_PASSWORD']:
            if prop not in config or not config[prop]:
                raise Exception('Property: "{0}" is missing in {1}'.format(prop, test_env_file))

        for key, value in config.items():
            os.environ[key] = value
else:
    print('WARNING: Test environment file not found at: {0}'.format(test_env_file))


@pytest.fixture(scope='session')
def syn_test_helper():
    helper = SynapseTestHelper()
    yield helper
    helper.dispose()


@pytest.fixture(scope='session')
def syn_client(syn_test_helper):
    return syn_test_helper.client()


@pytest.fixture(scope='session')
def syn_project(syn_test_helper):
    return syn_test_helper.create_project()


@pytest.fixture(scope='session')
def temp_file(syn_test_helper):
    fd, tmp_filename = tempfile.mkstemp()
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(syn_test_helper.uniq_name())
    yield tmp_filename

    if os.path.isfile(tmp_filename):
        os.remove(tmp_filename)


@pytest.fixture()
def new_temp_dir():
    path = tempfile.mkdtemp()
    yield path
    if os.path.isdir(path):
        shutil.rmtree(path)


@pytest.fixture()
def new_test_project(new_temp_dir):
    """
    Provides a test Project with one ProjectFile.
    :param temp_dir:
    :return: Project
    """
    project = Project(new_temp_dir)
    project.title = 'My Project Title'
    project.description = 'My Project Description'
    project.project_uri = 'syn:syn001'
    project.files.append(
        ProjectFile(remote_uri='syn:syn002',
                    local_path=os.path.join('data', 'core', 'file1.csv'),
                    version='1.2'
                    )
    )
    project.save()

    return project

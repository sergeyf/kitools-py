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
from src.kitools import ProjectFile


def test___init__():
    test_remote_uri = 'syn:syn123'
    test_path = '/tmp/test.csv'
    test_version = '1.2'
    project_file = ProjectFile(remote_uri=test_remote_uri, local_path=test_path, version=test_version)

    assert project_file.remote_uri == test_remote_uri
    assert project_file.local_path == test_path
    assert project_file.version == test_version

    # Ensure version is a string
    assert ProjectFile(version=None).version is None
    assert ProjectFile(version=1).version == '1'
    assert ProjectFile(version='').version is None


def test_to_absolute_path():
    rel_path = os.path.join('one', 'two', 'three')
    project_file = ProjectFile(local_path=rel_path)
    root_path = os.path.join('/', 'tmp', 'project')

    abs_path = project_file.to_absolute_path(root_path)
    assert abs_path == os.path.join(root_path, rel_path)

def test_to_relative_path():
    root_path = os.path.join('/', 'tmp', 'project')
    expected_rel_path = os.path.join('one', 'two', 'three')
    child_path = os.path.join(root_path, expected_rel_path)

    rel_path = ProjectFile.to_relative_path(child_path, root_path)
    assert rel_path == expected_rel_path
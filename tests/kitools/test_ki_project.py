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
import pytest
import os
import json as JSON
import uuid
import shutil
import synapseclient
from src.kitools import KiProject, KiProjectResource, DataType, DataUri


@pytest.fixture(scope='session')
def mk_syn_files(syn_test_helper, write_file, mk_tempdir):
    def _mk(syn_parent, file_num=2, versions=2, suffix=''):
        syn_files = []

        temp_dir = mk_tempdir()

        for file_num in range(1, file_num + 1):
            # Create N versions of each file.
            syn_file = None

            temp_file = os.path.join(temp_dir, 'File{0}{1}'.format(file_num, suffix))

            for version_num in range(1, versions + 1):
                write_file(temp_file, 'version{0}'.format(version_num))

                syn_file = syn_test_helper.client().store(synapseclient.File(
                    path=temp_file,
                    parent=syn_parent,
                    name=os.path.basename(temp_file)))

            syn_files.append(syn_file)
        return syn_files

    yield _mk


@pytest.fixture(scope='session')
def mk_syn_folders(syn_test_helper):
    def _mk(syn_parent, count=2, suffix=''):
        syn_folders = []

        for folder_count in range(1, count + 1):
            syn_folder = syn_test_helper.client().store(
                synapseclient.Folder(name='Folder{0}{1}'.format(folder_count, suffix), parent=syn_parent))
            syn_folders.append(syn_folder)
        return syn_folders

    yield _mk


@pytest.fixture(scope='session')
def mk_syn_folders_files(mk_syn_files, mk_syn_folders):
    def _mk(syn_parent):
        root_files = mk_syn_files(syn_parent)
        root_folders = mk_syn_folders(syn_parent)

        for root_folder in root_folders:
            mk_syn_files(root_folder, suffix='_1')

            for level2_folder in mk_syn_folders(root_folder, suffix='_1'):
                mk_syn_files(level2_folder, suffix='_2')

        return syn_parent, root_folders, root_files

    yield _mk


@pytest.fixture(scope='session')
def syn_non_data(mk_syn_project, mk_syn_folders_files):
    """
    Creates this:

    file1
    file2
    folder1/
        file1_1
        file2_1
        Folder1_1/
            file1_2
            file2_2
        Folder2_1/
            file1_2
            file2_2
    folder2/
        file1_1
        file2_1
        Folder1_1/
            file1_2
            file2_2
        Folder2_1/
            file1_2
            file2_2
    """
    syn_project = mk_syn_project()
    return mk_syn_folders_files(syn_project)


@pytest.fixture(scope='session')
def syn_data(mk_syn_project, syn_test_helper, mk_syn_folders_files):
    """
    Creates this:

    data
        /core
            file1
            file2
            folder1/
                file1_1
                file2_1
                Folder1_1/
                    file1_2
                    file2_2
                Folder2_1/
                    file1_2
                    file2_2
            folder2/
                file1_1
                file2_1
                Folder1_1/
                    file1_2
                    file2_2
                Folder2_1/
                    file1_2
                    file2_2
        /derived
            <same as core...>
        /discovered
            <same as core...>

    This method will return the root files/folders under data/core, data/derived, data/discovered.
    The data and data_type folders are NOT returned.
    """
    syn_project = mk_syn_project()
    root_folders = []
    root_files = []

    syn_data_folder = syn_test_helper.client().store(synapseclient.Folder(name='data', parent=syn_project))

    for data_type_name in DataType.ALL:
        syn_folder = syn_test_helper.client().store(synapseclient.Folder(name=data_type_name, parent=syn_data_folder))
        folder, folders, files = mk_syn_folders_files(syn_folder)
        root_folders += folders
        root_files += files

    return syn_project, root_folders, root_files


@pytest.fixture(scope='session')
def mk_local_data_dir(mk_uniq_string, write_file):
    def _mk(kiproject):
        all_data_paths = []

        for data_type_name in DataType.ALL:
            all_data_paths.append(kiproject.data_type_to_project_path(data_type_name))

        # Create some local data files.
        local_data_files = []
        for data_path in all_data_paths:
            filename = '{0}_file_{1}.csv'.format(os.path.basename(data_path), mk_uniq_string())
            file_path = os.path.join(data_path, filename)
            write_file(file_path, 'version1')
            local_data_files.append(file_path)

        # Create some local data folders.
        local_data_folders = []
        for data_path in all_data_paths:
            folder_name = '{0}_folder_{1}'.format(os.path.basename(data_path), mk_uniq_string())
            folder_path = os.path.join(data_path, folder_name)
            os.makedirs(folder_path)
            local_data_folders.append(folder_path)

            # Create some files in the folder
            for count in range(1, 4):
                filename = 'file_{0}.csv'.format(mk_uniq_string())
                file_path = os.path.join(folder_path, filename)
                write_file(file_path, 'version1')

        return local_data_folders, local_data_files

    yield _mk


def assert_matches_project(kiprojectA, kiprojectB):
    """
    Asserts that two Projects match each other.
    """
    assert kiprojectA.local_path == kiprojectB.local_path
    assert kiprojectA._config_path == kiprojectB._config_path
    assert kiprojectA.title == kiprojectB.title
    assert kiprojectA.description == kiprojectB.description
    assert kiprojectA.project_uri == kiprojectB.project_uri

    assert len(kiprojectA.resources) == len(kiprojectB.resources)

    for fileA in kiprojectA.resources:
        fileB = next((b for b in kiprojectB.resources if
                      b.remote_uri == fileA.remote_uri and
                      b.rel_path == fileA.rel_path and
                      b.version == fileA.version), None)
        assert fileB


def assert_matches_config(kiproject):
    """
    Asserts that a KiProject's config matches the KiProject.
    """
    json = None
    with open(kiproject._config_path) as f:
        json = JSON.load(f)

    assert json.get('title', None) == kiproject.title
    assert json.get('description', None) == kiproject.description
    assert json.get('project_uri', None) == kiproject.project_uri

    for jfile in json.get('resources'):
        file = next((f for f in kiproject.resources if
                     f.remote_uri == jfile['remote_uri'] and
                     f.rel_path == jfile['rel_path'] and
                     f.version == jfile['version']), None)
        assert file


def assert_data_type_paths(kiproject, exists=True):
    """
    Asserts that all the data_type directories exist or not.
    :param exists:
    :return:
    """
    for data_type_name in DataType.ALL:
        assert os.path.isdir(kiproject.data_type_to_project_path(data_type_name)) is exists


@pytest.fixture()
def kiproject(mk_kiproject):
    return mk_kiproject()


def test_it_sets_the_kiproject_paths(mk_kiproject, mk_tempdir):
    temp_dir = mk_tempdir()
    kiproject = mk_kiproject(dir=temp_dir)
    assert kiproject.local_path == temp_dir
    assert kiproject.data_path == os.path.join(temp_dir, DataType.DATA_DIR_NAME)
    assert kiproject._config_path == os.path.join(temp_dir, KiProject.CONFIG_FILENAME)


def test_it_expands_user_dir_in_local_path():
    # TODO: test this.
    pass


def test_it_expands_vars_in_local_path():
    # TODO: test this.
    pass


def test_it_creates_a_config_file_from_the_constructor(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)

    # Delete the config file
    os.remove(kiproject._config_path)
    assert os.path.exists(kiproject._config_path) is False

    new_project = KiProject(kiproject.local_path)

    assert os.path.isfile(new_project._config_path)
    assert_matches_config(new_project)


def test_it_loads_the_config_file_from_the_constructor(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)
    other_project = KiProject(kiproject.local_path)
    assert_matches_config(other_project)
    assert_matches_project(other_project, kiproject)


def test_it_loads_the_config_file(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)

    other_project = KiProject(kiproject.local_path)
    other_project.title = None
    other_project.description = None
    other_project.project_uri = None
    other_project.resources.clear()

    other_project.load()
    assert_matches_project(other_project, kiproject)


def test_it_loads_the_config_file_when_it_exists(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)
    assert os.path.isfile(kiproject._config_path)
    assert kiproject.load() is True


def test_it_does_not_load_the_config_file_when_it_does_not_exist(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)
    os.remove(kiproject._config_path)
    assert os.path.isfile(kiproject._config_path) is False
    assert kiproject.load() is False


def test_it_creates_a_config_file_when_saved(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)

    # Delete the config file
    os.remove(kiproject._config_path)
    assert os.path.exists(kiproject._config_path) is False

    # Save a new config file
    kiproject.save()

    assert os.path.isfile(kiproject._config_path)
    assert_matches_config(kiproject)


def test_it_updates_the_config_file_when_saved(mk_kiproject, mk_fake_uri, mk_fake_project_file):
    kiproject = mk_kiproject(with_fake_project_files=True)
    kiproject.title = str(uuid.uuid4())
    kiproject.description = str(uuid.uuid4())
    kiproject.project_uri = mk_fake_uri()
    kiproject.resources.append(mk_fake_project_file(kiproject))

    kiproject.save()
    assert_matches_config(kiproject)


def test_it_creates_the_project_dir_structure_on_a_new_project(kiproject):
    assert_data_type_paths(kiproject, exists=True)


def test_it_recreates_the_project_dir_structure_on_an_existing_project(mk_kiproject):
    kiproject = mk_kiproject()
    shutil.rmtree(os.path.join(kiproject.local_path, 'data'))
    assert_data_type_paths(kiproject, exists=False)

    # Reload the kiproject
    kiproject = KiProject(kiproject.local_path)
    assert_data_type_paths(kiproject, exists=True)


def test_find_project_file_by(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True, with_fake_project_files_count=3)

    props = ['id', 'root_id', 'remote_uri', 'abs_path', 'rel_path', 'name', 'version', 'data_type']
    uniq_props = ['id', 'remote_uri', 'abs_path', 'rel_path']

    for ki_project_resource in kiproject.resources:
        all_args = {}
        for prop in props:
            value = getattr(ki_project_resource, prop)
            if value:
                all_args[prop] = value

        # Finds by all properties
        found = kiproject.find_project_resource_by(**all_args)
        assert found == ki_project_resource

        # Find by each unique property individually.
        for prop, value in all_args.items():
            if prop not in uniq_props:
                continue

            single_arg = {
                prop: value
            }
            found = kiproject.find_project_resource_by(**single_arg)
            assert found == ki_project_resource

    # TODO: test "and"/"or" operator.


def test_it_prints_out_the_root_project_resources(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True, with_fake_project_files_count=3)
    table = kiproject.data_list()

    index = 0
    for resource in kiproject.resources:
        row = table[index]
        assert row[0] == resource.remote_uri
        assert row[1] == resource.version
        assert row[2] == resource.name
        assert row[3] == resource.rel_path
        index += 1


def test_it_creates_a_new_remote_project(mk_mock_kiproject_input, mk_tempdir, syn_test_helper):
    mk_mock_kiproject_input(create_remote_project_or_existing='c')
    kiproject = KiProject(mk_tempdir())

    syn_project = syn_test_helper.client().get(DataUri.parse(kiproject.project_uri).id)
    syn_test_helper.dispose_of(syn_project)


def test_it_adds_a_remote_data_structure_file(mk_kiproject, syn_data):
    kiproject = mk_kiproject()
    syn_project, syn_folders, syn_files = syn_data

    for syn_file in syn_files:
        syn_file_uri = DataUri('syn', syn_file.id).uri
        ki_project_resource = kiproject.data_add(syn_file_uri)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_adds_a_remote_data_structure_folder(mk_kiproject, syn_data):
    kiproject = mk_kiproject()
    syn_project, syn_folders, syn_files = syn_data

    for syn_folder in syn_folders:
        ki_project_resource = kiproject.data_add(DataUri('syn', syn_folder.id).uri)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_adds_a_remote_non_data_structure_file(mk_kiproject, syn_non_data):
    kiproject = mk_kiproject()
    syn_parent, syn_folders, syn_files = syn_non_data

    for syn_file in syn_files:
        syn_file_uri = DataUri('syn', syn_file.id).uri
        ki_project_resource = kiproject.data_add(syn_file_uri, data_type=DataType.CORE)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_adds_a_remote_non_data_structure_folder(mk_kiproject, syn_non_data):
    kiproject = mk_kiproject()
    syn_parent, syn_folders, syn_files = syn_non_data

    for syn_folder in syn_folders:
        ki_project_resource = kiproject.data_add(DataUri('syn', syn_folder.id).uri, data_type=DataType.CORE)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_adds_a_local_data_structure_file(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for file_path in local_data_files:
        ki_project_resource = kiproject.data_add(file_path)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_adds_a_local_data_structure_folder(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for folder_path in local_data_folders:
        ki_project_resource = kiproject.data_add(folder_path)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_pulls_a_file_matching_the_data_structure(mk_kiproject, syn_data):
    kiproject = mk_kiproject()
    syn_project, syn_folders, syn_files = syn_data

    for syn_file in syn_files:
        syn_file_uri = DataUri('syn', syn_file.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_file_uri)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity


def test_it_pulls_a_folder_matching_the_data_structure(mk_kiproject, syn_data):
    kiproject = mk_kiproject()
    syn_project, syn_folders, syn_files = syn_data

    for syn_folder in syn_folders:
        if syn_folder.name == 'data' or syn_folder.name == 'core':
            continue

        syn_folder_uri = DataUri('syn', syn_folder.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_folder_uri)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity
        # TODO: check that file/folders exist locally


def test_it_pulls_a_file_not_matching_the_data_structure(mk_kiproject, syn_non_data):
    kiproject = mk_kiproject()
    syn_parent, syn_folders, syn_files = syn_non_data

    for syn_file in syn_files:
        syn_file_uri = DataUri('syn', syn_file.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_file_uri, data_type=DataType.CORE)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity
        # TODO: check that file/folders exist locally


def test_it_pulls_a_folder_not_matching_the_data_structure(mk_kiproject, syn_non_data):
    kiproject = mk_kiproject()
    syn_parent, syn_folders, syn_files = syn_non_data

    for syn_folder in syn_folders:
        syn_folder_uri = DataUri('syn', syn_folder.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_folder_uri, data_type=DataType.CORE)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity
        # TODO: check that file/folders exist locally


def test_it_does_not_pull_a_file_unless_the_remote_file_changed_TODO():
    raise NotImplementedError()


def test_it_pushes_a_file_matching_the_data_structure(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for file_path in local_data_files:
        ki_project_resource = kiproject.data_add(file_path)

        # Push the file
        remote_entity = kiproject.data_push(ki_project_resource.name)
        assert remote_entity
        # TODO: check that file/folders were pushed


def test_it_pushes_a_folder_matching_the_data_structure(mk_kiproject, mk_uniq_string, write_file, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for folder_path in local_data_folders:
        ki_project_resource = kiproject.data_add(os.path.dirname(folder_path))

        # Push the file
        remote_entity = kiproject.data_push(ki_project_resource.name)
        assert remote_entity
        # TODO: check that file/folders were pushed


def test_it_does_not_push_a_file_unless_the_local_file_changed_TODO():
    raise NotImplementedError()


def test_it_tests_the_workflow(mk_kiproject,
                               mk_local_data_dir,
                               syn_data,
                               syn_non_data):
    kiproject = mk_kiproject()
    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    ###########################################################################
    # Add/Push Local Files and Folders
    ###########################################################################

    # Files
    for local_file in local_data_files:
        resource = kiproject.data_add(local_file)
        abs_path = kiproject.data_push(resource)
        assert abs_path == resource.abs_path

    # Folders
    for local_folder in local_data_folders:
        resource = kiproject.data_add(local_folder)
        abs_path = kiproject.data_push(resource)
        assert abs_path == resource.abs_path

    ###########################################################################
    # Add/Pull Remote Data Files and Folders
    ###########################################################################
    _, syn_data_folders, syn_data_files = syn_data

    # Files
    for syn_file in syn_data_files:
        remote_uri = DataUri('syn', syn_file.id).uri
        resource = kiproject.data_add(remote_uri)
        abs_path = kiproject.data_pull(remote_uri)
        # Lock the version
        resource = kiproject.data_change(remote_uri, version='2')
        assert resource.version == '2'
        abs_path = kiproject.data_pull(remote_uri)

    # Folders
    for syn_folder in syn_data_folders:
        remote_uri = DataUri('syn', syn_folder.id).uri
        resource = kiproject.data_add(remote_uri)
        abs_path = kiproject.data_pull(remote_uri)

    ###########################################################################
    # Add/Pull Remote non-Data Files and Folders
    ###########################################################################
    _, syn_non_data_folders, syn_non_data_files = syn_non_data

    # Files
    for syn_non_data_file in syn_non_data_files:
        remote_uri = DataUri('syn', syn_non_data_file.id).uri
        resource = kiproject.data_add(remote_uri, data_type=DataType.CORE)
        abs_path = kiproject.data_pull(remote_uri)

    # Folders
    for syn_non_data_folder in syn_non_data_folders:
        remote_uri = DataUri('syn', syn_non_data_folder.id).uri
        resource = kiproject.data_add(remote_uri, data_type=DataType.CORE)
        abs_path = kiproject.data_pull(remote_uri)

    ###########################################################################
    # data_list
    ###########################################################################
    kiproject.data_list()
    kiproject.data_list(all=True)

    ###########################################################################
    # data_remove
    ###########################################################################
    for resource in kiproject.resources.copy():
        if resource.root_id:
            continue
        kiproject.data_remove(resource.remote_uri or resource.abs_path)

    assert len(kiproject.resources) == 0

    assert True


def test_it_removes_resources(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)

    for resource in kiproject.resources.copy():
        if resource.root_id:
            continue

        kiproject.data_remove(resource.remote_uri or resource.abs_path)

    assert len(kiproject.resources) == 0


def test_data_type_to_project_path(kiproject):
    for data_type in DataType.ALL:
        assert kiproject.data_type_to_project_path(data_type) == os.path.join(kiproject.data_path, data_type)


def test_data_type_from_project_path(kiproject):
    for data_type_name in DataType.ALL:
        path = kiproject.data_type_to_project_path(data_type_name)
        assert kiproject.data_type_from_project_path(path).name == data_type_name

        other_paths = []
        for other_path in ['one', 'two', 'three', 'file.csv']:
            other_paths.append(other_path)
            new_path = os.path.join(path, *other_paths)
            assert kiproject.data_type_from_project_path(new_path).name == data_type_name


def test_is_project_data_path(kiproject, mk_tempdir):
    temp_dir = mk_tempdir()

    assert kiproject.is_project_data_path(temp_dir) is False
    # TODO: add more tests

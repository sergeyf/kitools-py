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

import os


class ProjectTemplate:

    def __init__(self, path):
        self.path = path

    def write(self):
        self.create_dirs()
        self.create_gitignore()

    def create_dirs(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        for dirname in ProjectTemplate.project_dir_names():
            full_path = os.path.join(self.path, dirname)
            if not os.path.exists(full_path):
                os.mkdir(full_path)

    def create_gitignore(self):
        pass

    @staticmethod
    def project_dir_names():
        return [
            'data',
            'data{0}core'.format(os.sep),
            'data{0}derived'.format(os.sep),
            'data{0}discovered'.format(os.sep),
            'data{0}discovered{0}_raw'.format(os.sep),
            'data{0}scripts'.format(os.sep),
            'data{0}scripts{0}_raw'.format(os.sep),
            'data{0}reports'.format(os.sep)]

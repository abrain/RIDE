#  Copyright 2008-2011 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import unittest
import datafilereader


class TestParents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        chief = datafilereader.construct_chief_controller(datafilereader.OCCURRENCES_PATH)
        cls.directory = chief.data
        cls.test = datafilereader.get_ctrl_by_name('TestSuite1', chief.datafiles)
        cls.resource = datafilereader.get_ctrl_by_name(datafilereader.OCCURRENCES_RESOURCE_NAME, chief.datafiles)
        cls.external_resource = datafilereader.get_ctrl_by_name('Resu', chief.datafiles)

    def test_test_suite_parent_is_directory(self):
        self.assertEquals(self.test.parent, self.directory)
        self.assertTrue(self.test in self.directory.children)

    def test_local_resource_parent_is_directory(self):
        self.assertEquals(self.resource.parent, self.directory)
        self.assertTrue(self.resource in self.directory.children)

    def test_external_resource_parent_is_undefined(self):
        self.assertEquals(self.external_resource.parent, None)
        self.assertTrue(self.external_resource not in self.directory.children)

if __name__ == '__main__':
    unittest.main()

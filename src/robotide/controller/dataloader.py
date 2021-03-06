#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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

import os
from threading import Thread

from robot.parsing.model import TestData, TestDataDirectory
from robot.parsing.populators import FromFilePopulator


class DataLoader(object):

    def __init__(self, namespace):
        self._namespace = namespace
        self._namespace.reset_resource_and_library_cache()

    def load_datafile(self, path, load_observer):
        return self._load(_DataLoader(path), load_observer)

    def load_initfile(self, path, load_observer):
        res = self._load(_InitFileLoader(path), load_observer)
        return res

    def resources_for(self, datafile, load_observer):
        return self._load(_ResourceLoader(datafile, self._namespace.get_resources),
                          load_observer)

    def _load(self, loader, load_observer):
        self._wait_until_loaded(loader, load_observer)
        return loader.result

    def _wait_until_loaded(self, loader, load_observer):
        loader.start()
        load_observer.notify()
        while loader.isAlive():
            loader.join(0.1)
            load_observer.notify()


class _DataLoaderThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.result = None

    def run(self):
        try:
            self.result = self._run()
        except Exception:
            pass # TODO: Log this error somehow


class _DataLoader(_DataLoaderThread):

    def __init__(self, path):
        _DataLoaderThread.__init__(self)
        self._path = path

    def _run(self):
        return TestData(source=self._path)


class _InitFileLoader(_DataLoaderThread):

    def __init__(self, path):
        _DataLoaderThread.__init__(self)
        self._path = path

    def _run(self):
        result = TestDataDirectory(source=os.path.dirname(self._path))
        result.initfile = self._path
        FromFilePopulator(result).populate(self._path)
        return result


class _ResourceLoader(_DataLoaderThread):

    def __init__(self, datafile, resource_loader):
        _DataLoaderThread.__init__(self)
        self._datafile = datafile
        self._loader = resource_loader

    def _run(self):
        return self._loader(self._datafile)

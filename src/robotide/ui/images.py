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
import wx
from robot.parsing.model import Variable
from robotide.controller.settingcontrollers import VariableController
from robotide.controller.macrocontrollers import TestCaseController, UserKeywordController
from robotide.controller.filecontrollers import TestDataDirectoryController, TestCaseFileController, ResourceFileController, DirectoryController


_SIZE = (16, 16)
_BASE = os.path.join(os.path.dirname(__file__), '..', 'widgets')


class TreeImageList(wx.ImageList):

    def __init__(self):
        wx.ImageList.__init__(self, *_SIZE)
        self._images = {
            TestDataDirectoryController: _TreeImage(self, 'folder.png'),
            DirectoryController: _TreeImage(self, 'folder_wrench.png'),
            TestCaseFileController: _TreeImage(self, 'page_white.png'),
            TestCaseController: _TreeImage(self, 'robot.png'),
            UserKeywordController: _TreeImage(self, 'cog.png'),
            ResourceFileController: _TreeImage(self, 'page_white_gear.png'),
            VariableController: _TreeImage(self, 'dollar.png')
        }

    @property
    def directory(self):
        return self._images[DirectoryController]

    def __getitem__(self, controller):
        return self._images[controller.__class__]


class _TreeImage(object):

    def __init__(self, image_list, normal, expanded=None):
        self.normal = self._get_image(image_list, normal)
        self.expanded = self._get_image(image_list, expanded) if expanded else self.normal

    def _get_image(self, image_list, source):
        if source.startswith('wx'):
            img = wx.ArtProvider_GetBitmap(source, wx.ART_OTHER, _SIZE)
        else:
            path = os.path.join(_BASE, source)
            img = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        return image_list.Add(img)

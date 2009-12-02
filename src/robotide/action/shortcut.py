#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

import wx


class Shortcut(object):

    def __init__(self, shortcut):
        self.value = self._normalize(shortcut)
        self._shortcut = shortcut

    def __nonzero__(self):
        return bool(self._shortcut)

    def _normalize(self, shortcut):
        if not shortcut:
            return None
        order = ['Shift', 'Ctrl', 'Alt']
        keys = [ self._normalize_key(key) for key in self._split(shortcut) ]
        keys.sort(key=lambda t: t in order and order.index(t) or 42)
        return '-'.join(keys)

    def parse(self):
        keys = self._split(self._shortcut)
        if len(keys) == 1:
            flags = wx.ACCEL_NORMAL
        else:
            flags = sum(self._get_wx_key_constant('ACCEL', key)
                        for key in keys[:-1])
        return flags, self._get_key(keys[-1])

    def _normalize_key(self, key):
        key = key.title()
        return {'Del': 'Delete', 'Ins': 'Insert',
                'Enter': 'Return', 'Esc':'Escape'}.get(key, key)

    def _split(self, shortcut):
        return shortcut.replace('+', '-').split('-')

    def _get_wx_key_constant(self, prefix, name):
        attr = '%s_%s' % (prefix, name.upper().replace(' ', ''))
        try:
            return getattr(wx, attr)
        except AttributeError:
            raise ValueError('Invalid shortcut key: %s' % name)

    def _get_key(self, key):
        if len(key) == 1:
            return ord(key.upper())
        return self._get_wx_key_constant('WXK', self._normalize_key(key))
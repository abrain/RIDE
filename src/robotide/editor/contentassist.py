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

import wx
from wx.lib.expando import ExpandoTextCtrl
from robot.utils.normalizing import normalize

from robotide import context

from popupwindow import RidePopupWindow, Tooltip


_PREFERRED_POPUP_SIZE = (400, 200)


class _ContentAssistTextCtrlBase(object):

    def __init__(self, plugin, controller=None):
        self._popup = ContentAssistPopup(self, plugin, controller=controller)
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnFocusLost)
        self.Bind(wx.EVT_MOVE, self.OnFocusLost)
        self._showing_content_assist = False
        self._row = None

    def set_row(self, row):
        self._row = row

    def OnChar(self, event):
        # TODO: This might benefit from some cleanup
        keycode = event.GetKeyCode()
        # Ctrl-Space handling needed for dialogs
        if keycode == wx.WXK_SPACE and event.ControlDown():
            self.show_content_assist()
            return
        if keycode in [wx.WXK_UP, wx.WXK_DOWN, wx.WXK_PAGEUP, wx.WXK_PAGEDOWN] \
                and self._popup.is_shown():
            self._popup.select_and_scroll(keycode)
            return
        elif keycode == wx.WXK_RETURN and self._popup.is_shown():
            self.OnFocusLost(event)
            return
        elif keycode == wx.WXK_TAB:
            self.OnFocusLost(event, False)
        elif keycode == wx.WXK_ESCAPE and self._popup.is_shown():
            self._popup.hide()
            return
        elif self._popup.is_shown() and keycode < 256:
            self._populate_content_assist(event)
        event.Skip()

    def OnFocusLost(self, event, set_value=True):
        if not self._popup.is_shown():
            return
        value = self._popup.get_value()
        if set_value and value:
            self.SetValue(value)
            self.SetInsertionPoint(len(self.Value))
        else:
            self.Clear()
        self.hide()

    def reset(self):
        self._popup.reset()
        self._showing_content_assist = False

    def show_content_assist(self):
        if self._showing_content_assist:
            return
        self._showing_content_assist = True
        if self._populate_content_assist():
            self._show_content_assist()

    def _populate_content_assist(self, event=None):
        value = self.GetValue()
        if event is not None:
            if event.GetKeyCode() == wx.WXK_BACK:
                value = value[:-1]
            elif event.GetKeyCode() == wx.WXK_DELETE:
                pos = self.GetInsertionPoint()
                value = value[:pos] + value[pos + 1:]
            elif event.GetKeyCode() == wx.WXK_ESCAPE:
                self.hide()
                return False
            else:
                value += unichr(event.GetRawKeyCode())
        return self._popup.content_assist_for(value, row=self._row)

    def _show_content_assist(self):
        height = self.GetSizeTuple()[1]
        x, y = self.ClientToScreenXY(0, 0)
        self._popup.show(x, y, height)

    def content_assist_value(self):
        return self._popup.content_assist_value(self.Value)

    def hide(self):
        self._popup.hide()
        self._showing_content_assist = False


class ExpandingContentAssistTextCtrl(_ContentAssistTextCtrlBase, ExpandoTextCtrl):

    def __init__(self, parent, plugin, controller):
        ExpandoTextCtrl.__init__(self, parent, size=wx.DefaultSize, style=wx.WANTS_CHARS)
        _ContentAssistTextCtrlBase.__init__(self, plugin, controller=controller)


class ContentAssistTextCtrl(_ContentAssistTextCtrlBase, wx.TextCtrl):

    def __init__(self, parent, plugin, size=wx.DefaultSize):
        wx.TextCtrl.__init__(self, parent, size=size, style=wx.WANTS_CHARS)
        _ContentAssistTextCtrlBase.__init__(self, plugin)

class Suggestions(object):

    def __init__(self, plugin, controller):
        self._plugin = plugin
        self._controller = controller
        self._previous_value = None
        self._previous_choices = []

    def get_for(self, value, row=None):
        self._previous_choices = self._get_choices(value, row)
        self._previous_value = value
        return [k for k,_ in self._previous_choices]

    def get_item(self, name):
        for k, v in self._previous_choices:
            if k == name:
                return v
        raise Exception('Item not in choices "%s"' % (name))

    def _get_choices(self, value, row):
        if self._previous_value and value.startswith(self._previous_value):
            return [(key, val) for key, val in self._previous_choices
                                    if normalize(key).startswith(normalize(value))]
        if self._controller and row:
            choices = self._controller.get_local_namespace_for_row(row).get_suggestions(value)
        else:
            choices = self._plugin.content_assist_values(value) # TODO: Remove old functionality when no more needed
        return self._format_choices(choices, value)

    def _format_choices(self, data, prefix):
        return [(self._format(val, prefix), val) for val in data]

    def _format(self, choice, prefix):
        return choice.name if normalize(choice.name).startswith(normalize(prefix)) else choice.longname


class ContentAssistPopup(object):

    def __init__(self, parent, plugin, controller=None):
        self._parent = parent
        self._plugin = plugin
        self._main_popup = RidePopupWindow(parent, _PREFERRED_POPUP_SIZE)
        self._details_popup = Tooltip(parent, _PREFERRED_POPUP_SIZE)
        self._selection = -1
        self._list = ContentAssistList(self._main_popup, self.OnListItemSelected,
                                       self.OnListItemActivated)
        self._suggestions = Suggestions(self._plugin, controller)

    def reset(self):
        self._selection = -1

    def get_value(self):
        return self._selection != -1 and self._list.get_text(self._selection) or None

    def content_assist_for(self, value, row=None):
        self._choices = self._suggestions.get_for(value, row=row)
        if not self._choices:
            self._list.ClearAll()
            self._parent.hide()
            return False
        self._list.populate(self._choices)
        return True

    def _starts(self, val1, val2):
        return val1.lower().startswith(val2.lower())

    def content_assist_value(self, value):
        if self._selection > -1:
            return self._list.GetItem(self._selection).GetText()
        return None

    def show(self, xcoord, ycoord, cell_height):
        self._main_popup.SetPosition((xcoord, self._move_y_where_room(ycoord, cell_height)))
        self._details_popup.SetPosition((self._move_x_where_room(xcoord),
                                         self._move_y_where_room(ycoord, cell_height)))
        self._main_popup.Show()
        self._list.SetFocus()

    def _move_x_where_room(self, start_x):
        width = _PREFERRED_POPUP_SIZE[0]
        max_horizontal = wx.GetDisplaySize()[0]
        free_right = max_horizontal - start_x - width
        free_left = start_x - width
        if max_horizontal - start_x < 2 * width:
            if free_left > free_right:
                return start_x - width
        return start_x + width

    def _move_y_where_room(self, start_y, cell_height):
        height = _PREFERRED_POPUP_SIZE[1]
        max_vertical = wx.GetDisplaySize()[1]
        if max_vertical - start_y - cell_height < height:
            return start_y - height
        return start_y + cell_height

    def is_shown(self):
        return self._main_popup.IsShown()

    def select_and_scroll(self, keycode):
        sel = self._list.GetFirstSelected()
        if keycode == wx.WXK_DOWN :
            if sel < (self._list.GetItemCount() - 1):
                self._select_and_scroll(sel + 1)
            else:
                self._select_and_scroll(0)
        elif keycode == wx.WXK_UP:
            if sel > 0 :
                self._select_and_scroll(sel - 1)
            else:
                self._select_and_scroll(self._list.GetItemCount() - 1)
        elif keycode == wx.WXK_PAGEDOWN:
            if self._list.ItemCount - self._selection > 14:
                self._select_and_scroll(self._selection + 14)
            else:
                self._select_and_scroll(self._list.ItemCount - 1)
        elif keycode == wx.WXK_PAGEUP:
            if self._selection > 14:
                self._select_and_scroll(self._selection - 14)
            else:
                self._select_and_scroll(0)

    def _select_and_scroll(self, selection):
        self._selection = selection
        self._list.Select(self._selection)
        self._list.EnsureVisible(self._selection)

    def hide(self):
        self._selection = -1
        self._main_popup.Show(False)
        self._details_popup.Show(False)

    def OnListItemActivated(self, event):
        self._parent.OnFocusLost(event)

    def OnListItemSelected(self, event):
        self._selection = event.GetIndex()
        item = self._suggestions.get_item(event.GetText())
        if item.details:
            self._details_popup.Show()
            self._details_popup.set_content(item.details, item.name)
        elif self._details_popup.IsShown():
            self._details_popup.Show(False)


class ContentAssistList(wx.ListCtrl):

    def __init__(self, parent, selection_callback, activation_callback=None):
        style = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER
        wx.ListCtrl.__init__(self, parent, style=style)
        self._selection_callback = selection_callback
        self._activation_callback = activation_callback
        self.SetSize(parent.GetSize())
        self.SetBackgroundColour(context.POPUP_BACKGROUND)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, selection_callback)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, activation_callback)

    def populate(self, data):
        self.ClearAll()
        self.InsertColumn(0, '', width=self.Size[0])
        for row, item in enumerate(data):
            self.InsertStringItem(row, item)
        self.Select(0)

    def get_text(self, index):
        return self.GetItem(index).GetText()

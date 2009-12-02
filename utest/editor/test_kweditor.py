import unittest

from robot.utils.asserts import assert_equals

from robotide.editor.kweditor import KeywordEditor, GRID_CLIPBOARD
from robotide.publish.messages import RideGridCellChanged
from robotide.publish import PUBLISHER
from resources import FakeSuite, PYAPP_REFERENCE #Needed to be able to create wx components
# wx needs to imported last so that robotide can select correct wx version.
import wx


DATA = [['kw1', '', ''],
        ['kw2', 'arg1', ''],
        ['kw3', 'arg1', 'arg2']]

class _FakeMainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)

class _FakeTree(object):
    mark_dirty = lambda self, datafile: None

class _KeywordList(list):
    def __init__(self):
        list.__init__(self)
        self.datafile = FakeSuite()
        for item in DATA:
            self.append(_KeywordData(item[0], [val for val in item[1:] if val]))

    def parse_keywords_from_grid(self, kwdata):
        list.__init__(self)
        for kw in kwdata:
            self.append(_KeywordData(kw[0], [val for val in kw[1:] if val]))

class _KeywordData(object):
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def get_display_value(self):
        return [self.name] + self.args


class TestCoordinates(unittest.TestCase):

    def setUp(self):
        self._editor = KeywordEditor(_FakeMainFrame(), _KeywordList(), None)

    def test_cell_selection(self):
        self._editor.SelectBlock(2,2,2,2)
        self._verify_selection(2,2,2,2)

    def test_selecting_multiple_cells(self):
        self._editor.SelectBlock(0,1,3,4)
        self._verify_selection(0,1,3,4)

    def _verify_selection(self, toprow, topcol, botrow, botcol):
        assert_equals(self._editor._active_coords.topleft.row, toprow)
        assert_equals(self._editor._active_coords.topleft.col, topcol)
        assert_equals(self._editor._active_coords.bottomright.row, botrow)
        assert_equals(self._editor._active_coords.bottomright.col, botcol)


class TestClipBoard(unittest.TestCase):

    def setUp(self):
        self._editor = KeywordEditor(_FakeMainFrame(), _KeywordList(), _FakeTree())

    def test_copy_one_cell(self):
        self._copy_block_and_verify((0,0,0,0), [[val for val in DATA[0] if val]])

    def test_copy_row(self):
        self._copy_block_and_verify((1,0,1,1), [[val for val in DATA[1] if val]])

    def test_copy_block(self):
        self._copy_block_and_verify((0,0,2,2), DATA)

    def _copy_block_and_verify(self, block, exp_content):
        self._editor.SelectBlock(*block)
        self._editor.OnCopy()
        assert_equals(GRID_CLIPBOARD.get_contents(), exp_content)
        self._verify_grid_content(DATA)

    def test_cut_one_cell(self):
        self._cut_block_and_verify((0,0,0,0), [[val for val in DATA[0] if val]],
                                   [['', '', '']] + DATA[1:])

    def test_cut_row(self):
        self._cut_block_and_verify((2,0,2,2), [DATA[2]], DATA[:2])

    def test_cut_block(self):
        self._cut_block_and_verify((0,0,2,2), DATA, [])

    def _cut_block_and_verify(self, block, exp_clipboard, exp_grid):
        self._cut_block(block)
        assert_equals(GRID_CLIPBOARD.get_contents(), exp_clipboard)
        self._verify_grid_content(exp_grid)

    def test_undo_with_cut(self):
        self._cut_undo_and_verify((0,0,0,0), DATA)
        self._cut_undo_and_verify((0,0,2,2), DATA)

    def test_multiple_levels_of_undo(self):
        self._cut_block((0,0,0,0))
        self._cut_block((2,0,2,2))
        self._editor.undo()
        self._verify_grid_content(DATA[1:])
        self._editor.undo()
        self._verify_grid_content(DATA)

    def _cut_undo_and_verify(self, block, exp_data_after_undo):
        self._cut_block(block)
        self._editor.undo()
        self._verify_grid_content(exp_data_after_undo)

    def _cut_block(self, block):
        self._editor.SelectBlock(*block)
        self._editor.OnCut()

    def test_paste_one_cell(self):
        self._copy_and_paste_block((1,0,1,0), (3,0,3,0), DATA + [['kw2']])
        # These tests are not independent
        self._copy_and_paste_block((1,0,1,0), (0,3,0,3),
                                   [DATA[0] + ['kw2']] + DATA[1:] + [['kw2']])

    def test_paste_row(self):
        self._copy_and_paste_block((2,0,2,2), (3,1,3,1), DATA + [[''] + DATA[2]])

    def test_paste_block(self):
        self._copy_and_paste_block((0,0,2,2), (4,0,4,0), DATA + [['']] + DATA)

    def test_paste_over(self):
        self._copy_and_paste_block((1,0,1,1), (0,0,0,0), [DATA[1]] + DATA[1:])

    def _copy_and_paste_block(self, sourceblock, targetblock, exp_content):
        self._editor.SelectBlock(*sourceblock)
        self._editor.OnCopy()
        self._editor.SelectBlock(*targetblock)
        self._editor.OnPaste()
        self._verify_grid_content(exp_content)

    def _verify_grid_content(self, data):
        for row in range(self._editor.GetNumberRows()):
            for col in range(self._editor.GetNumberCols()):
                value = self._editor.GetCellValue(row, col)
                try:
                    assert_equals(value, data[row][col],
                                  'The contents of cell (%d,%d) was not as '
                                  'expected' % (row, col))
                except IndexError:
                    assert_equals(value, '')

    def test_simple_undo(self):
        self._editor.SelectBlock(*(0,0,0,0))
        self._editor.OnCut()
        self._editor.undo()
        self._verify_grid_content(DATA)


class TestEditing(unittest.TestCase):

    def setUp(self):
        self._editor = KeywordEditor(_FakeMainFrame(), _KeywordList(), None)
        PUBLISHER.subscribe(self._on_cell_changed, RideGridCellChanged)#('core', 'grid', 'cell changed')

    def test_correct_event_is_published_during_population(self):
        self._editor.write_cell('Hello', 0, 0)
        assert_equals(self._data.cell, (0,0))
        assert_equals(self._data.value, 'Hello')
        assert_equals(self._data.previous, 'kw1')
        assert_equals(self._data.grid, self._editor)

    def test_correct_event_is_published_when_editing(self):
        self._editor.SetCellValue(2, 3, 'Robot rulez!')
        assert_equals(self._data.cell, (2,3))
        assert_equals(self._data.value, 'Robot rulez!')
        assert_equals(self._data.previous, '')
        assert_equals(self._data.grid, self._editor)

    def _on_cell_changed(self, message):
        self._data = message


if __name__ == '__main__':
    unittest.main()
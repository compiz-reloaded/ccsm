#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors: Quinn Storm (quinn@beryl-project.org)
#          Patrick Niklaus (marex@opencompositing.org)
# Copyright (C) 2007 Quinn Storm

import pygtk
import gtk
import gobject
import os
import mimetypes
mimetypes.init()

from ccm.Constants import *
from ccm.Conflicts import *
from ccm.Widgets import EdgeSelector
from ccm.Utils import *

import locale
import gettext
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("ccsm", DataDir + "/locale")
gettext.textdomain("ccsm")
_ = gettext.gettext

CurrentUpdater = None

class Setting:
    def __init__(self, Setting, createUpdater=True):
        global CurrentUpdater
        self.Custom = False
        self.Setting = Setting
        self.Blocked = 0
        self.MakeLabel()
        self.Reset = gtk.Button()
        Tooltips.set_tip(self.Reset,_("Reset setting to the default value"))
        self.Reset.set_image(gtk.image_new_from_stock(
            gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON))
        self.Reset.connect('clicked', self.DoReset)
        self._Init()

        if createUpdater and CurrentUpdater == None:
            context = None
            if self.Setting.__class__ == list:
                context = self.Setting[0].Plugin.Context
            else:
                context = self.Setting.Plugin.Context
            CurrentUpdater = Updater(context)

        CurrentUpdater.Append(self)

    def Attach(self, table, row):
        self.Reset.set_sensitive(not self.Setting.ReadOnly)
        self.Widget.set_sensitive(not self.Setting.ReadOnly)
        if self.Custom:
            table.attach(self.Widget, 0, 100, row, row+1, TableDef, TableDef, TableX, TableX)
        else:
            table.attach(self.Label, 0, 1, row, row+1, gtk.FILL, TableDef, TableX, TableX)
            table.attach(self.Widget, 1, 99, row, row+1, TableDef, TableDef, TableX, TableX)
            table.attach(self.Reset, 99, 100, row, row+1, 0, TableDef, TableX, TableX)

    def PureVirtual(self, str):
        raise PureVirtualError, str, self.Setting.Name

    def _Init(self):
        self.PureVirtual('_Init')
    
    def DoReset(self, foo):
        self.Setting.Reset()
        self.Setting.Plugin.Context.Write()
        self.Read()

    def MakeLabel(self):
        self.Label = gtk.EventBox()
        label = gtk.Label()
        if self.Setting.Integrated:
            label.set_markup("<span foreground=\"blue\">%s</span>" % self.Setting.ShortDesc)
        else:
            label.set_markup("<span>%s</span>" % self.Setting.ShortDesc)
        self.Label.add(label)
        Tooltips.set_tip(self.Label, self.Setting.LongDesc)
        label.props.xalign = 0
        label.props.wrap_mode = gtk.WRAP_WORD
        label.set_size_request(160, -1)
        label.set_line_wrap(True)

    def Block(self):
        self.Blocked = self.Blocked+1
    
    def UnBlock(self):
        self.Blocked = self.Blocked-1

    def Read(self):
        self.Block()
        self._Read()
        self.UnBlock()

    def _Read(self):
        self.PureVirtual('_Read')

    def Changed(self, *args, **kwargs):
        if self.Blocked <= 0:
            self._Changed()
            self.Setting.Plugin.Context.Write()

    def _Changed(self):
        self.PureVirtual('_Changed')

class StringMatchSetting(Setting):
    def _Init(self):
        self.Entry = gtk.Entry()
        Tooltips.set_tip(self.Entry, self.Setting.LongDesc)
        self.Entry.connect('activate', self.Changed)
        self.Entry.connect('focus-out-event', self.Changed)
        self.Widget = self.Entry
    
    def _Read(self):
        self.Entry.set_text(self.Setting.Value)

    def _Changed(self):
        self.Setting.Value = self.Entry.get_text()

class FileSetting:
    def __init__(self, Setting):
        self.Setting = Setting
        self.Open = gtk.Button()
        Tooltips.set_tip(self.Open, _("Browse for ") + self.Setting.LongDesc)
        self.Open.set_image(gtk.image_new_from_stock(
            gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
        self.Open.connect('clicked', self.OpenFileChooser)
    
    def CreateFilter(self):
        filter = gtk.FileFilter()
        if len(self.Setting.Hints) > 1:
            if self.Setting.Hints[1] == 'image':
                filter.set_name(_("Images"))
                filter.add_pattern("*.png")
                filter.add_pattern("*.jpg")
                filter.add_pattern("*.jpeg")
                filter.add_pattern("*.svg")
            else:
                filter.add_pattern("*.*")
        else:
            filter.add_pattern("*")
            filter.set_name(_("File"))

        return filter

    def CheckFileType(self, filename):
        if filename.find(".") == -1:
            return True
            
        ext = filename.split(".")[-1]
        try:
            mime = mimetypes.types_map["." + ext]
        except:
            return True
        if len(self.Setting.Hints) > 1:
            if self.Setting.Hints[1] == 'image':
                require = FeatureRequirement(self.Setting.Plugin.Context, 'imagemime:' + mime)
                return require.Resolve()
        
        return True
            
    def OpenFileChooser(self, widget, custom_value=None):
        value = self.Setting.Value
        if custom_value != None:
            value = custom_value
        b = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        chooser = gtk.FileChooserDialog(title=_("Open file.."), buttons=b)
        
        if os.path.exists(value):
            chooser.set_filename(value)
        else:
            chooser.set_current_folder(os.environ.get("HOME"))
        chooser.set_filter(self.CreateFilter())
        ret = chooser.run()
        
        filename = chooser.get_filename()
        chooser.destroy()
        if ret == gtk.RESPONSE_OK:
            if self.CheckFileType(filename):
                self.SetFileName(filename)
    
    def SetFileName(self, text):
        self.PureVirtual('SetFileName')

class FileStringSetting(StringMatchSetting, FileSetting):
    def __init__(self, Setting):
        StringMatchSetting.__init__(self, Setting)
        FileSetting.__init__(self, Setting)
        self.Widget = gtk.HBox()
        self.Widget.set_spacing(5)
        self.Widget.pack_start(self.Entry, True, True)
        self.Widget.pack_start(self.Open, False, False)

    def SetFileName(self, filename):
        self.Entry.set_text(filename)
        self.Changed()

class EnumSetting(Setting):
    def _Init(self):
        self.Widget = gtk.EventBox()
        Tooltips.set_tip(self.Widget, self.Setting.LongDesc)
        self.Combo = gtk.combo_box_new_text()
        self.Widget.add(self.Combo)
        sortedItems = sorted(self.Setting.Info[2].items(), EnumSettingSortCompare)
        for name, value in sortedItems:
            self.Combo.append_text(name)
        self.Combo.connect('changed', self.Changed)

    def _Read(self):
        self.Combo.set_active(self.Setting.Value)

    def _Changed(self):
        active = self.Combo.get_active_text()
        self.Setting.Value = self.Setting.Info[2][active]

class BoolSetting (Setting):

    def _Init (self):
        self.Custom = True
        self.Widget = gtk.HBox ()
        self.CheckButton = gtk.CheckButton ()
        label = gtk.Label (self.Setting.ShortDesc)
        if self.Setting.Integrated:
            label.set_markup ("<span foreground=\"blue\">%s</span>" % \
                              self.Setting.ShortDesc)
        self.align = gtk.Alignment (0, 0.5)
        self.align.add (label)
        self.buttonAlign = gtk.Alignment (0, 0.5)
        self.buttonAlign.set_padding (0, 0, 0, 10)
        self.buttonAlign.add (self.CheckButton)
        Tooltips.set_tip (self.CheckButton, self.Setting.LongDesc)
        self.Widget.pack_start (self.align, True, True)
        self.Widget.pack_start (self.buttonAlign, False, False)
        self.Widget.pack_start (self.Reset, False, False)
        self.CheckButton.connect ('toggled', self.Changed)

    def _Read (self):
        self.CheckButton.set_active (self.Setting.Value)

    def _Changed (self):
        self.Setting.Value = self.CheckButton.get_active ()

class IntFloatSetting(Setting):
    def _Init(self):
        inc = 1
        if self.Setting.Type == 'Int':
            inc = 1
        else:
            inc = self.Setting.Info[2]

        self.Adj = gtk.Adjustment(self.Setting.Value, self.Setting.Info[0], self.Setting.Info[1], inc, inc*10)
        self.Spin = gtk.SpinButton(self.Adj)
        Tooltips.set_tip(self.Spin, self.Setting.LongDesc)
        
        if self.Setting.Type == 'Float':
            self.Spin.set_digits(4)
        
        self.Scale = gtk.HScale(self.Adj)
        Tooltips.set_tip(self.Scale, self.Setting.LongDesc)
        self.Scale.props.draw_value = False
        self.Scale.connect('button-release-event', self.Changed)
        self.Scale.connect('focus-out-event', self.Changed)
        self.Spin.connect('activate', self.Changed)
        self.Spin.connect('button-release-event', self.Changed)
        self.Spin.connect('focus-out-event', self.Changed)
        self.Widget = self.Scale

    def Attach(self, Table, row):
        self.Reset.set_sensitive(not self.Setting.ReadOnly)
        self.Scale.set_sensitive(not self.Setting.ReadOnly)
        self.Spin.set_sensitive(not self.Setting.ReadOnly)
        Table.attach(self.Label, 0, 1, row, row+1, gtk.FILL, TableDef, TableX, TableX)
        Table.attach(self.Scale, 1, 2, row, row+1, TableDef, TableDef, TableX, TableX)
        Table.attach(self.Spin, 2, 3, row, row+1, gtk.FILL, TableDef, TableX, TableX)
        Table.attach(self.Reset, 99, 100, row, row+1, 0, TableDef, TableX, TableX)

    def _Read(self):
        self.Adj.set_value(self.Setting.Value)

    def _Changed(self):
        self.Setting.Value = self.Adj.get_value()

class ColorSetting(Setting):
    def _Init(self):
        self.Widget = gtk.ColorButton()
        Tooltips.set_tip(self.Widget, self.Setting.LongDesc)
        self.Widget.set_use_alpha(True)
        self.Widget.connect('color-set', self.Changed)

    def _Read(self):
        col = gtk.gdk.Color()
        col.red = self.Setting.Value[0]
        col.green = self.Setting.Value[1]
        col.blue = self.Setting.Value[2]
        self.Widget.set_color(col)
        self.Widget.set_alpha(self.Setting.Value[3])

    def _Changed(self):
        col = self.Widget.get_color()
        alpha = self.Widget.get_alpha()
        self.Setting.Value = [col.red, col.green, col.blue, alpha]

class MultiListSetting(Setting):
    def _Init(self):
        self.Widget = gtk.VBox()
        self.Custom = True
        self.Settings = self.Setting # self.Setting is a list in this case
        
        types, cols = self.ListInfo()
        self.Types = types
        self.Store = gtk.ListStore(*types)
        self.View = gtk.TreeView(self.Store)
        Tooltips.set_tip(self.View, _("Multi-list settings. You can double-click a row to edit the values."))
        self.View.set_headers_visible(True)
        for col in cols:
            self.View.insert_column_with_attributes(-1, col[0], col[1], **col[2])
        self.Store.connect('row-deleted', self.Changed)
        self.Store.connect('rows-reordered', self.Changed)
        self.View.connect('row-activated', self.Activated)
        self.Select = self.View.get_selection()
        self.Select.set_mode(gtk.SELECTION_MULTIPLE)

        self.Widget.set_border_width(5)
        self.Widget.set_spacing(5)
        self.Widget.set_size_request(-1, 170)
        self.Scroll = gtk.ScrolledWindow()
        self.Scroll.props.hscrollbar_policy = gtk.POLICY_NEVER
        self.Scroll.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
        self.Scroll.add(self.View)
        self.Widget.pack_start(self.Scroll, True, True)
        
        buttonBox = gtk.HBox(False)
        buttonBox.set_spacing(5)
        self.Widget.pack_start(buttonBox, False, False)
        buttonTypes = ((gtk.STOCK_ADD, self.Add),
                 (gtk.STOCK_DELETE, self.Delete), 
                 (gtk.STOCK_EDIT, self.Edit),
                 (gtk.STOCK_GO_UP, self.MoveUp), 
                 (gtk.STOCK_GO_DOWN, self.MoveDown),)
        for type in buttonTypes:
            b = gtk.Button(type[0])
            b.set_use_stock(True)
            buttonBox.pack_start(b, False, False)
            b.connect('clicked', type[1])
        buttonBox.pack_end(self.Reset, False, False)

    def ColChanged(self, *args, **kwargs):
        if self.Blocked <= 0:
            self._ColChanged(*args, **kwargs)
            self.Settings[0].Plugin.Context.Write()

    def Changed(self, *args, **kwargs):
        if self.Blocked <= 0:
            self._Changed()
            self.Settings[0].Plugin.Context.Write()

    def DoReset(self, foo):
        for setting in self.Settings:
            setting.Reset()
        self.Setting[0].Plugin.Context.Write()
        self.Read()

    def MakeLabel(self):
        pass
    
    def Add(self, b):
        values = []
        for setting in self.Settings:
            if len(setting.Info) > 0 and setting.Info[0] == 'Int' and len(setting.Info[1][2]) > 0:
                sortedItems = sorted(setting.Info[1][2].items(), EnumSettingSortCompare)
                # select first item by default
                pos = 0
                value = sortedItems[pos][0]
            elif setting.Info[0] == "Int" or setting.Info[0] == "Float":
                value = 0
            else:
                value = ""
            values.append(value)
        values = self._Edit(values)
        if values is not None:
            self.Block()
            iter = self.Store.append()
            self.UnBlock()
            col = 0
            for value in values:
                self.SetIterValue(iter, col, value)
                col += 1
            self.Changed()

    def Delete(self, b):
        selectedRows = self.Select.get_selected_rows()[1]
        for path in selectedRows:
            iter = self.Store.get_iter(path)
            self.Store.remove(iter)

    def Edit(self, b):
        selectedRows = self.Select.get_selected_rows()[1]
        if len(selectedRows) == 1:
            iter = self.Store.get_iter(selectedRows[0])
            values = []
            for col in range(len(self.Settings)):
                value = self.Store.get(iter, col)[0]
                values.append(value)
            values = self._Edit(values)
            if values != None:
                col = 0
                for value in values:
                    self.SetIterValue(iter, col, value)
                    col += 1
                self.Changed()

    def MoveUp(self, b):
        selectedRows = self.Select.get_selected_rows()[1]
        if len(selectedRows) == 1:
            iter = self.Store.get_iter(selectedRows[0])
            prev = self.Store.get_iter_first()
            if not self.Store.get_path(prev) == self.Store.get_path(iter):
                while prev is not None and not self.Store.get_path(self.Store.iter_next(prev)) == self.Store.get_path(iter):
                    prev = self.Store.iter_next(prev)
                self.Store.swap(iter, prev)

    def MoveDown(self, b):
        selectedRows = self.Select.get_selected_rows()[1]
        if len(selectedRows) == 1:
            iter = self.Store.get_iter(selectedRows[0])
            next = self.Store.iter_next(iter)
            if next is not None:
                self.Store.swap(iter, next)

    def ListInfo(self):
        types = []
        cols = []
        col = 0
        for setting in self.Settings:
            if setting.Info[0] == "String" or setting.Info[0] == "Match":
                types.append(gobject.TYPE_STRING)
            elif setting.Info[0] == "Int" and len(setting.Info[1][2]) > 0:
                types.append(gobject.TYPE_STRING)
            elif setting.Info[0] == "Int":
                types.append(gobject.TYPE_INT)
            elif setting.Info[0] == "Float":
                types.append(gobject.TYPE_FLOAT)
            
            renderer = gtk.CellRendererText()
            renderer.connect("edited", self.ColChanged, col)
            cols.append((setting.ShortDesc, renderer, {'text':col}))
            col += 1

        return types, cols

    def Activated(self, object, path, col):
        self.Edit(None)

    def _Read(self):
        self.Store.clear()
        iters = []
        for values in self.Settings[0].Value:
            iters.append(self.Store.append())

        row = 0
        for iter in iters:
            for j in range(len(self.Settings)):
                setting = self.Settings[j]
                value = None
                if len(setting.Info) > 0 and setting.Info[0] == 'Int' and len(setting.Info[1][2]) > 0:
                    pos = setting.Value[row]
                    sortedItems = sorted(setting.Info[1][2].items(), EnumSettingSortCompare)
                    value = sortedItems[pos][0]
                else:
                    if row < len(setting.Value):
                        value = setting.Value[row]
                    else:
                        if setting.Info[0] == 'Int':
                            value = 0
                        elif setting.Info[0] == 'String' or setting.Info[0] == 'Match':
                            value = ""
                self.Store.set(iter, j, value)
            row += 1

    def _Edit(self, values=None):
        dlg = gtk.Dialog(_("Edit"))
        dlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK).grab_default()
        dlg.set_default_response(gtk.RESPONSE_OK)
        table = gtk.Table()
        dlg.vbox.pack_start(table)

        row = 0
        widgets = []
        for setting in self.Settings:
            ebox = gtk.EventBox()
            label = gtk.Label(setting.ShortDesc)
            ebox.add(label)
            Tooltips.set_tip(ebox, setting.LongDesc)
            if self.Types[row] == gobject.TYPE_STRING and setting.Info[0] == 'Int' and len(setting.Info[1][2]) > 0:
                comboBox = gtk.combo_box_new_text()
                sortedItems = sorted(setting.Info[1][2].items(), EnumSettingSortCompare)
                for item in sortedItems:
                    comboBox.append_text(item[0])
                if values != None:
                    pos = values[row]
                    value = setting.Info[1][2][pos]
                    comboBox.set_active(value)
                table.attach(ebox, 0, 1, row, row+1, xpadding=5, xoptions=gtk.FILL)
                table.attach(comboBox, 2, 3, row, row+1, xpadding=5)
                widgets.append(comboBox)
            elif self.Types[row] == gobject.TYPE_STRING:
                Tooltips.set_tip(ebox, setting.LongDesc)
                entry = gtk.Entry()
                Tooltips.set_tip(entry, setting.LongDesc)
                if values != None:
                    entry.set_text(values[row])
                table.attach(ebox, 0, 1, row, row+1, xpadding=5, xoptions=gtk.FILL)
                table.attach(entry, 2, 3, row, row+1, xpadding=5)
                widgets.append(entry)
            elif self.Types[row] == gobject.TYPE_INT or self.Types[row] == gobject.TYPE_FLOAT:
                inc = 0
                if setting.Info[0] == 'Int':
                    inc = 1
                else:
                    inc = setting.Info[1][2]
                value = 0
                if values != None:
                    value = values[row]
                adjustment = gtk.Adjustment(value, setting.Info[1][0], setting.Info[1][1], inc, inc*10)
                spin = gtk.SpinButton(adjustment)
                Tooltips.set_tip(spin, setting.LongDesc)
                if setting.Info[0] == 'Float':
                    spin.set_digits(4)
                scale = gtk.HScale(adjustment)
                Tooltips.set_tip(scale, setting.LongDesc)
                scale.props.draw_value = False
                table.attach(ebox, 0, 1, row, row+1, xpadding=5, xoptions=gtk.FILL)
                table.attach(scale, 2, 3, row, row+1, xpadding=5)
                table.attach(spin, 3, 4, row, row+1, xpadding=5, xoptions=gtk.FILL)
                widgets.append(adjustment)
            row += 1

        dlg.vbox.show_all()
        ret = dlg.run()
        dlg.destroy()

        if ret == gtk.RESPONSE_OK:
            values = []
            row = 0
            for type in self.Types:
                if type == gobject.TYPE_STRING:
                    value = None
                    if widgets[row].__class__ == gtk.Entry:
                        value = widgets[row].get_text()
                    elif widgets[row].__class__ == gtk.ComboBox:
                        value = widgets[row].get_active_text()
                    values.append(value)
                elif type == gobject.TYPE_INT:
                    value = int(widgets[row].get_value())
                    values.append(value)
                elif type == gobject.TYPE_FLOAT:
                    value = widgets[row].get_value()
                    values.append(value)
                row += 1
            return values

        return None

    def SetIterValue(self, iter, col, value):
        if self.Types[col] == gobject.TYPE_STRING:
            self.Store.set(iter, col, value)
        elif self.Types[col] == gobject.TYPE_INT:
            self.Store.set(iter, col, int(value))
        elif self.Types[col] == gobject.TYPE_FLOAT:
            self.Store.set(iter, col, float(value))

    def _ColChanged(self, obj, path, value, col):
        iter = self.Store.get_iter_from_string(path)
        self.SetIterValue(iter, col, value)
        self._Changed()

    def _Changed(self):
        col = 0
        for setting in self.Settings:
            iter = self.Store.get_iter_first()
            values = []
            while iter:
                value = None
                if setting.Info[0] == 'Int' and len(setting.Info[1][2]) > 0:
                    pos = self.Store.get(iter, col)[0]
                    value = setting.Info[1][2][pos]
                else:
                    value = self.Store.get(iter, col)[0]
                values.append(value)
                iter = self.Store.iter_next(iter)
            setting.Value = values
            col += 1

    def Attach(self, table, row):
        table.attach(self.Widget, 0, 100, row, row+1, xpadding=5)

class ListSetting(Setting):
    def _Init(self):
        self.Widget = gtk.Frame(self.Setting.ShortDesc)
        label = self.Widget.get_label_widget()
        if self.Setting.Integrated:
            label.set_markup("<span foreground=\"blue\">%s</span>" % self.Setting.ShortDesc)
        self.Custom = True
        
        info = self._ListInfo()
        self.Store = gtk.ListStore(*info[0])
        self.View = gtk.TreeView(self.Store)
        Tooltips.set_tip(self.View, self.Setting.LongDesc)
        if len(info[0]) == 1:
            self.View.set_headers_visible(False)
        for i in info[1]:
            self.View.insert_column_with_attributes(-1, i[1], i[0], **i[2])
        self.Store.connect('row-changed', self.Changed)
        self.Store.connect('row-deleted', self.Changed)
        self.Store.connect('row-inserted', self.Changed)
        self.Store.connect('rows-reordered', self.Changed)
        self.View.connect('row-activated', self.Activated)
        self.Select = self.View.get_selection()
        self.Select.set_mode(gtk.SELECTION_MULTIPLE)

        box = gtk.VBox()
        box.set_border_width(5)
        box.set_spacing(5)
        self.Widget.add(box)
        self.Scroll = gtk.ScrolledWindow()
        self.Scroll.props.hscrollbar_policy = gtk.POLICY_NEVER
        self.Scroll.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
        self.Scroll.add(self.View)
        box.pack_start(self.Scroll, True, True)
        
        buttonBox = gtk.HBox(False)
        buttonBox.set_spacing(5)
        box.pack_start(buttonBox, False, False)
        buttonTypes = ((gtk.STOCK_ADD, self.Add),
                 (gtk.STOCK_DELETE, self.Delete), 
                 (gtk.STOCK_EDIT, self.Edit),
                 (gtk.STOCK_GO_UP, self.MoveUp), 
                 (gtk.STOCK_GO_DOWN, self.MoveDown),)
        for type in buttonTypes:
            b = gtk.Button(type[0])
            b.set_use_stock(True)
            buttonBox.pack_start(b, False, False)
            b.connect('clicked', type[1])
        buttonBox.pack_end(self.Reset, False, False)

    def Add(self, b):
        value = self._Edit()
        if value is not None:
            self.Block()
            Iter = self.Store.append()
            self.UnBlock()
            self._ListSet(Iter, value)

    def Delete(self, b):
        selectedRows = self.Select.get_selected_rows()[1]
        for path in selectedRows:
            iter = self.Store.get_iter(path)
            self.Store.remove(iter)

    def Activated(self, object, path, col):
        self.Edit(None)

    def Edit(self, b):
        selectedRows = self.Select.get_selected_rows()[1]
        if len(selectedRows) == 1:
            iter = self.Store.get_iter(selectedRows[0])
            value = self._Edit(self._ListGet(iter))
            if value is not None:
                self._ListSet(iter, value)

    def MoveUp(self, b):
        selectedRows = self.Select.get_selected_rows()[1]
        if len(selectedRows) == 1:
            iter = self.Store.get_iter(selectedRows[0])
            prev = self.Store.get_iter_first()
            if not self.Store.get_path(prev) == self.Store.get_path(iter):
                while prev is not None and not self.Store.get_path(self.Store.iter_next(prev)) == self.Store.get_path(iter):
                    prev = self.Store.iter_next(prev)
                self.Store.swap(iter, prev)

    def MoveDown(self, b):
        selectedRows = self.Select.get_selected_rows()[1]
        if len(selectedRows) == 1:
            iter = self.Store.get_iter(selectedRows[0])
            next = self.Store.iter_next(iter)
            if next is not None:
                self.Store.swap(iter, next)

    def _ListInfo(self):
        self.PureVirtual('_ListInfo')

    def _Read(self):
        self.Store.clear()
        for value in self.Setting.Value:
            iter = self.Store.append()
            self._ListSet(iter, value)

    def _ListSet(self, iter, value):
        self.PureVirtual('_ListRead')

    def _ListGet(self, iter):
        self.PureVirtual('_ListGet')

    def _Edit(self, d, value = None):
        self.PureVirtual('_Edit')

    def _Changed(self):
        values = []
        iter = self.Store.get_iter_first()
        while iter:
            value = self._ListGet(iter)
            if value != "":
                values.append(value)
            iter = self.Store.iter_next(iter)
        self.Setting.Value = values

    def Attach(self, table, row):
        self.Widget.set_sensitive(not self.Setting.ReadOnly)
        self.Reset.set_sensitive(not self.Setting.ReadOnly)
        table.attach(self.Widget, 0, 100, row, row+1, xpadding=5)

class StringMatchListSetting(ListSetting):
    def _ListInfo(self):
        return (gobject.TYPE_STRING, ), [(gtk.CellRendererText(), _("Value (%s)") % self.Setting.Info[0], {'text':0})]

    def _ListSet(self, iter, value):
        self.Store.set(iter, 0, value)

    def _ListGet(self, iter):
        return self.Store.get(iter, 0)[0]

    def _Edit(self, value=""):
        dlg = gtk.Dialog(_("Edit %s") % self.Setting.ShortDesc)
        dlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK).grab_default()
        dlg.set_default_response(gtk.RESPONSE_OK)
        
        ebox = gtk.EventBox()
        label = gtk.Label(_("Value (%s) for %s:") % (self.Setting.Info[0], self.Setting.ShortDesc))
        ebox.add(label)
        
        Tooltips.set_tip(ebox, self.Setting.LongDesc)
        dlg.vbox.pack_start(ebox)
        
        entry = gtk.Entry()
        Tooltips.set_tip(entry, self.Setting.LongDesc)
        entry.props.activates_default = True
        entry.set_text(value)
        dlg.vbox.pack_start(entry)
        
        dlg.vbox.show_all()
        ret = dlg.run()
        dlg.destroy()

        if ret == gtk.RESPONSE_OK:
            return entry.get_text()
        return None

class FileListSetting(StringMatchListSetting, FileSetting):
    def __init__(self, Setting):
        StringMatchListSetting.__init__(self, Setting)
        FileSetting.__init__(self, Setting)
    
    def _Edit(self, value=""):
        dlg = gtk.Dialog(_("Edit %s") % self.Setting.ShortDesc)
        dlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK).grab_default()
        dlg.set_default_response(gtk.RESPONSE_OK)
        
        ebox = gtk.EventBox()
        label = gtk.Label(_("Value (%s) for %s:") % (self.Setting.Info[0], self.Setting.ShortDesc))
        ebox.add(label)
        
        Tooltips.set_tip(ebox, self.Setting.LongDesc)
        dlg.vbox.pack_start(ebox)

        hbox = gtk.HBox()
        hbox.set_spacing(5)
        
        entry = gtk.Entry()
        Tooltips.set_tip(entry, self.Setting.LongDesc)
        entry.props.activates_default = True
        entry.set_text(value)
        hbox.pack_start(entry)

        self.Entry = entry

        open = gtk.Button()
        open.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
        open.connect('clicked', self.OpenFileChooser, value)
        hbox.pack_start(open, False, False)

        dlg.vbox.pack_start(hbox)
        
        dlg.vbox.show_all()
        ret = dlg.run()
        dlg.destroy()

        self.Entry = None

        if ret == gtk.RESPONSE_OK:
            return entry.get_text()
        return None

    def SetFileName(self, filename):
        if self.Entry != None:
            self.Entry.set_text(filename)

class IntDescListSetting(Setting):
    def _Init(self):
        self.Widget = gtk.Frame(self.Setting.ShortDesc)
        self.Table = gtk.Table()
        self.Custom = True
        
        row = 0
        col = 0
        self.Checks = []
        sortedItems = sorted(self.Setting.Info[1][2].items(), EnumSettingSortCompare)
        self.minVal = sortedItems[0][1]
        for key, value in sortedItems:
            box = gtk.CheckButton(key)
            Tooltips.set_tip(box, self.Setting.LongDesc)
            self.Checks.append((key, box))
            self.Table.attach(box, col, col+1, row, row+1, TableDef, TableDef, TableX, TableX)
            box.connect('toggled', self.Changed)
            col = col+1
            if (col >=  3):
                col = 0
                row = row+1
        
        self.HBox = gtk.HBox()
        self.VBox = gtk.VBox()
        self.HBox.pack_start(self.VBox, False, False)
        self.HBox.pack_start(self.Table, True, True)
        self.VBox.pack_start(self.Reset, False, False)
        self.Widget.add(self.HBox)

    def _Read(self):
        for key, box in self.Checks:
            box.set_active(False)
        for setVal in self.Setting.Value:
            self.Checks[setVal-self.minVal][1].set_active(True)

    def _Changed(self):
        values = []
        for key, box in self.Checks:
            if box.get_active():
                values.append(self.Setting.Info[1][2][key])
        self.Setting.Value = values
    
    def Attach(self, table, row):
        self.Widget.set_sensitive(not self.Setting.ReadOnly)
        self.Reset.set_sensitive(not self.Setting.ReadOnly)
        table.attach(self.Widget, 0, 100, row, row+1, xpadding = 5)

class IntFloatListSetting(ListSetting):
    def _ListInfo(self):
        return (gobject.TYPE_STRING, ), [(gtk.CellRendererText(), 
            _("Value (%s)") % self.Setting.Info[0], {'text':0})]

    def _ListSet(self, Iter, v):
        self.Store.set(Iter, 0, str(v))

    def _ListGet(self, Iter):
        return eval(self.Store.get(Iter, 0)[0])

    def _Edit(self, value = None):
        dlg = gtk.Dialog(_("Edit %s") % self.Setting.ShortDesc)
        dlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK).grab_default()
        dlg.set_default_response(gtk.RESPONSE_OK)
        label = gtk.Label(_("Value (%s) for %s:") % (self.Setting.Info[0], self.Setting.ShortDesc))
        ebox = gtk.EventBox()
        ebox.add(label)
        Tooltips.set_tip(ebox, self.Setting.LongDesc)
        dlg.vbox.pack_start(ebox)
        box = gtk.HBox()
        dlg.vbox.pack_start(box)
        
        val = self.Setting.Info[1][0]
        if value is not None:
            val = value
        
        if self.Setting.Info[0] == 'Int':
            inc = 1
        else:
            inc = self.Setting.Info[1][2]
        
        adj = gtk.Adjustment(val, 
                self.Setting.Info[1][0], self.Setting.Info[1][1], 
                inc, inc*10)
        spin = gtk.SpinButton(adj)
        Tooltips.set_tip(spin, setting.LongDesc)
        if self.Setting.Info[0] == 'Float':
            spin.set_digits(4)
        scale = gtk.HScale(adj)
        Tooltips.set_tip(scale, setting.LongDesc)
        scale.props.draw_value = False
        
        box.pack_start(scale, True, True)
        box.pack_start(spin, False, False)
        
        dlg.vbox.show_all()
        ret = dlg.run()
        dlg.destroy()

        if ret == gtk.RESPONSE_OK:
            return adj.get_value()
        return None

class KeySetting (Setting):

    key = 0
    mods = 0
    iter = None

    def _Init (self):
        self.store = gtk.ListStore (gobject.TYPE_UINT, gobject.TYPE_UINT)
        self.store.append ([0, 0])
        self.iter = self.store.get_iter_root ()
        tv = gtk.TreeView (self.store)
        tv.set_headers_visible (False)
        key_renderer = gtk.CellRendererAccel ()
        key_renderer.set_property ("editable", True)
        key_renderer.connect ("accel-edited", self.bindingEdited)
        key_renderer.connect ("accel-cleared", self.bindingCleared)
        tv.insert_column_with_attributes (-1, "", key_renderer,
                                          accel_key = 0, accel_mods = 1)

        Tooltips.set_tip (tv, self.Setting.LongDesc)

        alignment = gtk.Alignment (1.0)
        alignment.add (tv)

        self.Widget = alignment

    def bindingCleared (self, renderer, path):
        '''Binding cleared callback'''
        self.bindingEdited (renderer, path, 0, 0, 0)

    def bindingEdited (self, renderer, path, key, mods, keycode):
        '''Binding edited callback'''
        # Update & save binding
        if key or mods:
            accel = gtk.accelerator_name (key, mods)
        else:
            accel = "Disabled"
        conflict = ActionConflict (self.Setting, key = accel)
        if conflict.Resolve (CurrentUpdater):
            self.key = key
            self.mods = mods
            self.Changed ()
            # Update store
            self.store.set (self.iter, 0, key, 1, mods)

    def _Read (self):
        self.key, self.mods = gtk.accelerator_parse (self.Setting.Value)
        self.store.set (self.iter, 0, self.key, 1, self.mods)

    def _Changed (self):
        self.Setting.Value = gtk.accelerator_name (self.key, self.mods)

class EdgeSetting (Setting):

    current = ""

    def _Init (self):
        self.Button = gtk.Button ()
        self.setButtonLabel ()
        self.Button.connect ("clicked", self.RunEdgeSelector)

        Tooltips.set_tip (self.Button, self.Setting.LongDesc)

        self.Widget = self.Button

    def setButtonLabel (self):
        label = self.current
        if len (self.current):
            edges = self.current.split ("|")
            edges = map (lambda s: _(s), edges)
            label = ", ".join (edges)
        else:
            label = _("None")
        self.Button.set_label (label)

    def RunEdgeSelector (self, widget):
        dlg = gtk.Dialog (_("Edit %s") % self.Setting.ShortDesc)
        dlg.set_position (gtk.WIN_POS_CENTER_ON_PARENT)
        parent = self.Widget.get_parent_window ().get_toplevel ()
        dlg.set_transient_for (parent.get_user_data ())
        dlg.add_button (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dlg.add_button (gtk.STOCK_OK, gtk.RESPONSE_OK).grab_default()
        dlg.set_default_response (gtk.RESPONSE_OK)
        
        selector = EdgeSelector (self.current)
        alignment = gtk.Alignment ()
        alignment.set_padding (10, 10, 10, 10)
        alignment.add (selector)

        Tooltips.set_tip (selector, self.Setting.LongDesc)
        dlg.vbox.pack_start (alignment)
        
        dlg.vbox.show_all ()
        ret = dlg.run ()
        dlg.destroy ()

        if ret != gtk.RESPONSE_OK:
            return

        new = selector.current
        conflict = ActionConflict (self.Setting, edges = new)
        if conflict.Resolve (CurrentUpdater):
            self.current = new
            self.Changed ()

    def _Read (self):
        self.current = self.Setting.Value
        self.setButtonLabel ()

    def _Changed (self):
        self.Setting.Value = self.current
        self.setButtonLabel ()

BellSetting = BoolSetting

def MakeSetting(setting):
    if setting.Type == 'String' or setting.Type == 'Match':
        if len(setting.Hints) > 0 and setting.Hints.__contains__('file'):
            return FileStringSetting(setting)
        else:
            return StringMatchSetting(setting)
    elif setting.Type == 'Bool':
        return BoolSetting(setting)
    elif setting.Type == 'Int' and len(setting.Info[2].keys()) > 0:
        return EnumSetting(setting)
    elif setting.Type == 'Float' or setting.Type == 'Int':
        return IntFloatSetting(setting)
    elif setting.Type == 'Color':
        return ColorSetting(setting)
    elif setting.Type == 'List':
        if setting.Info[0] == 'String' or setting.Info[0] == 'Match':
            if len(setting.Hints) > 0 and setting.Hints.__contains__('file'):
                return FileListSetting(setting)
            else:
                return StringMatchListSetting(setting)
        elif setting.Info[0] == 'Int':
            if len(setting.Info[1][2]) > 0:
                return IntDescListSetting(setting)
            else:
                return IntFloatListSetting(setting)
        elif setting.Info[0] == 'Float':
            return IntFloatListSetting(setting)
        else:
            raise TypeError, _("Unhandled list type %s for %s")%(setting.Info[0], setting.Name)
    elif setting.Type == 'Key':
        return KeySetting (setting)
    elif setting.Type == 'Edge':
        return EdgeSetting(setting)
    elif setting.Type == 'Bell':
        return BellSetting(setting)
    return None

class SubGroupArea:
    def __init__(self, name, subGroup, filter=None):
        self.MySettings = []
        settings = FilterSettings(sorted(sum((v.values() for v in [subGroup.Display]+[subGroup.Screens[CurrentScreenNum]]), []), SettingSortCompare), filter)
        if name == '':
            self.Widget = gtk.Table()
            self.Child = self.Widget
        else:
            self.Widget = gtk.Frame()
            self.Expander = gtk.Expander(name)
            self.Widget.add(self.Expander)
            self.Expander.set_expanded(False)
            self.Child = gtk.Table()
            self.Expander.add(self.Child)

            # create a special widget for list subGroups
            if len(settings) > 1 and HasOnlyType(settings, 'List'):
                multiList = MultiListSetting(settings)
                multiList.Read()
                multiList.Attach(self.Child, 0)
                self.Empty = False
                self.Expander.set_expanded(True)

                return # exit earlier to avoid unneeded logic's
        
        self.Empty = True
        row = 0
        for setting in settings:
            if not setting.Name == 'active_plugins':
                set = MakeSetting(setting)
                if set is not None:
                    set.Read()
                    set.Attach(self.Child, row)
                    self.MySettings = self.MySettings + [set]
                    row = row+1
                    self.Empty = False

        if name != '' and row < 4: # ahi hay magic numbers!
            self.Expander.set_expanded(True)

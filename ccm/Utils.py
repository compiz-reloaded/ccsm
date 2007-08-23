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

import os

import pygtk
import gtk
import gtk.gdk
import gobject

from ccm.Constants import *

import locale
import gettext
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("ccsm", DataDir + "/locale")
gettext.textdomain("ccsm")
_ = gettext.gettext

def makeActionImage (action):
    img = gtk.Image ()
    size = 22
    path = "%s/mini-%s.png" % (PixmapDir, action)
    try:
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size (path, size, size)
        img.set_from_pixbuf (pixbuf)
    except:
        img.set_from_stock (gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_BUTTON)
    align = gtk.Alignment (0, 0.5)
    align.set_padding (0, 0, 0, 10)
    align.add (img)
    return align    

def makeCustomSetting (desc, integrated, widget, reset):
    box = gtk.HBox ()
    label = gtk.Label (desc)
    if integrated:
        label.set_markup ("<span foreground=\"blue\">%s</span>" % desc)
    align = gtk.Alignment (0, 0.5)
    align.add (label)
    widgetAlign = gtk.Alignment (0, 0.5)
    widgetAlign.set_padding (0, 0, 0, 10)
    widgetAlign.add (widget)
    box.pack_start (align, True, True)
    box.pack_start (widgetAlign, False, False)
    box.pack_start (reset, False, False)
    return box

def getScreens():
    screens = []
    display = gtk.gdk.display_get_default()
    nScreens = display.get_n_screens()
    for i in range(nScreens):
        screens.append(i)
    return screens

class Style:
    def __init__(self):
        fakeWindow = gtk.Window()
        styleWidget = gtk.Entry()
        fakeWindow.add(styleWidget)
        styleWidget.realize()
        bc = styleWidget.style.bg[gtk.STATE_SELECTED]
        self.BrightColor = "#%.4x%.4x%.4x" % (bc.red, bc.green, bc.blue)
        bc = styleWidget.style.light[gtk.STATE_NORMAL]
        self.BackgroundColor = "#%.4x%.4x%.4x" % (bc.red, bc.green, bc.blue)
        styleWidget.destroy()
        fakeWindow.destroy()

class Image(gtk.Image):
    def __init__(self, name=None, type=ImageNone, size = 32):
        gtk.Image.__init__(self)

        if name != None:
            if type == ImagePlugin:
                iconpath = "%s/plugin-%s.svg" % (PixmapDir, name)
                if not os.path.exists(iconpath):
                    iconpath = "%s/plugin-unknown.svg" % PixmapDir
                try:
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(iconpath, size, size)
                    self.set_from_pixbuf(pixbuf)
                except:
                    self.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_BUTTON)

            elif type == ImageCategory:
                iconpath = "%s/category-%s.svg" % (PixmapDir, name)
                if not os.path.exists(iconpath):
                    iconpath = "%s/category-uncategorized.svg" % PixmapDir
                try:
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(iconpath, size, size)
                    self.set_from_pixbuf(pixbuf)
                except:
                    self.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_BUTTON)

            elif type == ImageThemed:
                iconTheme = gtk.icon_theme_get_default()
                try:
                    pixbuf = iconTheme.load_icon(name, size, 0)
                    self.set_from_pixbuf(pixbuf)
                except:
                    self.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_BUTTON)

            elif type == ImageStock:
                try:
                    self.set_from_stock(name, size)
                except:
                    self.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_BUTTON)

class Label(gtk.Label):
    def __init__(self, value = "", wrap = 160):
        gtk.Label.__init__(self, value)
        self.props.xalign = 0
        self.props.wrap_mode = gtk.WRAP_WORD
        self.set_line_wrap(True)
        self.set_size_request(wrap, -1)

class NotFoundBox(gtk.Alignment):
    def __init__(self, value):
        gtk.Alignment.__init__(self, 0.5, 0.5, 0.0, 0.0)
        
        box = gtk.HBox()
        self.Warning = gtk.Label()
        self.Markup = _("<span size=\"large\"><b>No matches found.</b> </span><span>\n\n Your filter \"<b>%s</b>\" does not match any items.</span>")
        self.Warning.set_markup(self.Markup % value)
        image = Image("face-surprise", ImageThemed, 48)
            
        box.pack_start(image, False, False, 0)
        box.pack_start(self.Warning, True, True, 15)
        self.add(box)

    def update(self, value):
        self.Warning.set_markup(self.Markup % value)

# Updates all registered setting when they where changed through CompizConfig
class Updater:
    def __init__(self, context):
        self.VisibleSettings = []
        self.NotRemoved = []
        self.Context = context

        gobject.timeout_add(2000, self.Update)
    
    def Append(self, setting):
        self.VisibleSettings.append(setting)

    def UpdateSetting (self, setting):
        for widget in self.VisibleSettings:
            if widget.Setting == setting:
                widget.Read ()
                break

    def Update(self):
        changed = self.Context.ProcessEvents()
        if changed:
            changedSettings = self.Context.ChangedSettings
            for settingWidget in self.VisibleSettings:
                # Remove already destroyed widgets
                if not settingWidget.Widget.get_parent():
                    self.VisibleSettings.remove(settingWidget)
                
                # Exception for multi settings widgets (multi list widget, action page, etc.)
                if settingWidget.Setting.__class__ != list:
                    if settingWidget.Setting in changedSettings:
                        settingWidget.Read()
                        changedSettings.remove(settingWidget.Setting)
                else:
                    read = False
                    for setting in settingWidget.Setting:
                        if setting in changedSettings:
                            read = True
                            changedSettings.remove(setting)
                    if read:
                        settingWidget.Read()
            # For removing non-visible settings
            for oldSetting in self.NotRemoved:
                if oldSetting in changedSettings:
                    changedSettings.remove(oldSetting)
            self.NotRemoved = changedSettings
            self.Context.ChangedSettings = changedSettings

        return True

class PureVirtualError(Exception):
    pass

def SettingSortCompare(v1, v2):
    return cmp(v1.Plugin.Ranking[v1.Name], v2.Plugin.Ranking[v2.Name])

def FirstItemSortCompare(sg1, sg2):
    return cmp(sg1[0], sg2[0])

def EnumSettingSortCompare(v1, v2):
    return cmp(v1[1], v2[1])

def PluginSortCompare(p1, p2):
    return cmp(p1.ShortDesc, p2.ShortDesc)

# singleRun is used to combine the run stages, in this case run is a list
# containing the run levels which should be used to filter the settings
def FilterSettings(settings, filter, run=0, singleRun=False):
    if filter == None:
        return settings

    filteredSettings = []

    for setting in settings:
        # First run, only search in shortDesc and name
        if run == 0 or (singleRun and run.count(0) != 0):
            shortDesc = setting.ShortDesc.lower()
            name = setting.Name.lower()
            if shortDesc.find(filter) != -1:
                filteredSettings.append(setting)
                continue
            elif name.find(filter) != -1:
                filteredSettings.append(setting)
                continue
        # Then in longDesc
        if run == 1 or (singleRun and run.count(1) != 0):
            longDesc = setting.LongDesc.lower()
            if longDesc.find(filter) != -1:
                filteredSettings.append(setting)
                continue
        # Finally search in the option value
        if run == 2 or (singleRun and run.count(2) != 0):
            value = ""
            # make sure enum settings work too
            if setting.Type == 'Int' and len(setting.Info[2].keys()) > 0:
                    value = sorted(setting.Info[2].items(), EnumSettingSortCompare)[setting.Value][0]
                    value = value.lower()
            # also make sure intDesc settings work right
            elif setting.Type == 'List' and setting.Info[0] == 'Int' and len(setting.Info[1][2]) > 0:
                for int in setting.Value:
                    for item in setting.Info[1][2].items():
                        if item[1] == int:
                            value += item[0]
                value = value.lower()
            else:
                value = str(setting.Value).lower()
            if value.find(filter) != -1:
                filteredSettings.append(setting)

    # Nothing was found, search also in the longDesc/value
    if len(filteredSettings) == 0 and run < 2 and not singleRun:
        return FilterSettings(settings, filter, run+1, False)

    return filteredSettings

def HasOnlyType(settings, type):
    empty = True
    for setting in settings:
        empty = False
        if setting.Type != type:
            return False
    return not empty

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
#          Guillaume Seguin (guillaume@segu.in)
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

def gtk_process_events ():
    while gtk.events_pending ():
        gtk.main_iteration ()

def protect_pango_markup (string):
    string = string.replace ("&", "&amp;")
    return string.replace ("<", "&lt;").replace (">", "&gt;")

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

class Image (gtk.Image):

    def __init__ (self, name = None, type = ImageNone, size = 32):
        gtk.Image.__init__ (self)

        if not name:
            return

        try:
            if type in  (ImagePlugin, ImageCategory, ImageThemed):
                if type == ImagePlugin:
                    name = "compiz-plugin-" + name
                elif type == ImageCategory:
                    name = "compiz-category-" + name
                iconTheme = gtk.icon_theme_get_default ()
                pixbuf = iconTheme.load_icon (name, size, 0)
                self.set_from_pixbuf (pixbuf)
            elif type == ImageStock:
                self.set_from_stock (name, size)
        except:
            self.set_from_stock (gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_BUTTON)

class ActionImage (gtk.Alignment):

    map = {
            "keyboard"  : "input-keyboard",
            "button"    : "input-mouse",
            "edges"     : "video-display",
            "bell"      : "audio-x-generic"
          }

    def __init__ (self, action):
        gtk.Alignment.__init__ (self, 0, 0.5)
        self.set_padding (0, 0, 0, 10)
        if action in self.map: action = self.map[action]
        self.add (Image (name = action, type = ImageThemed, size = 22))

class PrettyButton (gtk.Button):

    __gsignals__ = {
        'expose-event'      : 'override',
    }

    def __init__ (self):
        super (PrettyButton, self).__init__ ()
        self.states = {
                        "focus"   : False,
                        "pointer" : False
                      }
        self.set_size_request (200, -1)
        self.set_relief (gtk.RELIEF_NONE)
        self.connect ("focus-in-event", self.update_state_in, "focus")
        self.connect ("focus-out-event", self.update_state_out, "focus")

    def update_state_in (self, *args):
        state = args[-1]
        self.set_state (gtk.STATE_PRELIGHT)
        self.states[state] = True

    def update_state_out (self, *args):
        state = args[-1]
        self.states[state] = False
        if True in self.states.values ():
            self.set_state (gtk.STATE_PRELIGHT)
        else:
            self.set_state (gtk.STATE_NORMAL)

    def do_expose_event (self, event):
        has_focus = self.flags () & gtk.HAS_FOCUS
        if has_focus:
            self.unset_flags (gtk.HAS_FOCUS)

        ret = super (PrettyButton, self).do_expose_event (self, event)

        if has_focus:
            self.set_flags (gtk.HAS_FOCUS)

        return ret

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

class IdleSettingsParser:
    def __init__(self, context):
        def FilterPlugin (p):
            return not p.Initialized and p.Enabled

        self.Context = context
        self.PluginList = filter (lambda p: FilterPlugin (p[1]),
                                  self.Context.Plugins.items ())
        
        gobject.timeout_add (200, self.Wait)

    def Wait(self):
        if len (self.PluginList) == 0:
            return False
        
        gobject.idle_add (self.ParseSettings)
        
        return False
    
    def ParseSettings(self):
        name, plugin = self.PluginList[0]

        if not plugin.Initialized:
            plugin.Update ()

        self.PluginList.remove (self.PluginList[0])

        gobject.timeout_add (200, self.Wait)

        return False

# Updates all registered setting when they where changed through CompizConfig
class Updater:

    def __init__ (self):
        self.VisibleSettings = []
        self.Plugins = []
        self.NotRemoved = []

    def SetContext (self, context):
        self.Context = context

        gobject.timeout_add (2000, self.Update)

    def Append(self, setting):
        self.VisibleSettings.append(setting)

    def AppendPlugin (self, plugin):
        self.Plugins.append (plugin)

    def UpdateSetting (self, setting):
        for widget in self.VisibleSettings:
            if widget.Setting == setting:
                widget.Read ()
                break

    def Update(self):
        changed = self.Context.ProcessEvents()
        if changed:
            changedSettings = self.Context.ChangedSettings
            if len (filter (lambda s :  s.Plugin.Name == "core" and \
                                        s.Name == "active_plugins",
                            changedSettings)):
                map (lambda plugin: plugin.Read (), self.Plugins)
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
            map (lambda s: changedSettings.remove (s),
                 filter (lambda s: s in changedSettings, self.NotRemoved))
            self.NotRemoved = changedSettings
            self.Context.ChangedSettings = changedSettings

        return True

GlobalUpdater = Updater ()

class PluginSetting:

    def __init__ (self, plugin, widget):
        self.Widget = widget
        self.Plugin = plugin
        GlobalUpdater.AppendPlugin (self)

    def Read (self):
        self.Widget.set_active (self.Plugin.Enabled)

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

def HasOnlyType (settings, type):
    f = filter (lambda s: s.Type != type, settings)
    return len (settings) > 0 and len (f) == 0

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
#          Patrick Niklaus (patrick.niklaus@student.kit.edu)
#          Guillaume Seguin (guillaume@segu.in)
#          Christopher Williams (christopherw@verizon.net)
#          Sorokin Alexei (sor.alexei@meowr.ru)
# Copyright (C) 2007 Quinn Storm

import os

from gi.repository import GObject, GLib, Gtk, Gdk
from gi.repository import Pango
import weakref

from ccm.Constants import *
try:
    from html import escape as html_escape
except ImportError:
    from cgi import escape as html_escape
import operator
import itertools

import locale
import gettext
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("ccsm", DataDir + "/locale")
gettext.textdomain("ccsm")
_ = gettext.gettext

GLIB_VERSION = (GLib.MAJOR_VERSION, GLib.MINOR_VERSION, GLib.MICRO_VERSION)
GTK_VERSION = (Gtk.MAJOR_VERSION, Gtk.MINOR_VERSION, Gtk.MICRO_VERSION)

# Create GtkBox's in Gtk2 in the same manner.
if GTK_VERSION < (3, 0, 0):
    gtk_box_real = Gtk.Box
    class gtk_box (gtk_box_real):
        def __init__ (self, orientation=None, *args, **kwargs):
            gtk_box_real.__init__ (self, *args, **kwargs)
            if orientation:
                gtk_box_real.set_orientation(self, orientation)

        def new(*args, **kwargs):
            return Gtk.Box(*args, **kwargs)
    Gtk.Box = gtk_box

def gtk_process_events ():
    while Gtk.events_pending ():
        Gtk.main_iteration ()

IconTheme = Gtk.IconTheme.get_default()
try:
    for dir in IconDir:
        if GLib.file_test(dir, GLib.FileTest.IS_DIR) and \
           dir not in IconTheme.get_search_path():
            IconTheme.prepend_search_path(dir)
except (AttributeError, NameError, TypeError):
    for dir in IconDir:
        if GLib.file_test(dir, GLib.FileTest.IS_DIR):
            IconTheme.prepend_search_path(dir)

def protect_pango_markup (str_, quote=True):
    return html_escape(str_, quote) if str_ else ""

def protect_markup_dict (dict_):
    return dict((k, protect_pango_markup (v)) for (k, v) in dict_.items())

class Image (Gtk.Image):

    def __init__ (self, name = None, type = ImageNone, size = 32,
                  useMissingImage = False):
        Gtk.Image.__init__ (self)

        if not name:
            return

        if useMissingImage:
            self.set_from_icon_name ("image-missing",
                                     Gtk.IconSize.LARGE_TOOLBAR)
            return

        try:
            pixbuf = None

            if type == ImagePlugin:
                name = "plugin-" + name
                try:
                    pixbuf = IconTheme.load_icon (name, size, 0)
                except GLib.GError:
                    pixbuf = IconTheme.load_icon ("plugin-unknown", size, 0)

            elif type == ImageCategory:
                name = "plugins-" + name
                try:
                    pixbuf = IconTheme.load_icon (name, size, 0)
                except GLib.GError:
                    pixbuf = IconTheme.load_icon ("plugins-unknown", size, 0)

            elif type == ImageThemed:
                pixbuf = IconTheme.load_icon (name, size,
                                              Gtk.IconLookupFlags.USE_BUILTIN)

            self.set_from_pixbuf (pixbuf)
        except GLib.GError:
            self.set_from_icon_name ("image-missing", Gtk.IconSize.BUTTON)

class ActionImage (Gtk.Box):

    map = {
            "keyboard"  : "input-keyboard",
            "button"    : "input-mouse",
            "edges"     : "video-display",
            "bell"      : "audio-x-generic"
          }

    def __init__ (self, action):
        Gtk.Box.__init__ (self)
        if action in self.map: action = self.map[action]
        image = Image (name = action, type = ImageThemed, size = 22)
        if GTK_VERSION >= (3, 12, 0):
            image.set_margin_end(10)
            self.add (image)
        else:
            alignment = Gtk.Alignment()
            alignment.set_padding (0, 0, 0, 10)
            alignment.add (image)
            self.add (alignment)

class SizedButton (Gtk.Button):

    minWidth = -1
    minHeight = -1

    def __init__ (self, minWidth = -1, minHeight = -1):
        super (SizedButton, self).__init__ ()
        self.minWidth = minWidth
        self.minHeight = minHeight
        if GTK_VERSION >= (3, 0, 0):
            self.set_size_request (self.minWidth, self.minHeight)
        else:
            self.connect ("size-request", self.on_size_request)
            self.connect ("expose-event", self.on_expose_event)

    if GTK_VERSION < (3, 0, 0):
        def on_size_request (self, widget, rect, data=None):
            rect.width = max (rect.width, self.minWidth)
            rect.height = max (rect.height, self.minHeight)

        def on_expose_event (self, widget, event, data=None):
            widget.queue_resize_no_redraw ()

class PrettyButton (Gtk.Button):

    _old_toplevel = None

    def __init__ (self):
        super (PrettyButton, self).__init__ ()
        self.states = {
                        "focus"   : False,
                        "pointer" : False
                      }
        self.set_size_request (200, -1)
        self.set_relief (Gtk.ReliefStyle.NONE)
        self.connect ("focus-in-event", self.update_state_in, "focus")
        self.connect ("focus-out-event", self.update_state_out, "focus")
        self.connect ("hierarchy-changed", self.hierarchy_changed)

    def hierarchy_changed (self, widget, old_toplevel):
        if old_toplevel == self._old_toplevel:
            return

        if GTK_VERSION >= (3, 0, 0):
            if not old_toplevel and self.get_state_flags () != Gtk.StateFlags.NORMAL:
                self.set_state_flags (Gtk.StateFlags.NORMAL, True)
        else:
            if not old_toplevel and self.get_state () != Gtk.StateType.NORMAL:
                self.set_state (Gtk.StateType.NORMAL)

        self._old_toplevel = old_toplevel


    def update_state_in (self, *args):
        state = args[-1]
        if GTK_VERSION >= (3, 0, 0):
            self.set_state_flags (Gtk.StateFlags.PRELIGHT, True)
        else:
            self.set_state (Gtk.StateType.PRELIGHT)
        self.states[state] = True

    def update_state_out (self, *args):
        state = args[-1]
        self.states[state] = False
        if GTK_VERSION >= (3, 0, 0):
            if True in self.states.values ():
                self.set_state_flags (Gtk.StateFlags.PRELIGHT, True)
            else:
                self.set_state_flags (Gtk.StateFlags.NORMAL, True)
        else:
            if True in self.states.values ():
                self.set_state (Gtk.StateType.PRELIGHT)
            else:
                self.set_state (Gtk.StateType.NORMAL)

class Label(Gtk.Label):
    def __init__(self, value = "", wrap = 160):
        Gtk.Label.__init__(self)
        self.set_markup(value)
        self.props.xalign = 0
        self.set_line_wrap(True)
        self.set_line_wrap_mode(Pango.WrapMode.WORD)
        self.set_max_width_chars(0)
        self.set_size_request(wrap, -1)

class NotFoundBox(Gtk.Box):
    def __init__(self, value=""):
        Gtk.Box.__init__(self)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.Warning = Gtk.Label()
        self.Markup = _("<span size=\"large\"><b>No matches found.</b> </span><span>\n\n Your filter \"<b>%s</b>\" does not match any items.</span>")
        value = protect_pango_markup(value)
        self.Warning.set_markup(self.Markup % value)
        image = Image(name="face-surprise", type=ImageThemed, size=48)

        box.pack_start(image, False, False, 0)
        box.pack_start(self.Warning, True, True, 15)
        self.pack_start(box, True, False, 0)

    def update(self, value):
        value = protect_pango_markup(value)
        self.Warning.set_markup(self.Markup % value)

class IdleSettingsParser:
    def __init__(self, context, main):
        def FilterPlugin (p):
            return not p.Initialized and p.Enabled

        self.Context = context
        self.Main = main
        self.PluginList = [p for p in self.Context.Plugins.items() if FilterPlugin(p[1])]
        nCategories = len (main.MainPage.RightWidget._boxes)
        self.CategoryLoadIconsList = list(range(3, nCategories)) # Skip the first 3
        print("Loading icons...")

        GLib.timeout_add (150, self.Wait)

    def Wait(self):
        if not self.PluginList:
            return False

        if len (self.CategoryLoadIconsList) == 0: # If we're done loading icons
            GLib.idle_add (self.ParseSettings)
        else:
            GLib.idle_add (self.LoadCategoryIcons)

        return False

    def ParseSettings(self):
        name, plugin = self.PluginList[0]

        if not plugin.Initialized:
            plugin.Update ()
            self.Main.RefreshPage(plugin)

        self.PluginList.remove (self.PluginList[0])

        GLib.timeout_add (200, self.Wait)

        return False

    def LoadCategoryIcons(self):
        from ccm.Widgets import PluginButton

        catIndex = self.CategoryLoadIconsList[0]
        pluginWindow = self.Main.MainPage.RightWidget
        categoryBox = pluginWindow._boxes[catIndex]
        for (pluginIndex, plugin) in \
            enumerate (categoryBox.get_unfiltered_plugins()):
            categoryBox._buttons[pluginIndex] = PluginButton (plugin)
        categoryBox.rebuild_grid (categoryBox._current_cols, True)
        pluginWindow.connect_buttons (categoryBox)

        self.CategoryLoadIconsList.remove (self.CategoryLoadIconsList[0])

        GLib.timeout_add (150, self.Wait)

        return False

# Updates all registered setting when they where changed through CompizConfig
class Updater:

    def __init__ (self):
        self.VisibleSettings = {}
        self.Plugins = []
        self.Block = 0

    def SetContext (self, context):
        self.Context = context

        GLib.timeout_add (2000, self.Update)

    def Append (self, widget):
        reference = weakref.ref(widget)
        setting = widget.Setting
        self.VisibleSettings.setdefault((setting.Plugin.Name, setting.Name), []).append(reference)

    def AppendPlugin (self, plugin):
        self.Plugins.append (plugin)

    def Remove (self, widget):
        setting = widget.Setting
        l = self.VisibleSettings.get((setting.Plugin.Name, setting.Name))
        if not l:
            return
        for i, ref in enumerate(list(l)):
            if ref() is widget:
                l.remove(ref)
                break

    def UpdatePlugins(self):
        for plugin in self.Plugins:
            plugin.Read()

    def UpdateSetting (self, setting):
        widgets = self.VisibleSettings.get((setting.Plugin.Name, setting.Name))
        if not widgets:
            return
        for reference in widgets:
            widget = reference()
            if widget is not None:
                widget.Read()

    def Update (self):
        if self.Block > 0:
            return True

        if self.Context.ProcessEvents():
            changed = self.Context.ChangedSettings
            if [s for s in changed if s.Plugin.Name == "core" and s.Name == "active_plugins"]:
                self.UpdatePlugins()

            for setting in list(changed):
                widgets = self.VisibleSettings.get((setting.Plugin.Name, setting.Name))
                if widgets:
                    for reference in widgets:
                        widget = reference()
                        if widget is not None:
                            widget.Read()
                            if widget.List:
                                widget.ListWidget.Read()
                changed.remove(setting)

            self.Context.ChangedSettings = changed

        return True

GlobalUpdater = Updater ()

class PluginSetting:

    def __init__ (self, plugin, widget, handler):
        self.Widget = widget
        self.Plugin = plugin
        self.Handler = handler
        GlobalUpdater.AppendPlugin (self)

    def Read (self):
        widget = self.Widget
        widget.handler_block(self.Handler)
        widget.set_active (self.Plugin.Enabled)
        widget.set_sensitive (self.Plugin.Context.AutoSort)
        widget.handler_unblock(self.Handler)

class PureVirtualError(Exception):
    pass

def SettingKeyFunc(value):
    return value.Plugin.Ranking[value.Name]

def CategoryKeyFunc(category):
    if 'General' == category:
        return ''
    else:
        return category or 'zzzzzzzz'

def GroupIndexKeyFunc(item):
    return item[1][0]

FirstItemKeyFunc = operator.itemgetter(0)

EnumSettingKeyFunc = operator.itemgetter(1)

PluginKeyFunc = operator.attrgetter('ShortDesc')

def HasOnlyType (settings, stype):
    return settings and not [s for s in settings if s.Type != stype]

def GetDefaultScreenNum():
    screen = Gdk.Screen.get_default()
    try:
        number = screen.get_screen_number()
    except AttributeError:
        number = screen.get_number()
    return number

def SetCurrentScreenNum(number):
    SetCurrentScreenNum.value = number
SetCurrentScreenNum.value = -1

def GetCurrentScreenNum():
    number = SetCurrentScreenNum.value
    if number < 0:
        number = GetDefaultScreenNum()
    return number

def GetScreenNums():
    screens = []
    nScreens = max(GetDefaultScreenNum(), GetCurrentScreenNum()) + 1
    display = Gdk.Display.get_default()
    if GTK_VERSION >= (3, 10, 0):
        Gdk.error_trap_push()
        try:
            import Xlib.display
            xdisplay = Xlib.display.Display(display.get_name())
            nScreens = xdisplay.screen_count()
        except:
            pass
        Gdk.error_trap_pop_ignored()
    else:
        nScreens = display.get_n_screens()
    for s in range(nScreens):
        screens.append(s)
    return screens

def GetSettings(group, types=None):

    def TypeFilter (settings, types):
         for setting in settings:
            if setting.Type in types:
                yield setting

    # Compiz 0.9.x and Compiz 0.8.x compatibility.
    try:
        screen = iter(group.Screen.values())
    except (AttributeError, TypeError):
        screenNum = GetCurrentScreenNum()
        screen = itertools.chain(iter(group.Screens[screenNum].values()),
                                 iter(group.Display.values()))

    if types:
        screen = TypeFilter(screen, types)
    return screen

def GetAcceleratorName(key, mods):
    accel = Gtk.accelerator_name(key, mods)

    for mod in KeyModifier:
        if "%s_L" % mod in accel:
            accel = accel.replace ("%s_L" % mod, "<%s>" % mod)
        if "%s_R" % mod in accel:
            accel = accel.replace ("%s_R" % mod, "<%s>" % mod)
    accel = Gtk.accelerator_name(*Gtk.accelerator_parse(accel))

    for alias in KeyModifierAlias:
        accel = accel.replace("<%s>" % alias[0], "<%s>" % alias[1])
    return accel

def UpdateAcceleratorName (accel):
    if accel.lower ().strip () in ("disabled", "none"):
        accel = ""

    keys = [key for key in KeyModifier if key in accel]
    keys.extend([key[1] for key in KeyModifierAlias if key[0] in accel])
    keys.sort()

    # Get all keys in the order with Gtk::accelerator_name().
    accel = GetAcceleratorName (*Gtk.accelerator_parse (accel))

    # Prepend all additional keys not recognized by it.
    for key in set (keys):
        if key not in accel:
            accel = "<%s>%s" % (key, accel)
    return accel

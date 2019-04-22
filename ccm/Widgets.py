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
# Authors: Quinn Storm (livinglatexkali@gmail.com)
#          Patrick Niklaus (patrick.niklaus@student.kit.edu)
#          Guillaume Seguin (guillaume@segu.in)
#          Christopher Williams (christopherw@verizon.net)
#          Sorokin Alexei (sor.alexei@meowr.ru)
#          Wolfgang Ulbrich (chat-to-me@raveit.de)
# Copyright (C) 2007 Quinn Storm

from gi.repository import GObject, GLib, Gtk
from gi.repository import Gdk, GdkPixbuf, PangoCairo
import cairo
from collections import OrderedDict
from math import pi, sqrt
import time
import re
import os
import subprocess
import sys
import mimetypes
mimetypes.init()

from ccm.Utils import *
from ccm.Constants import *
from ccm.Conflicts import *

import locale
import gettext
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("ccsm", DataDir + "/locale")
gettext.textdomain("ccsm")
_ = gettext.gettext

#
# Try to use gtk like coding style for consistency
#

class FallbackStack(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self._named_children = {}
        self._visible_child = None

    def add_named(self, child, name):
        if name in self._named_children.items():
            c = self._named_children[name]
            if c is not child:
                self.remove(c)
        self._named_children[name] = child
        self.pack_start(child, True, True, 0)

    def _show_chosen_child(self):
        for n, c in self._named_children.items():
            if n == self._visible_child:
                c.show_all()
            else:
                c.hide()

    def set_visible_child(self, child):
        for n, c in self._named_children():
            if c is child:
                self._visible_child = n
                c.show_all()
            else:
                c.hide()

    def set_visible_child_name(self, name):
        if name not in self._named_children:
            return
        self._visible_child = name
        self._show_chosen_child()

    def get_visible_child_name(self):
        return self._visible_child

    def get_visible_child(self):
        return self._named_children.get(self._visible_child)

class ClearEntry(Gtk.Entry):
    def __init__(self):
        Gtk.Entry.__init__(self)
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                     "edit-clear")
        self.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("Clear"))
        self.connect('icon-press', self._clear_pressed)

    def _clear_pressed(self, widget, pos, event):
        if pos == Gtk.EntryIconPosition.SECONDARY:
            self.set_text("")

# Cell Renderer for MultiList

class CellRendererColor(Gtk.CellRenderer):
    if GLIB_VERSION >= (2, 42, 0):
        __gproperties__ = {
            'text': (GObject.TYPE_STRING,
                    'color markup text',
                    'The color as markup like this: #rrrrggggbbbbaaaa',
                    '#0000000000000000',
                    GObject.ParamFlags.READWRITE)
        }
    else:
        __gproperties__ = {
            'text': (GObject.TYPE_STRING,
                    'color markup text',
                    'The color as markup like this: #rrrrggggbbbbaaaa',
                    '#0000000000000000',
                    GObject.PARAM_READWRITE)
       }

    _text  = '#0000000000000000'
    _color = [0, 0, 0, 0]
    _surface = None
    _surface_size = (-1, -1)

    def __init__(self):
        Gtk.CellRenderer.__init__(self)

    def _parse_color(self):
        if GTK_VERSION >= (3, 0, 0):
            color = Gdk.RGBA()
            color.parse(self._text[:-4])
            color.alpha = int("0x%s" % self._text[-4:], base=16) / 65535.0
            self._color = [color.red, color.green, color.blue, color.alpha]
        else:
            color = Gdk.color_parse(self._text[:-4])
            alpha = int("0x%s" % self._text[-4:], base=16)
            self._color = [color.red / 65535.0, color.green / 65535.0,
                           color.blue / 65535.0, alpha / 65535.0]

    def do_set_property(self, property, value):
        if property.name == 'text':
            self._text = value
            self._parse_color()
        else:
            raise AttributeError("unknown property %s" % property.name)

    def do_get_property(self, property):
        if property.name == 'text':
            return self._text
        else:
            raise AttributeError("unknown property %s" % property.name)

    if GTK_VERSION < (3, 0, 0):
        def do_get_size(self, widget, cell_area):
            return (0, 0, 0, 0) # FIXME

    def redraw(self, width, height):
        # found in gtk-color-button.c
        CHECK_SIZE  = 4
        CHECK_DARK  = 21845 # 65535 / 3
        CHECK_LIGHT = 43690

        width += 10
        height += 10
        self._surface_size = (width, height)
        self._surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(self._surface)

        x = 0
        y = 0
        colors = [CHECK_DARK, CHECK_LIGHT]
        state = 0
        begin_state = 0
        while y < height:
            while x < width:
                cr.rectangle(x, y, CHECK_SIZE, CHECK_SIZE)
                c = colors[state] / 65535.0
                cr.set_source_rgb(c, c, c)
                cr.fill()
                x += CHECK_SIZE
                state = not state
            state = not begin_state
            begin_state = state
            x = 0
            y += CHECK_SIZE

    def _render(self, cr, widget, background_area, cell_area, flags):
        height, width = (cell_area.height, cell_area.width)
        sheight, swidth = self._surface_size
        if height > sheight or width > swidth:
            self.redraw(width, height)

        padding = 1
        cr.rectangle(cell_area.x + padding, cell_area.y + padding,
                     width - (padding * 2), height - (padding * 2))
        cr.clip()

        cr.set_source_surface(self._surface, cell_area.x, cell_area.y)
        cr.paint()

        cr.set_source_rgba(*self._color)
        cr.paint()

    if GTK_VERSION >= (3, 0, 0):
        def do_render(self, *args, **kwargs):
            self._render(*args, **kwargs)
    else:
        def do_render(self, window, widget, background_area, cell_area, expose_area, flags):
            cr = window.cairo_create()
            Gdk.cairo_rectangle(cr, expose_area)
            cr.clip()
            self._render(cr, widget, background_area, cell_area, flags)

class PluginView(Gtk.TreeView):
    def __init__(self, plugins):
        liststore = Gtk.ListStore(str, GdkPixbuf.Pixbuf, bool, object)
        self.model = liststore.filter_new()
        Gtk.TreeView.__init__(self, model=self.model)

        self.SelectionHandler = None

        self.Plugins = set(plugins)

        for plugin in sorted(plugins.values(), key=PluginKeyFunc):
            liststore.append([plugin.ShortDesc, Image(plugin.Name, type=ImagePlugin).props.pixbuf,
                plugin.Enabled, plugin])

        column = Gtk.TreeViewColumn(_('Plugin'), Gtk.CellRendererPixbuf(), pixbuf=1, sensitive=2)
        self.insert_column(column, 0)
        cell = Gtk.CellRendererText()
        cell.props.wrap_width = 200
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
        self.model.set_visible_func(self.VisibleFunc, None)
        self.get_selection().connect('changed', self.SelectionChanged)

    def VisibleFunc(self, model, iter, data=None):
        return model[iter][3].Name in self.Plugins

    def Filter(self, plugins):
        self.Plugins = set(plugins)
        self.model.refilter()

    def SelectionChanged(self, selection):
        model, iter = selection.get_selected()
        if iter is None:
            return self.SelectionHandler(None)

        return self.SelectionHandler(model[iter][3])

class GroupView(Gtk.TreeView):
    def __init__(self, name):
        self.model = Gtk.ListStore(str, str)
        Gtk.TreeView.__init__(self, model=self.model)

        self.SelectionHandler = None

        self.Visible = set()

        cell = Gtk.CellRendererText()
        cell.props.ypad = 5
        cell.props.wrap_width = 200
        column = Gtk.TreeViewColumn(name, cell, text=0)
        self.append_column(column)

        self.get_selection().connect('changed', self.SelectionChanged)
        self.hide()
        self.set_no_show_all(True)

    def Update(self, items):
        self.model.clear()

        self.model.append([_('All'), 'All'])

        length = 0
        for item in items:
            self.model.append([item or _("General"), item])
            if item: # exclude "General" from count
                length += 1

        if length:
            self.show_all()
            self.set_no_show_all(False)
        else:
            self.hide()
            self.set_no_show_all(True)

    def SelectionChanged(self, selection):
        model, iter = selection.get_selected()
        if iter is None:
            return None

        return self.SelectionHandler(model[iter][1])

# Selector Buttons
#
class SelectorButtons(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        if GTK_VERSION >= (3, 0, 0):
            self.props.margin = 10
        else:
            self.set_border_width(10)
        self.set_spacing(5)
        self.buttons = []
        self.arrows = []

    def clear_buttons(self):
        for widget in (self.arrows + self.buttons):
            widget.destroy()

        self.arrows = []
        self.buttons = []

    def add_button(self, label, callback):
        try:
            arrow = Gtk.Arrow(arrow_type=Gtk.ArrowType.RIGHT, shadow_type=Gtk.ShadowType.NONE)
        except (AttributeError, TypeError):
            arrow = Gtk.Arrow()
            arrow.set(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE)
        button = Gtk.Button(label=label)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.connect('clicked', self.on_button_clicked, callback)
        if self.get_children():
            self.pack_start(arrow, False, False, 0)
            self.arrows.append(arrow)
        self.pack_start(button, False, False, 0)
        self.buttons.append(button)
        self.show_all()

    def remove_button(self, pos):
        if pos > len(self.buttons)-1:
            return
        self.buttons[pos].destroy()
        self.buttons.remove(self.buttons[pos])
        if pos > 0:
            self.arrows[pos-1].destroy()
            self.arrows.remove(self.arrows[pos-1])

    def on_button_clicked(self, widget, callback):
        callback(selector=True)

# Scrolled List
#
class ScrolledList(Gtk.ScrolledWindow):
    def __init__(self, name):
        Gtk.ScrolledWindow.__init__(self)

        self.props.hscrollbar_policy = Gtk.PolicyType.NEVER
        self.props.vscrollbar_policy = Gtk.PolicyType.AUTOMATIC

        self.store = Gtk.ListStore(GObject.TYPE_STRING)

        self.view = Gtk.TreeView(model=self.store)
        self.view.set_headers_visible(True)
        self.view.insert_column(Gtk.TreeViewColumn(name, Gtk.CellRendererText(), text=0), -1)

        self.set_size_request(300, 300)

        self.add(self.view)

        self.select = self.view.get_selection()
        self.select.set_mode(Gtk.SelectionMode.SINGLE)

    def get_list(self):
        values = []
        iter = self.store.get_iter_first()
        while iter:
            value = self.store.get(iter, 0)[0]
            if value != "":
                values.append(value)
            iter = self.store.iter_next(iter)
        return values

    def clear(self):
        self.store.clear()

    def append(self, value):
        iter = self.store.append()
        self.store.set_value(iter, 0, value)

    def set(self, pos, value):
        iter = self.store.get_iter(pos)
        self.store.set_value(iter, 0, value)

    def delete(self, b):
        selected_rows = self.select.get_selected_rows()[1]
        for path in selected_rows:
            iter = self.store.get_iter(path)
            self.store.remove(iter)

    def move_up(self, b):
        selected_rows = self.select.get_selected_rows()[1]
        if len(selected_rows) == 1:
            iter = self.store.get_iter(selected_rows[0])
            prev = self.store.get_iter_first()
            if not self.store.get_path(prev) == self.store.get_path(iter):
                while prev is not None and not self.store.get_path(self.store.iter_next(prev)) == self.store.get_path(iter):
                    prev = self.store.iter_next(prev)
                self.store.swap(iter, prev)

    def move_down(self, b):
        selected_rows = self.select.get_selected_rows()[1]
        if len(selected_rows) == 1:
            iter = self.store.get_iter(selected_rows[0])
            next = self.store.iter_next(iter)
            if next is not None:
                self.store.swap(iter, next)

# Button modifier selection widget
#
class ModifierSelector (Gtk.DrawingArea):

    __gsignals__    = {"added" : (GObject.SignalFlags.RUN_FIRST,
                                  None, [GObject.TYPE_STRING]),
                       "removed" : (GObject.SignalFlags.RUN_FIRST,
                                    None, [GObject.TYPE_STRING])}

    _current = []

    _base_pixbuf = None
    _surface     = None

    _x0     = 0
    _y0     = 12
    _width  = 100
    _height = 50

    _font   = "Sans 12 Bold"

    def __init__ (self, mods):
        '''Prepare widget'''
        super (ModifierSelector, self).__init__ ()
        self._current = mods.split ("|")
        self._base_pixbuf = Image ("modifier", ImageInternal, -1).get_pixbuf ()
        self.add_events (Gdk.EventMask.BUTTON_PRESS_MASK)
        if GTK_VERSION >= (3, 0, 0):
            self.connect ("draw", self.draw_event)
        else:
            self.connect ("expose-event", self.draw_event)
        self.connect ("button-press-event", self.button_press)
        self.set_size_request (200, 3 * (self._height + 10))

        x0, y0, width, height = self._x0, self._y0, self._width, self._height
        self._modifiers = {
            "Shift"     : (x0, y0),
            "Control"   : (x0, y0 + height),
            "Super"     : (x0 + width, y0),
            "Alt"       : (x0 + width, y0 + height),
            "Meta"      : (x0, y0 + 2 * height),
            "Hyper"     : (x0 + width, y0 + 2 * height)
        }

        self._names = {
            "Control"   : "Ctrl"
        }

    def set_current (self, value):
        self._current = value.split ("|")
        self.redraw (queue = True)

    def get_current (self):
        return "|".join ([s for s in self._current if len (s) > 0])
    current = property (get_current, set_current)

    def draw (self, cr, width, height):
        '''The actual drawing function'''
        for mod in self._modifiers:
            x, y = self._modifiers[mod]
            if mod in self._names: text = self._names[mod]
            else: text = mod
            Gdk.cairo_set_source_pixbuf (cr, self._base_pixbuf, x, y)
            cr.rectangle (x, y, self._width, self._height)
            cr.fill_preserve ()
            if mod in self._current:
                cr.set_source_rgb (0.3, 0.3, 0.3)
                self.write (cr, x + 23, y + 15, text)
                cr.set_source_rgb (0.5, 1, 0)
            else:
                cr.set_source_rgb (0, 0, 0)
            self.write (cr, x + 22, y + 14, text)

    def write (self, cr, x, y, text):
        cr.move_to (x, y)
        markup = '''<span font_desc="%s">%s</span>''' % (self._font, text)
        layout = PangoCairo.create_layout (cr)
        try:
            layout.set_markup (markup)
        except (AttributeError, TypeError):
            layout.set_markup (markup, -1)
        PangoCairo.show_layout (cr, layout)

    def redraw (self, queue = False):
        '''Redraw internal surface'''
        alloc = self.get_allocation ()
        # Prepare drawing surface
        width, height = alloc.width, alloc.height
        self._surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context (self._surface)
        # Clear
        cr.set_operator (cairo.OPERATOR_CLEAR)
        cr.paint ()
        cr.set_operator (cairo.OPERATOR_OVER)
        # Draw
        self.draw (cr, alloc.width, alloc.height)
        # Queue expose event if required
        if queue:
            self.queue_draw ()

    def draw_event (self, widget, data):
        '''Draw event handler'''
        if GTK_VERSION >= (3, 0, 0):
            cr = data
        else:
            event = data
            cr = event.window.cairo_create ()
        if not self._surface:
            self.redraw ()
        cr.set_source_surface (self._surface)
        if GTK_VERSION < (3, 0, 0):
            cr.rectangle (event.area.x, event.area.y,
                          event.area.width, event.area.height)
            cr.clip ()
        cr.paint ()
        return False

    def in_rect (self, x, y, x0, y0, x1, y1):
        return x >= x0 and y >= y0 and x <= x1 and y <= y1

    def button_press (self, widget, event):
        x, y = event.x, event.y
        mod = ""

        for modifier in self._modifiers:
            x0, y0 = self._modifiers[modifier]
            if self.in_rect (x, y, x0, y0,
                             x0 + self._width, y0 + self._height):
                mod = modifier
                break

        if not len (mod):
            return
        if mod in self._current:
            self._current.remove (mod)
            self.emit ("removed", mod)
        else:
            self._current.append (mod)
            self.emit ("added", mod)
        self.redraw (queue = True)

# Edge selection widget
#
class EdgeSelector (Gtk.DrawingArea):

    __gsignals__    = {"clicked" : (GObject.SignalFlags.RUN_FIRST,
                                    None, (GObject.TYPE_STRING, GObject.TYPE_PYOBJECT,))}

    _base_pixbuf = None
    _surface     = None
    _radius      = 13
    _cradius     = 20
    _coords      = []

    def __init__ (self):
        '''Prepare widget'''
        super (EdgeSelector, self).__init__ ()
        self._base_pixbuf = Image ("display", ImageInternal, -1).get_pixbuf ()
        self.add_events (Gdk.EventMask.BUTTON_PRESS_MASK)
        if GTK_VERSION >= (3, 0, 0):
            self.connect ("draw", self.draw_event)
        else:
            self.connect ("expose-event", self.draw_event)
        self.connect ("button-press-event", self.button_press)
        self.set_size_request (196, 196)

        # Useful vars
        x0 = 16
        y0 = 24
        x1 = 181
        y1 = 133
        x2 = x0 + 39
        y2 = y0 + 26
        x3 = x1 - 39
        y3 = y1 - 26
        self._coords = (x0, y0, x1, y1, x2, y2, x3, y3)

    def draw (self, cr, width, height):
        '''The actual drawing function'''
        # Useful vars
        x0, y0, x1, y1, x2, y2, x3, y3 = self._coords
        cradius = self._cradius
        radius  = self._radius

        cr.set_line_width(1.0)

        # Top left edge
        cr.new_path ()
        cr.move_to (x0, y0 + cradius)
        cr.line_to (x0, y0)
        cr.line_to (x0 + cradius, y0)
        cr.arc (x0, y0, cradius, 0, pi / 2)
        cr.close_path ()
        self.set_fill_color (cr, "TopLeft")
        cr.fill_preserve ()
        self.set_stroke_color (cr, "TopLeft")
        cr.stroke ()
        # Top right edge
        cr.new_path ()
        cr.move_to (x1, y0 + cradius)
        cr.line_to (x1, y0)
        cr.line_to (x1 - cradius, y0)
        cr.arc_negative (x1, y0, cradius, pi, pi/2)
        cr.close_path ()
        self.set_fill_color (cr, "TopRight")
        cr.fill_preserve ()
        self.set_stroke_color (cr, "TopRight")
        cr.stroke ()
        # Bottom left edge
        cr.new_path ()
        cr.move_to (x0, y1 - cradius)
        cr.line_to (x0, y1)
        cr.line_to (x0 + cradius, y1)
        cr.arc_negative (x0, y1, cradius, 2 * pi, 3 * pi / 2)
        cr.close_path ()
        self.set_fill_color (cr, "BottomLeft")
        cr.fill_preserve ()
        self.set_stroke_color (cr, "BottomLeft")
        cr.stroke ()
        # Bottom right edge
        cr.new_path ()
        cr.move_to (x1, y1 - cradius)
        cr.line_to (x1, y1)
        cr.line_to (x1 - cradius, y1)
        cr.arc (x1, y1, cradius, pi, 3 * pi / 2)
        cr.close_path ()
        self.set_fill_color (cr, "BottomRight")
        cr.fill_preserve ()
        self.set_stroke_color (cr, "BottomRight")
        cr.stroke ()
        # Top edge
        cr.new_path ()
        cr.move_to (x2 + radius, y0)
        cr.line_to (x3 - radius, y0)
        cr.arc (x3 - radius, y0, radius, 0, pi / 2)
        cr.line_to (x2 + radius, y0 + radius)
        cr.arc (x2 + radius, y0, radius, pi / 2, pi)
        cr.close_path ()
        self.set_fill_color (cr, "Top")
        cr.fill_preserve ()
        self.set_stroke_color (cr, "Top")
        cr.stroke ()
        # Bottom edge
        cr.new_path ()
        cr.move_to (x2 + radius, y1)
        cr.line_to (x3 - radius, y1)
        cr.arc_negative (x3 - radius, y1, radius, 0, - pi / 2)
        cr.line_to (x2 + radius, y1 - radius)
        cr.arc_negative (x2 + radius, y1, radius, - pi / 2, pi)
        cr.close_path ()
        self.set_fill_color (cr, "Bottom")
        cr.fill_preserve ()
        self.set_stroke_color (cr, "Bottom")
        cr.stroke ()
        # Left edge
        cr.new_path ()
        cr.move_to (x0, y2 + radius)
        cr.line_to (x0, y3 - radius)
        cr.arc_negative (x0, y3 - radius, radius, pi / 2, 0)
        cr.line_to (x0 + radius, y2 + radius)
        cr.arc_negative (x0, y2 + radius, radius, 0, 3 * pi / 2)
        cr.close_path ()
        self.set_fill_color (cr, "Left")
        cr.fill_preserve ()
        self.set_stroke_color (cr, "Left")
        cr.stroke ()
        # Right edge
        cr.new_path ()
        cr.move_to (x1, y2 + radius)
        cr.line_to (x1, y3 - radius)
        cr.arc (x1, y3 - radius, radius, pi / 2, pi)
        cr.line_to (x1 - radius, y2 + radius)
        cr.arc (x1, y2 + radius, radius, pi, 3 * pi / 2)
        cr.close_path ()
        self.set_fill_color (cr, "Right")
        cr.fill_preserve ()
        self.set_stroke_color (cr, "Right")
        cr.stroke ()

    def set_fill_color (self, cr, edge):
        '''Set painting color for edge'''
        cr.set_source_rgb (0.9, 0.9, 0.9)

    def set_stroke_color (self, cr, edge):
        '''Set stroke color for edge'''
        cr.set_source_rgb (0.45, 0.45, 0.45)

    def redraw (self, queue = False):
        '''Redraw internal surface'''
        alloc = self.get_allocation ()
        # Prepare drawing surface
        width, height = alloc.width, alloc.height
        self._surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context (self._surface)
        # Draw background
        Gdk.cairo_set_source_pixbuf (cr, self._base_pixbuf, 0, 0)
        cr.paint ()
        # Draw
        self.draw (cr, alloc.width, alloc.height)
        # Queue expose event if required
        if queue:
            self.queue_draw ()

    def draw_event (self, widget, data):
        '''Draw event handler'''
        if GTK_VERSION >= (3, 0, 0):
            cr = data
        else:
            event = data
            cr = event.window.cairo_create ()
        if not self._surface:
            self.redraw ()
        cr.set_source_surface (self._surface)
        if GTK_VERSION < (3, 0, 0):
            cr.rectangle (event.area.x, event.area.y,
                          event.area.width, event.area.height)
            cr.clip ()
        cr.paint ()
        return False

    def in_circle_quarter (self, x, y, x0, y0, x1, y1, x2, y2, radius):
        '''Args:
            x, y = point coordinates
            x0, y0 = center coordinates
            x1, y1 = circle square top left coordinates
            x2, y2 = circle square bottom right coordinates
            radius = circle radius'''
        if not self.in_rect (x, y, x1, y1, x2, y2):
            return False
        return self.dist (x, y, x0, y0) <= radius

    def dist (self, x1, y1, x2, y2):
        return sqrt ((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def in_rect (self, x, y, x0, y0, x1, y1):
        return x >= x0 and y >= y0 and x <= x1 and y <= y1

    def button_press (self, widget, event):
        x, y = event.x, event.y
        edge = ""

        # Useful vars
        x0, y0, x1, y1, x2, y2, x3, y3 = self._coords
        cradius = self._cradius
        radius  = self._radius

        if self.in_circle_quarter (x, y, x0, y0, x0, y0,
                                   x0 + cradius, y0 + cradius,
                                   cradius):
            edge = "TopLeft"
        elif self.in_circle_quarter (x, y, x1, y0, x1 - cradius, y0,
                                     x1, y0 + cradius, cradius):
            edge = "TopRight"
        elif self.in_circle_quarter (x, y, x0, y1, x0, y1 - cradius,
                                     x0 + cradius, y1, cradius):
            edge = "BottomLeft"
        elif self.in_circle_quarter (x, y, x1, y1, x1 - cradius, y1 - cradius,
                                     x1, y1, cradius):
            edge = "BottomRight"
        elif self.in_rect (x, y, x2 + radius, y0, x3 - radius, y0 + radius) \
             or self.in_circle_quarter (x, y, x2 + radius, y0, x2, y0,
                                        x2 + radius, y0 + radius, radius) \
             or self.in_circle_quarter (x, y, x3 - radius, y0, x3 - radius, y0,
                                        x3, y0 + radius, radius):
            edge = "Top"
        elif self.in_rect (x, y, x2 + radius, y1 - radius, x3 - radius, y1) \
             or self.in_circle_quarter (x, y, x2 + radius, y1, x2, y1 - radius,
                                        x2 + radius, y1, radius) \
             or self.in_circle_quarter (x, y, x3 - radius, y1,
                                        x3 - radius, y1 - radius,
                                        x3, y1, radius):
            edge = "Bottom"
        elif self.in_rect (x, y, x0, y2 + radius, x0 + radius, y3 - radius) \
             or self.in_circle_quarter (x, y, x0, y2 + radius, x0, y2,
                                        x0 + radius, y2 + radius, radius) \
             or self.in_circle_quarter (x, y, x0, y3 - radius,
                                        x0, y3 - radius,
                                        x0 + radius, y3, radius):
            edge = "Left"
        elif self.in_rect (x, y, x1 - radius, y2 + radius, x1, y3 - radius) \
             or self.in_circle_quarter (x, y, x1, y2 + radius, x1 - radius, y2,
                                        x1, y2 + radius, radius) \
             or self.in_circle_quarter (x, y, x1, y3 - radius,
                                        x1 - radius, y3 - radius,
                                        x1, y3, radius):
            edge = "Right"

        if edge:
            self.emit ("clicked", edge, event)

# Edge selection widget
#
class SingleEdgeSelector (EdgeSelector):

    _current = []

    def __init__ (self, edge):
        '''Prepare widget'''
        EdgeSelector.__init__ (self)
        self._current = edge.split ("|")
        self.connect ('clicked', self.edge_clicked)

    def set_current (self, value):
        self._current = value.split ("|")
        self.redraw (queue = True)

    def get_current (self):
        return "|".join ([s for s in self._current if len (s) > 0])
    current = property (get_current, set_current)

    def set_fill_color (self, cr, edge):
        '''Set painting color for edge'''
        if edge in self._current:
            cr.set_source_rgb (0.64, 1.0, 0.09)
        else:
            cr.set_source_rgb (0.80, 0.00, 0.00)

    def set_stroke_color (self, cr, edge):
        '''Set stroke color for edge'''
        if edge in self._current:
            cr.set_source_rgb (0.31, 0.60, 0.02)
        else:
            cr.set_source_rgb (0.64, 0.00, 0.00)

    def edge_clicked (self, widget, edge, event):
        if not len (edge):
            return
        if edge in self._current:
            self._current.remove (edge)
        else:
            self._current.append (edge)

        self.redraw (queue = True)

# Global Edge Selector
#
class GlobalEdgeSelector(EdgeSelector):

    _settings = []
    _edges = {}
    _text  = {}
    _context = None

    def __init__ (self, context, settings=[]):
        EdgeSelector.__init__ (self)

        self._context = context
        self._settings = settings

        self.connect ("clicked", self.show_popup)

        if len (settings) <= 0:
            self.generate_setting_list ()

    def set_fill_color (self, cr, edge):
        '''Set painting color for edge'''
        if edge in self._edges:
            cr.set_source_rgb (0.64, 1.0, 0.09)
        else:
            cr.set_source_rgb (0.80, 0.00, 0.00)

    def set_stroke_color (self, cr, edge):
        '''Set stroke color for edge'''
        if edge in self._edges:
            cr.set_source_rgb (0.31, 0.60, 0.02)
        else:
            cr.set_source_rgb (0.64, 0.00, 0.00)

    def set_settings (self, value):
        self._settings = value

    def get_settings (self):
        return self._settings
    settings = property (get_settings, set_settings)

    def generate_setting_list (self):
        self._settings = []

        def filter_settings(plugin):
            if plugin.Enabled:
                settings = sorted (GetSettings(plugin), key=SettingKeyFunc)
                settings = [s for s in settings if s.Type == 'Edge']
                return settings
            return []

        for plugin in self._context.Plugins.values ():
            self._settings += filter_settings (plugin)

        for setting in self._settings:
            edges = setting.Value.split ("|")
            for edge in edges:
                self._edges[edge] = setting

    def set_edge_setting (self, setting, edge):
        if not setting:
            if edge in self._edges:
                self._edges.pop(edge)
            for setting in self._settings:
              value = setting.Value.split ("|")
              if edge in value:
                value.remove(edge)
                value = "|".join ([s for s in value if len (s) > 0])
                setting.Value = value
        else:
            value = setting.Value.split ("|")
            if not edge in value:
                value.append (edge)
            value = "|".join ([s for s in value if len (s) > 0])

            conflict = EdgeConflict (self.get_toplevel (), setting, value,
                                     settings=self._settings,
                                     autoResolve=True)
            if conflict.Resolve (GlobalUpdater):
                setting.Value = value
                self._edges[edge] = setting

        self._context.Write()
        self.redraw (queue = True)

    def show_popup (self, widget, edge, event):
        self._text = {}
        comboBox = Gtk.ComboBoxText.new ()

        comboBox.append_text (_("None"))
        comboBox.set_active (0)
        i = 1
        for setting in self._settings:
            text = "%s: %s" % (setting.Plugin.ShortDesc, setting.ShortDesc)
            comboBox.append_text (text)
            self._text[text] = setting

            if edge in setting.Value.split ("|"):
                comboBox.set_active (i)
            i += 1

        comboBox.set_size_request (200, -1)
        comboBox.connect ('changed', self.combo_changed, edge)

        popup = Popup (parent=widget, child=comboBox, decorated=False,
                       mouse=True, modal=False)
        comboBox.show ()
        popup.show ()
        popup.connect ('focus-out-event', self.focus_out)

    def focus_out (self, widget, event):
        combo = widget.get_child ()
        if combo.props.popup_shown:
            return
        gtk_process_events ()
        widget.destroy ()

    def combo_changed (self, widget, edge):
        try:
            text = widget.do_get_active_text (widget)
        except (AttributeError, NameError, TypeError):
            text = widget.get_active_text ()
        setting = None
        if text != _("None"):
            setting = self._text[text]
        self.set_edge_setting (setting, edge)
        popup = widget.get_parent ()
        popup.destroy ()

# Popup
#
class Popup (Gtk.Window):

    def __init__ (self, parent=None, text=None, child=None, decorated=True, mouse=False, modal=True):
        Gtk.Window.__init__ (self, type=Gtk.WindowType.TOPLEVEL)
        self.set_type_hint (Gdk.WindowTypeHint.UTILITY)
        self.set_position (mouse and Gtk.WindowPosition.MOUSE or Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_default_size (0, 0)
        if parent:
            self.set_transient_for (parent.get_toplevel ())
        self.set_modal (modal)
        self.set_decorated (decorated)
        self.set_skip_taskbar_hint (modal)
        self.set_destroy_with_parent (True)

        if text:
            label = Gtk.Label (label=text)
            if GTK_VERSION >= (3, 0, 0):
                label.props.margin = 20
                child = label
            else:
                alignment = Gtk.Alignment ()
                alignment.set_padding (20, 20, 20, 20)
                alignment.add (label)
                label.show ()
                child = alignment

        if child:
            self.add (child)
            child.show ()

        gtk_process_events ()

    def destroy (self):
        Gtk.Window.destroy (self)
        gtk_process_events ()

# Key Grabber
#
class KeyGrabber (Gtk.Button):

    __gsignals__    = {"changed" : (GObject.SignalFlags.RUN_FIRST,
                                    None,
                                    ()),
                       "current-changed" : (GObject.SignalFlags.RUN_FIRST,
                                    None,
                                    ())}

    key     = 0
    mods    = Gdk.ModifierType.SHIFT_MASK
    handler = None
    popup   = None

    label   = None
    widget_mapped = False

    def __init__ (self, key = 0, mods = Gdk.ModifierType.SHIFT_MASK, label = None):
        '''Prepare widget'''
        super (KeyGrabber, self).__init__ ()

        self.key = key
        self.mods = mods

        self.label = label

        self.connect ("clicked", self.begin_key_grab)
        self.set_label ()

    def begin_key_grab (self, widget):
        self.popup_mapped = False
        def on_widget_map_event (widget, event, data=None):
            self.popup_mapped = True
            widget.disconnect_by_func (on_widget_map_event)

        self.popup = Popup (parent=widget,
                            text=_("Please press the new key combination"))
        self.popup.add_events (Gdk.EventMask.KEY_PRESS_MASK)

        # Wait until the popup is fully shown.
        self.handler = self.popup.connect ("map-event", on_widget_map_event)
        self.popup.show ()
        while not self.popup_mapped:
            Gtk.main_iteration ()
        self.popup_mapped = False

        self.handler = self.popup.connect ("key-press-event",
                                           self.on_key_press_event)

        self.popup.present ()

        if GTK_VERSION >= (3, 20, 0):
            self.seat = self.popup.get_display ().get_default_seat ()
            while True:
                ret = self.seat.grab (self.popup.get_window (),
                                      Gdk.SeatCapabilities.KEYBOARD, False,
                                      None, None, None, None)
                if ret == Gdk.GrabStatus.SUCCESS:
                    break
                time.sleep (0.1)
        else:
            while True:
                ret = Gdk.keyboard_grab (self.popup.get_window (), False,
                                         Gdk.CURRENT_TIME)
                if ret == Gdk.GrabStatus.SUCCESS:
                    break
                time.sleep (0.1)

    def end_key_grab (self):
        if GTK_VERSION >= (3, 20, 0):
            self.seat.ungrab ()
        else:
            Gdk.keyboard_ungrab (Gtk.get_current_event_time ())
        self.popup.disconnect (self.handler)
        self.popup.destroy ()

    def on_key_press_event (self, widget, event):
        mods = event.get_state() & Gdk.ModifierType(Gtk.accelerator_get_default_mod_mask())

        if event.keyval in (Gdk.KEY_Escape, Gdk.KEY_Return) \
            and not mods:
            if event.keyval == Gdk.KEY_Escape:
                self.emit ("changed")
            self.end_key_grab ()
            self.set_label ()
            return

        key = Gdk.keyval_to_lower (event.keyval)
        if (key == Gdk.KEY_ISO_Left_Tab):
            key = Gdk.KEY_Tab

        if event.keyval == Gdk.KEY_Escape and mods:
            self.end_key_grab ()
            self.set_label ()
            dialog = Gtk.MessageDialog (buttons=Gtk.ButtonsType.OK,
                                        transient_for=widget.get_toplevel ())
            dialog.set_markup(_("Escape is reserved and cannot be used for keybindings."))
            dialog.run()
            dialog.destroy()
            return

        if Gtk.accelerator_valid (key, mods) \
           or (key == Gdk.KEY_Tab and mods):
            self.set_label (key, mods)
            self.end_key_grab ()
            self.key = key
            self.mods = mods
            self.emit ("changed")
            return

        self.set_label (key, mods)

    def set_label (self, key = None, mods = None):
        if self.label:
            if key != None and mods != None:
                self.emit ("current-changed")
            Gtk.Button.set_label (self, self.label)
            return
        if key == None and mods == None:
            key = self.key
            mods = self.mods
        label = GetAcceleratorName (key, mods)
        if not len (label):
            label = _("Disabled")
        Gtk.Button.set_label (self, label)

class WindowStateSelector (Gtk.DrawingArea):

    __gsignals__    = {"added" : (GObject.SignalFlags.RUN_FIRST,
                                  None, [GObject.TYPE_STRING]),
                       "removed" : (GObject.SignalFlags.RUN_FIRST,
                                    None, [GObject.TYPE_STRING])}

    _current = []

    _surface = None

    _x0     = 0
    _y0     = 12
    _width  = 36
    _height = 36

    _font   = "Sans 12 Bold"

    def __init__ (self, states):
        '''Prepare widget'''
        super (WindowStateSelector, self).__init__ ()

        self.add_events (Gdk.EventMask.BUTTON_PRESS_MASK)
        self.add_events (Gdk.EventMask.POINTER_MOTION_MASK)

        if GTK_VERSION >= (3, 0, 0):
            self.connect ("draw", self.draw_event)
        else:
            self.connect ("expose-event", self.draw_event)
        self.connect ("button-press-event", self.button_press)
        self.connect ("motion-notify-event", self.region_tooltip)

        self.set_size_request (self._width*4, self._height*3+20)
        x0, y0, width, height = self._x0, self._y0, self._width, self._height

        self._states = {
            "modal"            : (x0            , y0, _("modal")),
            "sticky"           : (x0 + width    , y0, _("sticky")),
            "maxvert"          : (x0 + width * 2, y0, _("max vert")),
            "maxhorz"          : (x0 + width * 3, y0, _("max horz")),

            "shaded"           : (x0            , y0 + height, _("shaded")),
            "skiptaskbar"      : (x0 + width    , y0 + height, _("skip taskbar")),
            "skippager"        : (x0 + width * 2, y0 + height, _("skip pager")),
            "hidden"           : (x0 + width * 3, y0 + height, _("hidden")),

            "fullscreen"       : (x0            , y0 + height * 2, _("fullscreen")),
            "above"            : (x0 + width    , y0 + height * 2, _("above")),
            "below"            : (x0 + width * 2, y0 + height * 2, _("below")),
            "demandsattention" : (x0 + width * 3, y0 + height * 2, _("urgent")),
        }

        self._src_pixbufs = {}
        for state in self._states:
            pixbuf = Image ("ccsm-" + state, ImageInternal, -1).get_pixbuf ()
            self._src_pixbufs[state] = pixbuf

    def set_current(self, value):
        self._current = value
        self.redraw (queue = True)

    def get_current (self):
        return self._current
    current = property (get_current, set_current)

    def draw (self, cr, width, height):
        '''The actual drawing function'''

        if GTK_VERSION >= (3, 6, 0):
            context = self.get_style_context ()
            context.save()
            context.add_class(Gtk.STYLE_CLASS_VIEW)

            bgColor = tuple(context.get_background_color(context.get_state()))
            fgColor = tuple(context.get_color(context.get_state()))

            context.set_state(Gtk.StateFlags.SELECTED)
            selBgColor = tuple(context.get_background_color(context.get_state()))
            selFgColor = tuple(context.get_color(context.get_state()))
            if selFgColor[3] == 0.0:
                selFgColor = (fgColor[0] * 1.2, fgColor[1] * 1.2, fgColor[2] * 1.2, 1.0)
            if selBgColor[3] == 0.0:
                selBgColor = (bgColor[0] * 1.2, bgColor[1] * 1.2, bgColor[2] * 1.2, 1.0)

            context.restore()
        else:
            validBg, bgGdkColor = self.get_style().lookup_color('bg_color')
            validFg, fgGdkColor = self.get_style().lookup_color('fg_color')
            validSelBg, selBgGdkColor = self.get_style().lookup_color('selected_bg_color')
            validSelFg, selFgGdkColor = self.get_style().lookup_color('selected_fg_color')

            bgColor = (bgGdkColor.red / 65535.0, bgGdkColor.green / 65535.0, bgGdkColor.blue / 65535.0, 1.0)
            fgColor = (fgGdkColor.red / 65535.0, fgGdkColor.green / 65535.0, fgGdkColor.blue / 65535.0, 1.0)
            selBgColor = (selBgGdkColor.red / 65535.0, selBgGdkColor.green / 65535.0, selBgGdkColor.blue / 65535.0, 1.0)
            selFgColor = (selFgGdkColor.red / 65535.0, selFgGdkColor.green / 65535.0, selFgGdkColor.blue / 65535.0, 1.0)

            if validSelBg:
                selBgColor = (selBgGdkColor.red / 65535.0, selBgGdkColor.green / 65535.0, selBgGdkColor.blue / 65535.0, 1.0)
            elif validBg:
                selBgColor = (bgColor[0] * 1.2, bgColor[1] * 1.2, bgColor[2] * 1.2, bgColor[3])
            else:
                selBgColor = (0.65, 0.65, 0.65, 1.0)

            if validSelFg:
                selFgColor = (selFgGdkColor.red / 65535.0, selFgGdkColor.green / 65535.0, selFgGdkColor.blue / 65535.0, 1.0)
            elif validFg:
                selBgColor = (fgColor[0] * 1.2, fgColor[1] * 1.2, fgColor[2] * 1.2, fgColor[3])
            else:
                selFgColor = (0.0, 0.0, 0.0, 1.0)

        for stt in self._states:
            x, y, _ = self._states[stt]
            icon = self._src_pixbufs[stt]

            cr.push_group()
            cr.translate(x, y)
            cr.scale((self._width + .0) / icon.get_width(),
                     (self._height + .0) / icon.get_height())
            Gdk.cairo_set_source_pixbuf(cr, icon, 0, 0)
            cr.paint()
            src = cr.pop_group()

            current_state = stt in self._current

            if current_state:
                cr.set_source_rgba(*selBgColor)
                cr.rectangle(x, y, self._width, self._height)
                cr.fill()

            if current_state:
                cr.set_source_rgba(*selFgColor)
            else:
                cr.set_source_rgba(*fgColor)
            cr.mask(src)

    def redraw (self, queue = False):
        '''Redraw internal surface'''
        alloc = self.get_allocation ()
        # Prepare drawing surface
        width, height = alloc.width, alloc.height
        self._surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context (self._surface)
        # Clear
        cr.set_operator (cairo.OPERATOR_CLEAR)
        cr.paint ()
        cr.set_operator (cairo.OPERATOR_OVER)
        # Draw
        self.draw (cr, alloc.width, alloc.height)
        # Queue expose event if required
        if queue:
            self.queue_draw ()

    def draw_event (self, widget, data):
        '''Draw event handler'''
        if GTK_VERSION >= (3, 0, 0):
            cr = data
        else:
            event = data
            cr = event.window.cairo_create ()
        if not self._surface:
            self.redraw ()
        cr.set_source_surface (self._surface)
        if GTK_VERSION < (3, 0, 0):
            cr.rectangle (event.area.x, event.area.y,
                          event.area.width, event.area.height)
            cr.clip ()
        cr.paint ()
        return False

    def in_rect (self, x, y, x0, y0, x1, y1):
        return x >= x0 and y >= y0 and x <= x1 and y <= y1

    def button_press (self, widget, event):
        x, y = event.x, event.y
        stt = ""

        for state in self._states:
            x0, y0, _ = self._states[state]
            if self.in_rect (x, y, x0, y0,
                             x0 + self._width, y0 + self._height):
                stt = state
                break

        if not len (stt):
            return
        if stt in self._current:
            self._current.remove (stt)
            self.emit ("removed", stt)
        else:
            self._current.append (stt)
            self.emit ("added", stt)
        self.redraw (queue = True)

    def region_tooltip (self, widget, event):
        x, y = event.x, event.y
        stt_tip = ""

        for state in self._states:
            x0, y0, tt = self._states[state]
            if self.in_rect (x, y, x0, y0,
                             x0 + self._width, y0 + self._height):
                stt_tip = tt
                break

        self.set_tooltip_markup(stt_tip)

# Match Button
#
class MatchButton(Gtk.Button):

    __gsignals__    = {"changed" : (GObject.SignalFlags.RUN_FIRST,
                                    None,
                                    [GObject.TYPE_STRING])}

    prefix = OrderedDict([
            (_("Window Title"), 'title'),
            (_("Window Role"), 'role'),
            (_("Window Name"), 'name'),
            (_("Window Class"), 'class'),
            (_("Window Type"), 'type'),
            (_("Window State"), 'state'),
            (_("Window ID"), 'xid'),
    ])

    symbols = OrderedDict([
            (_("And"), '&'),
            (_("Or"), '|'),
    ])

    match   = None

    def __init__ (self, entry = None):
        '''Prepare widget'''
        super (MatchButton, self).__init__ ()

        self.entry = entry
        self.match = entry.get_text()

        self.add (Gtk.Image.new_from_icon_name ("list-add",
                                                Gtk.IconSize.BUTTON))
        self.connect ("clicked", self.run_edit_dialog)

    def set_match (self, value):
        self.match = value
        self.entry.set_text(value)
        self.entry.activate()

    def get_xprop_list(self, prefix_regexp, item_regexp, list_type, cmd = "xprop"):
        if sys.version_info.major >= 3:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, encoding="utf-8")
        else:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output = proc.communicate()[0]
        prex = re.compile(prefix_regexp)
        irex = re.compile(item_regexp)
        value = []
        for line in output.split("\n"):
            if prex.search(line):
                value = (s.lower().replace("_", "").replace("maximized", "max") for s in irex.findall(line))
                break
        return value

    def get_xprop (self, regexp, cmd = "xprop"):
        if sys.version_info.major >= 3:
            proc = subprocess.Popen (cmd, stdout=subprocess.PIPE, encoding="utf-8")
        else:
            proc = subprocess.Popen (cmd, stdout=subprocess.PIPE)
        output = proc.communicate ()[0]
        rex = re.compile (regexp)
        value = ""
        for line in output.split ("\n"):
            if rex.search (line):
                m = rex.match (line)
                value = m.groups () [-1]
                break

        return value

    def change_active_value_widget(self, widget, value_widget):
        try:
            prefix = self.prefix[widget.do_get_active_text(widget)]
        except (AttributeError, NameError, TypeError):
            prefix = self.prefix[widget.get_active_text()]

        if prefix == 'state':
            value_widget.set_visible_child_name('list')
        else:
            value_widget.set_visible_child_name('non-list')


    # Regular Expressions taken from beryl-settings
    def grab_value (self, widget, value_widget, type_widget):
        value = ""
        try:
            prefix = self.prefix[type_widget.do_get_active_text(type_widget)]
        except (AttributeError, NameError, TypeError):
            prefix = self.prefix[type_widget.get_active_text()]

        if prefix == "type":
            value = self.get_xprop(r"^_NET_WM_WINDOW_TYPE\(ATOM\) = _NET_WM_WINDOW_TYPE_(\w+)")
            value = value.lower().capitalize()
        elif prefix == "role":
            value = self.get_xprop(r"^WM_WINDOW_ROLE\(STRING\) = \"([^\"]+)\"")
        elif prefix == "name":
            value = self.get_xprop(r"^WM_CLASS\(STRING\) = \"([^\"]+)\"")
        elif prefix == "class":
            value = self.get_xprop(r"^WM_CLASS\(STRING\) = \"([^\"]+)\", \"([^\"]+)\"")
        elif prefix == "title":
            value = self.get_xprop(r"^_NET_WM_NAME\(UTF8_STRING\) = \"([^\n]+)\"")
            if not value:
                value = self.get_xprop(r"^WM_NAME\(STRING\) = \"([^\"]+)\"")
        elif prefix == "xid" or prefix == "id":
            value = self.get_xprop(r"^xwininfo: Window id: ([^\s]+)", "xwininfo")
        elif prefix == "state":
            value = self.get_xprop_list(r"^_NET_WM_STATE\(ATOM\) =",
                                        r"_NET_WM_STATE_(\w+)", "state")

        if value_widget.get_visible_child_name() == 'list':
            w = value_widget.get_visible_child()
            w.set_current(list(value))
        else:
            value_widget.get_visible_child().set_text(value)

    def generate_match (self, t, value, relation, invert, wrap_in_parens=False):
        match = ""
        text = self.match

        prefix = self.prefix[t]
        symbol = self.symbols[relation]

        # check if the current match needs some brackets
        if len(text) > 0 and text[-1] != ')' and text[0] != '(':
            match = "(%s)" % text
        else:
            match = text

        if invert:
            match = "%s %s !(%s=%s)" % (match, symbol, prefix, value)
        elif len(match) > 0:
            if wrap_in_parens:
                match = "%s %s (%s=%s)" % (match, symbol, prefix, value)
            else:
                match = "%s %s %s=%s" % (match, symbol, prefix, value)
        else:
            match = "%s=%s" % (prefix, value)

        self.set_match (match)

    def _check_entry_value (self, entry, dialog):
        is_valid = False
        value = entry.get_text()
        if value != "":
            is_valid = True
        dialog.set_response_sensitive(Gtk.ResponseType.OK, is_valid)

    def _check_list_value (self, widget, item, dialog):
        is_valid = False
        value = widget.current
        if value:
            is_valid = True
        dialog.set_response_sensitive(Gtk.ResponseType.OK, is_valid)

    def run_edit_dialog (self, widget):
        '''Run dialog to generate a match'''

        self.match = self.entry.get_text ()

        dlg = Gtk.Dialog (title=_("Edit match"),
                          transient_for=widget.get_toplevel ())
        dlg.set_position (Gtk.WindowPosition.CENTER_ON_PARENT)
        dlg.set_response_sensitive(Gtk.ResponseType.OK, False)

        button = dlg.add_button (_("_Cancel"), Gtk.ResponseType.CANCEL)
        button.set_image (Gtk.Image.new_from_icon_name ("gtk-cancel",
                                                        Gtk.IconSize.BUTTON))
        button = dlg.add_button (_("_Add"), Gtk.ResponseType.OK)
        button.set_image (Gtk.Image.new_from_icon_name ("list-add",
                                                        Gtk.IconSize.BUTTON))
        button.grab_default ()
        dlg.set_default_response (Gtk.ResponseType.OK)

        if GTK_VERSION >= (3, 12, 0):
            grid = Gtk.Grid (row_spacing=GridRow, column_spacing=GridColumn)
            grid.set_margin_top(GridColumn)
            grid.set_margin_bottom(GridColumn)
            grid.set_margin_start(GridRow)
            grid.set_margin_end(GridRow)
        else:
            grid = Gtk.Table ()

        rows = []

        # Type
        label = Label (_("Type"))
        type_chooser = Gtk.ComboBoxText.new ()
        for t in self.prefix:
            type_chooser.append_text (t)
        type_chooser.set_active (0)
        rows.append ((label, type_chooser))

        # Value
        label = Label (_("Value"))
        box = Gtk.Box (orientation=Gtk.Orientation.HORIZONTAL)
        box.set_spacing (5)
        entry = Gtk.Entry ()
        entry.connect ('changed', self._check_entry_value, dlg)
        list_view = WindowStateSelector([])
        list_view.connect('added', self._check_list_value, dlg)
        list_view.connect('removed', self._check_list_value, dlg)

        value_widget = FallbackStack()
        value_widget.add_named(entry, 'non-list')
        value_widget.add_named(list_view, 'list')
        value_widget.set_visible_child_name('non-list')
        type_chooser.connect('changed', self.change_active_value_widget, value_widget)

        button = Gtk.Button (label=_("Grab"))
        button.connect ('clicked', self.grab_value, value_widget, type_chooser)
        box.pack_start (value_widget, True, True, 0)
        box.pack_start (button, False, False, 0)
        rows.append ((label, box))

        # Relation
        label = Label (_("Relation"))
        relation_chooser = Gtk.ComboBoxText.new ()
        for relation in self.symbols:
            relation_chooser.append_text (relation)
        relation_chooser.set_active (0)
        rows.append ((label, relation_chooser))

        # Invert
        label = Label (_("Invert"))
        check = Gtk.CheckButton ()
        rows.append ((label, check))

        row = 0
        for label, widget in rows:
            if GTK_VERSION >= (3, 12, 0):
                grid.attach(label, 0, row, 1, 1)
                grid.attach(widget, 1, row, 1, 1)
            else:
                grid.attach(label, 0, 1, row, row + 1, yoptions=0,
                            xpadding=GridRow, ypadding=GridColumn)
                grid.attach(widget, 1, 2, row, row + 1, yoptions=0,
                            xpadding=GridRow, ypadding=GridColumn)
            row += 1

        dlg.vbox.pack_start (grid, True, True, 0)
        dlg.vbox.set_spacing (5)
        dlg.show_all ()
        value_widget.set_visible_child_name('non-list')

        response = dlg.run ()
        dlg.hide ()
        if response == Gtk.ResponseType.OK:
            try:
                t        = type_chooser.do_get_active_text (type_chooser)
                relation = relation_chooser.do_get_active_text (relation_chooser)
            except (AttributeError, NameError, TypeError):
                t        = type_chooser.get_active_text ()
                relation = relation_chooser.get_active_text ()
            invert  = check.get_active ()

            if value_widget.get_visible_child_name() == 'list':
                values = value_widget.get_visible_child().current
                value = ' & {0}='.format(self.prefix[t]).join(values)
                wrap_in_parens = True
            else:
                value = entry.get_text ()
                wrap_in_parens = False

            self.generate_match (t, value, relation, invert, wrap_in_parens=wrap_in_parens)

        dlg.destroy ()

class FileButton (Gtk.Button):
    __gsignals__    = {"changed" : (GObject.SignalFlags.RUN_FIRST,
                                    None,
                                    [GObject.TYPE_STRING])}
    _directory = False
    _context   = None
    _image     = False
    _path      = ""

    def __init__ (self, context, entry, directory=False, image=False, path=""):
        Gtk.Button.__init__ (self)

        self._entry = entry
        self._directory = directory
        self._context = context
        self._image = image
        self._path = path

        self.set_tooltip_text(_("Browse..."))
        if self._directory:
            self.set_image(Gtk.Image.new_from_icon_name("folder-open",
                                                        Gtk.IconSize.BUTTON))
        else:
            self.set_image(Gtk.Image.new_from_icon_name("document-open",
                                                        Gtk.IconSize.BUTTON))
        self.connect('clicked', self.open_dialog)

    def set_path (self, value):
        self._path = value
        self._entry.set_text (value)
        self._entry.activate ()

    def create_filter(self):
        filter = Gtk.FileFilter ()
        if self._image:
            filter.set_name (_("Images"))
            filter.add_mime_type ("image/png")
            filter.add_mime_type ("image/jpeg")
            filter.add_mime_type ("image/svg+xml")
            filter.add_pattern ("*.png")
            filter.add_pattern ("*.jpg")
            filter.add_pattern ("*.jpeg")
            filter.add_pattern ("*.svg")
        else:
            filter.add_pattern ("*")
            filter.set_name (_("File"))

        return filter

    def check_type (self, filename):
        if filename.find (".") == -1:
            return True
        ext = filename.split (".") [-1]

        try:
            mime = mimetypes.types_map [".%s" %ext]
        except KeyError:
            return True

        if self._image:
            require = FeatureRequirement (self.get_toplevel (),
                                          self._context, 'imagemime:' + mime)
            return require.Resolve ()

        return True

    def update_preview (self, widget):
        path = widget.get_preview_filename ()
        if path is None or os.path.isdir (path):
            widget.get_preview_widget ().clear ()
            return
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size (path, 128, 128)
        except GLib.GError:
            return
        widget.get_preview_widget ().set_from_pixbuf (pixbuf)

    def open_dialog (self, widget):
        if self._directory:
            title = _("Open directory...")
        else:
            title = _("Open file...")

        chooser = Gtk.FileChooserDialog (title=title,
                                         transient_for=widget.get_toplevel ())
        if self._directory:
            chooser.set_action (Gtk.FileChooserAction.SELECT_FOLDER)
        else:
            chooser.set_filter (self.create_filter ())

        if self._path and os.path.exists (self._path):
            chooser.set_filename (self._path)
        else:
            chooser.set_current_folder (os.environ.get("HOME"))

        if self._image:
            chooser.set_use_preview_label (False)
            chooser.set_preview_widget (Gtk.Image ())
            chooser.connect ("selection-changed", self.update_preview)

        button = chooser.add_button (_("_Cancel"), Gtk.ResponseType.CANCEL)
        button.set_image (Gtk.Image.new_from_icon_name ("gtk-cancel",
                                                        Gtk.IconSize.BUTTON))
        button = chooser.add_button (_("_Open"), Gtk.ResponseType.OK)
        button.set_image (Gtk.Image.new_from_icon_name ("document-open",
                                                        Gtk.IconSize.BUTTON))
        button.grab_default ()
        chooser.set_default_response (Gtk.ResponseType.OK)

        ret = chooser.run ()

        filename = chooser.get_filename ()
        chooser.destroy ()
        if ret == Gtk.ResponseType.OK:
            if self._directory or self.check_type (filename):
                self.set_path (filename)

# About Dialog
#
class AboutDialog (Gtk.AboutDialog):
    NAME = _("CompizConfig Settings Manager")
    VERSION = Version
    LOGO = "ccsm"
    COMMENTS = _("This is a settings manager for the CompizConfig configuration system.")
    COPYRIGHT = u"Copyright \xA9 2007-2008 Patrick Niklaus/Christopher Williams/Guillaume Seguin/Quinn Storm"
    AUTHORS = ["Patrick Niklaus <patrick.niklaus@student.kit.edu>",
               "Christopher Williams <christopherw@verizon.net>",
               "Guillaume Seguin <guillaume@segu.in>",
               "Quinn Storm <livinglatexkali@gmail.com>",
               "Alexei Sorokin <sor.alexei@meowr.ru>"]
    ARTISTS = ["Andrew Wedderburn <andrew.wedderburn@gmail.com>",
               "Patrick Niklaus <patrick.niklaus@student.kit.edu>",
               "GNOME Icon Theme Team"]
    TRANSLATOR_CREDITS = _("translator-credits")
    WEBSITE = "https://gitlab.com/compiz/ccsm"

    def __init__ (self, parent):
        Gtk.AboutDialog.__init__ (self, transient_for=parent,
                                  program_name=AboutDialog.NAME,
                                  version=AboutDialog.VERSION,
                                  logo_icon_name=AboutDialog.LOGO,
                                  comments=AboutDialog.COMMENTS,
                                  copyright=AboutDialog.COPYRIGHT,
                                  authors=AboutDialog.AUTHORS,
                                  artists=AboutDialog.ARTISTS,
                                  translator_credits=AboutDialog.TRANSLATOR_CREDITS,
                                  website=AboutDialog.WEBSITE)

        if GTK_VERSION >= (3, 0, 0):
            self.set_license_type (Gtk.License.GPL_2_0)
        else:
            self.set_license ("This program is free software; you can " +
                              "redistribute it and/or modify it under the " +
                              "terms of the GNU General Public License as " +
                              "published by the Free Software Foundation; " +
                              "either version 2 of the License, or (at your " +
                              "opinion) any later version.")
            self.set_wrap_license (True)

# Error dialog
#
class ErrorDialog (Gtk.MessageDialog):
    '''Display an error dialog'''

    def __init__ (self, parent, message):
        Gtk.MessageDialog.__init__ (self, transient_for=parent,
                                    destroy_with_parent=True,
                                    message_type=Gtk.MessageType.ERROR,
                                    buttons=Gtk.ButtonsType.CLOSE)
        self.set_position (Gtk.WindowPosition.CENTER)
        self.set_markup (message)
        self.set_title (_("An error has occured"))
        self.set_transient_for (parent)
        self.set_modal (True)
        self.show_all ()
        self.connect ("response", lambda *args: self.destroy ())

# Warning dialog
#
class WarningDialog (Gtk.MessageDialog):
    '''Display a warning dialog'''

    def __init__ (self, parent, message):
        Gtk.MessageDialog.__init__ (self, transient_for=parent,
                                    destroy_with_parent=True,
                                    message_type=Gtk.MessageType.WARNING,
                                    buttons=Gtk.ButtonsType.YES_NO)
        self.set_position (Gtk.WindowPosition.CENTER)
        self.set_markup (message)
        self.set_title (_("Warning"))
        self.set_transient_for (parent)
        self.connect_after ("response", lambda *args: self.destroy ())

# Plugin Button
#
class PluginButton (Gtk.Box):

    __gsignals__    = {"clicked"   : (GObject.SignalFlags.RUN_FIRST,
                                      None,
                                      []),
                       "activated" : (GObject.SignalFlags.RUN_FIRST,
                                      None,
                                      [])}

    _plugin = None

    def __init__ (self, plugin, useMissingImage = False):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self._plugin = plugin

        if not useMissingImage:
            image = Image (plugin.Name, ImagePlugin, 32)
        else:
            image = Image ("image-missing", ImageThemed, 32)
        label = Label (plugin.ShortDesc, 120)
        box = Gtk.Box (orientation=Gtk.Orientation.HORIZONTAL)
        box.set_spacing (5)
        box.pack_start (image, False, False, 0)
        box.pack_start (label, True, True, 0)

        button = PrettyButton ()
        button.connect ('clicked', self.show_plugin_page)
        button.set_tooltip_text (plugin.LongDesc)
        button.add (box)

        blacklist_plugins = ['core']
        if os.getenv('XDG_CURRENT_DESKTOP') == 'Unity':
            blacklist_plugins.append('unityshell')

        if plugin.Name not in blacklist_plugins:
            enable = Gtk.CheckButton ()
            enable.set_tooltip_text(_("Enable %s") % plugin.ShortDesc)
            enable.set_active (plugin.Enabled)
            enable.set_sensitive (plugin.Context.AutoSort)
            self._toggled_handler = enable.connect ("toggled", self.enable_plugin)
            PluginSetting (plugin, enable, self._toggled_handler)
            self.pack_start (enable, False, False, 0)
        self.pack_start (button, False, False, 0)

        self.set_size_request (220, -1)

    def enable_plugin (self, widget):

        plugin = self._plugin
        conflicts = plugin.Enabled and plugin.DisableConflicts or plugin.EnableConflicts

        conflict = PluginConflict (widget.get_toplevel (), plugin, conflicts)

        if conflict.Resolve ():
            plugin.Enabled = widget.get_active ()
        else:
            widget.handler_block(self._toggled_handler)
            widget.set_active (plugin.Enabled)
            widget.handler_unblock(self._toggled_handler)

        plugin.Context.Write ()
        GlobalUpdater.UpdatePlugins()
        plugin.Context.UpdateExtensiblePlugins ()
        self.emit ('activated')

    def show_plugin_page (self, widget):
        self.emit ('clicked')

    def filter (self, text, level=FilterAll):
        found = False
        if level & FilterName:
            if (text in self._plugin.Name.lower ()
            or text in self._plugin.ShortDesc.lower ()):
                found = True
        if not found and level & FilterLongDesc:
            if text in self._plugin.LongDesc.lower():
                found = True
        if not found and level & FilterCategory:
            if text == None \
            or (text == "" and self._plugin.Category.lower() == "") \
            or (text != "" and text in self._plugin.Category.lower()):
                found = True

        return found

    def get_plugin (self):
        return self._plugin

# Category Box
#
class CategoryBox(Gtk.Box):

    _plugins = None
    _unfiltered_plugins = None
    _buttons = None
    _context = None
    _name    = ""
    _grid    = None
    _separator = None
    _current_cols = 0
    _current_plugins = 0

    def __init__ (self, context, name, plugins=None, categoryIndex=0):
        Gtk.Box.__init__ (self)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing (5)

        self._context = context
        if plugins is not None:
            self._plugins = plugins
        else:
            self._plugins = []

        if not plugins:
            for plugin in context.Plugins.values ():
                if plugin.Category == name:
                    self._plugins.append (plugin)

        self._plugins.sort(key=PluginKeyFunc)
        self._name = name
        text = name or 'Uncategorized'

        # Keep unfiltered list of plugins for correct background icon loading
        self._unfiltered_plugins = self._plugins

        header = Gtk.Box (orientation=Gtk.Orientation.HORIZONTAL)
        if GTK_VERSION >= (3, 0, 0):
            header.props.margin = 5
        else:
            header.set_border_width (5)
        header.set_spacing (10)
        label = Label ('', -1)
        label.set_markup ("<span color='#aaa' size='x-large' weight='800'>%s</span>" % _(text))

        icon = text.lower ().replace (" ", "_")
        image = Image (icon, ImageCategory)
        header.pack_start (image, False, False, 0)
        header.pack_start (label, True, True, 0)

        if GTK_VERSION >= (3, 12, 0):
            self._grid = Gtk.Grid (row_spacing=GridRow,
                                   column_spacing=GridColumn)
            self._grid.set_margin_top (GridColumn + 10)
            self._grid.set_margin_bottom (GridColumn + 10)
            self._grid.set_margin_start (GridRow + 10)
            self._grid.set_margin_end (GridRow + 10)
        else:
            self._grid = Gtk.Table ()
            self._grid.set_border_width (10)

        # load icons now only for the first 3 categories
        dontLoadIcons = (categoryIndex >= 3);

        self._buttons = []
        for plugin in self._plugins:
            button = PluginButton(plugin, dontLoadIcons)
            self._buttons.append(button)

        if GTK_VERSION >= (3, 0, 0):
            self._separator = Gtk.Separator (orientation=Gtk.Orientation.HORIZONTAL)
            self._separator.set_margin_bottom (20)
        else:
            self._separator = Gtk.Alignment ()
            self._separator.set_padding (0, 20, 0, 0)
            self._separator.add (Gtk.HSeparator ())

        self.pack_start (header, False, False, 0)
        self.pack_start (self._grid, False, False, 0)
        self.pack_start (self._separator, True, True, 0)

    def show_separator (self, show):
        children = self.get_children ()
        if show:
            if self._separator not in children:
                self.pack_start (self._separator, True, True, 0)
        else:
            if self._separator in children:
                self.remove(self._separator)

    def filter_buttons (self, text, level=FilterAll):
        self._plugins = []
        for button in self._buttons:
            if button.filter (text, level=level):
                self._plugins.append (button.get_plugin())

        return bool(self._plugins)

    def rebuild_grid (self, ncols, force = False):
        if (not force and ncols == self._current_cols
        and len (self._plugins) == self._current_plugins):
            return
        self._current_cols = ncols
        self._current_plugins = len (self._plugins)

        children = self._grid.get_children ()
        if children:
            for child in children:
                self._grid.remove(child)

        row = 0
        col = 0
        for button in self._buttons:
            if button.get_plugin () in self._plugins:
                if GTK_VERSION >= (3, 12, 0):
                    self._grid.attach (button, col, row, 1, 1)
                else:
                    self._grid.attach (button, col, col+1, row, row + 1, 0,
                                       xpadding=GridRow, ypadding=GridColumn)
                col += 1
                if col == ncols:
                    col = 0
                    row += 1
        self.show_all ()

    def get_buttons (self):
        return self._buttons

    def get_plugins (self):
        return self._plugins

    def get_unfiltered_plugins (self):
        return self._unfiltered_plugins

# Plugin Window
#
class PluginWindow(Gtk.ScrolledWindow):
    __gsignals__    = {"show-plugin" : (GObject.SignalFlags.RUN_FIRST,
                                        None,
                                        [GObject.TYPE_PYOBJECT])}

    _not_found_box = None
    _style_block   = 0
    _context       = None
    _categories    = None
    _viewport      = None
    _boxes         = None
    _box           = None

    def __init__ (self, context, categories=[], plugins=[]):
        Gtk.ScrolledWindow.__init__ (self)

        self._categories = {}
        self._boxes = []
        self._context = context
        pool = plugins or list(self._context.Plugins.values())
        if len (categories):
            for plugin in pool:
                category = plugin.Category
                if category in categories:
                    if not category in self._categories:
                        self._categories[category] = []
                    self._categories[category].append(plugin)
        else:
            for plugin in pool:
                category = plugin.Category
                if not category in self._categories:
                    self._categories[category] = []
                self._categories[category].append(plugin)

        self.props.hscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        self.props.vscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        if GTK_VERSION >= (3, 0, 0):
            self.connect ('draw', self.rebuild_boxes)
        else:
            self.connect ('size-allocate', self.rebuild_boxes)

        self._box = Gtk.Box (orientation=Gtk.Orientation.VERTICAL)
        self._box.set_spacing (5)

        self._not_found_box = NotFoundBox ()

        categories = sorted(self._categories, key=CategoryKeyFunc)
        for (i, category) in enumerate(categories):
            plugins = self._categories[category]
            category_box = CategoryBox(context, category, plugins, i)
            self.connect_buttons (category_box)
            self._boxes.append (category_box)
            self._box.pack_start (category_box, False, False, 0)

        viewport = Gtk.Viewport ()
        if GTK_VERSION >= (3, 0, 0):
            viewport.get_style_context ().add_class (Gtk.STYLE_CLASS_VIEW)
        if GTK_VERSION >= (3, 12, 0):
            viewport.connect ('style-updated', self.update_viewport_style)
        else:
            viewport.connect ('style-set', self.update_viewport_style)
        viewport.set_focus_vadjustment (self.get_vadjustment ())
        viewport.add (self._box)
        self.add (viewport)

    def connect_buttons (self, category_box):
        buttons = category_box.get_buttons ()
        for button in buttons:
            button.connect('clicked', self.show_plugin_page)

    def update_viewport_style (self, widget, previous=None):
        if self._style_block > 0:
            return
        self._style_block += 1
        if GTK_VERSION < (3, 0, 0):
            bgColor = widget.get_style().lookup_color('base_color')
            if bgColor[0] != False:
                widget.modify_bg(Gtk.StateType.NORMAL, bgColor[1])
            else:
                widget.modify_bg(Gtk.StateType.NORMAL, None)
        self._style_block -= 1

    def filter_boxes (self, text, level=FilterAll):
        found = False

        for box in self._boxes:
            found |= box.filter_buttons (text, level)

        viewport = self.get_child ()
        child    = viewport.get_child ()

        if not found:
            if child is not self._not_found_box:
                viewport.remove (self._box)
                viewport.add (self._not_found_box)
            self._not_found_box.update (text)
        else:
            if child is self._not_found_box:
                viewport.remove (self._not_found_box)
                viewport.add (self._box)

        self.rebuild_boxes(self, self.get_allocation())
        self.queue_resize()
        self.show_all()

    def rebuild_boxes (self, widget, extra=None):
        rect = widget.get_allocation ()
        ncols = (int) (rect.width / 220)
        width = ncols * (220 + 2 * GridRow) + 40
        if width > rect.width:
            ncols -= 1

        children = self._box.get_children ()
        real_len = 0
        for box in self._boxes:
            if len(box.get_plugins()) != 0:
                real_len += 1
        pos = 0
        for box in self._boxes:
            if len(box.get_plugins()) == 0:
                if box in children:
                    self._box.remove(box)
            else:
                if box not in children:
                    self._box.pack_start (box, False, False, 0)
                    self._box.reorder_child (box, pos)
                box.rebuild_grid (ncols)
                if pos + 1 != real_len:
                    box.show_separator(True)
                else:
                    box.show_separator(False)
                pos += 1

    def get_categories (self):
        return list(self._categories)

    def show_plugin_page (self, widget):
        plugin = widget.get_plugin ()
        self.emit ('show-plugin', plugin)

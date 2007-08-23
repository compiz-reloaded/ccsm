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
import gtk.gdk
import gobject
import cairo
from math import pi, sqrt
import time

from ccm.Utils import *
from ccm.Constants import *

import locale
import gettext
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("ccsm", DataDir + "/locale")
gettext.textdomain("ccsm")
_ = gettext.gettext

#
# Try to use gtk like coding style for consistency
#

# Selector Buttons
#
class SelectorButtons(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
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
        arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)
        button = gtk.Button(label)
        button.set_relief(gtk.RELIEF_NONE)
        button.connect('clicked', callback, label)
        if len(self.get_children()) > 0:
            self.pack_start(arrow, False, False)
            self.arrows.append(arrow)
        self.pack_start(button, False, False)
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

# Selector Box
#
class SelectorBox(gtk.ScrolledWindow):
    def __init__(self, backgroundColor):
        gtk.ScrolledWindow.__init__(self)
        self.viewport = gtk.Viewport()
        self.viewport.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(backgroundColor))
        self.props.hscrollbar_policy = gtk.POLICY_NEVER
        self.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        self.set_size_request(210, 150)
        self.box = gtk.VBox()
        self.box.set_spacing(5)
        self.viewport.add(self.box)
        self.add(self.viewport)

    def close(self):
        self.destroy()
        self.viewport.destroy()
        for button in self.box.get_children():
            button.destroy()
        self.box.destroy()

    def add_item(self, item, callback, markup="%s"):
        button = gtk.Button()
        label = Label()
        item = item.replace("&", "&amp;")
        label.set_markup(markup % item or _("General"))
        button.add(label)
        button.connect("clicked", callback, item)
        button.set_relief(gtk.RELIEF_NONE)
        self.box.pack_start(button, False, False)

    def clear_list(self):
        for button in self.box.get_children():
            button.destroy()
    
    def set_item_list(self, list, callback):
        self.clear_list()
        for item in list:
            self.add_item(item)
            
        self.box.show_all()

# Scrolled List
#
class ScrolledList(gtk.ScrolledWindow):
    def __init__(self, name):
        gtk.ScrolledWindow.__init__(self)

        self.props.hscrollbar_policy = gtk.POLICY_NEVER
        self.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC

        self.store = gtk.ListStore(gobject.TYPE_STRING)

        self.custom_style = Style()

        viewport = gtk.Viewport()
        viewport.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.custom_style.BackgroundColor))
    
        self.view = gtk.TreeView(self.store)
        self.view.set_headers_visible(True)
        self.view.insert_column_with_attributes(-1, name, gtk.CellRendererText(), text=0)
        
        self.set_size_request(300, 300)
        
        viewport.add(self.view)
        self.add(viewport)
        
        self.select = self.view.get_selection()
        self.select.set_mode(gtk.SELECTION_SINGLE)

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
        self.store.set(iter, 0, value)

    def set(self, pos, value):
        iter = self.store.get_iter(pos)
        self.store.set(iter, 0, value)

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

# Edge selection widget
#
class EdgeSelector (gtk.DrawingArea):

    _current = []

    _base_surface   = None
    _surface        = None

    def __init__ (self, edge):
        '''Prepare widget'''
        super (EdgeSelector, self).__init__ ()
        self.current = edge
        background = "%s/display.png" % PixmapDir
        self._base_surface = cairo.ImageSurface.create_from_png (background)
        self.add_events (gtk.gdk.BUTTON_PRESS_MASK)
        self.connect ("expose_event", self.expose)
        self.connect ("button_press_event", self.button_press)
        self.set_size_request (200, 200)

    def set_current (self, value):
        self._current = value.split ("|")

    def get_current (self):
        return "|".join (filter (lambda s: len (s) > 0, self._current))
    current = property (get_current, set_current)

    def draw (self, cr, width, height):
        '''The actual drawing function'''
        # Useful vars
        x0 = 25
        y0 = 33
        x1 = 175
        y1 = 125
        x2 = x0 + 40
        x3 = x1 - 40
        y2 = y0 + 27
        y3 = y1 - 27
        cradius = 20
        radius = 13
        # Top left edge
        cr.new_path ()
        cr.move_to (x0, y0 - cradius)
        cr.line_to (x0, y0)
        cr.line_to (x0 + cradius, y0)
        cr.arc (x0, y0, cradius, 0, pi / 2)
        self.set_color (cr, "TopLeft")
        cr.fill ()
        # Top right edge
        cr.new_path ()
        cr.move_to (x1, y0 + cradius)
        cr.line_to (x1, y0)
        cr.line_to (x1 - cradius, y0)
        cr.arc (x1, y0, cradius, pi / 2, pi)
        self.set_color (cr, "TopRight")
        cr.fill ()
        # Bottom left edge
        cr.new_path ()
        cr.move_to (x0, y1 - cradius)
        cr.line_to (x0, y1)
        cr.line_to (x0 + cradius, y1)
        cr.arc (x0, y1, cradius, 3 * pi / 2, 2 * pi)
        self.set_color (cr, "BottomLeft")
        cr.fill ()
        # Bottom right edge
        cr.new_path ()
        cr.move_to (x1, y1 - cradius)
        cr.line_to (x1, y1)
        cr.line_to (x1 - cradius, y1)
        cr.arc (x1, y1, cradius, pi, 3 * pi / 2)
        self.set_color (cr, "BottomRight")
        cr.fill ()
        # Top edge
        cr.new_path ()
        cr.move_to (x2 + radius, y0)
        cr.line_to (x3 - radius, y0)
        cr.arc (x3 - radius, y0, radius, 0, pi / 2)
        cr.line_to (x2 + radius, y0 + radius)
        cr.arc (x2 + radius, y0, radius, pi / 2, pi)
        self.set_color (cr, "Top")
        cr.fill ()
        # Bottom edge
        cr.new_path ()
        cr.move_to (x2 + radius, y1)
        cr.line_to (x3 - radius, y1)
        cr.arc_negative (x3 - radius, y1, radius, 0, - pi / 2)
        cr.line_to (x2 + radius, y1 - radius)
        cr.arc_negative (x2 + radius, y1, radius, - pi / 2, pi)
        self.set_color (cr, "Bottom")
        cr.fill ()
        # Left edge
        cr.new_path ()
        cr.move_to (x0, y2 + radius)
        cr.line_to (x0, y3 - radius)
        cr.arc_negative (x0, y3 - radius, radius, pi / 2, 0)
        cr.line_to (x0 + radius, y2 + radius)
        cr.arc_negative (x0, y2 + radius, radius, 0, 3 * pi / 2)
        self.set_color (cr, "Left")
        cr.fill ()
        # Right edge
        cr.new_path ()
        cr.move_to (x1, y2 + radius)
        cr.line_to (x1, y3 - radius)
        cr.arc (x1, y3 - radius, radius, pi / 2, pi)
        cr.line_to (x1 - radius, y2 + radius)
        cr.arc (x1, y2 + radius, radius, pi, 3 * pi / 2)
        self.set_color (cr, "Right")
        cr.fill ()

    def set_color (self, cr, edge):
        '''Set painting color for edge'''
        if edge in self._current:
            cr.set_source_rgb (0, 1, 0)
        else:
            cr.set_source_rgb (0.90, 0, 0)

    def redraw (self, queue = False):
        '''Redraw internal surface'''
        alloc = self.get_allocation ()
        # Prepare drawing surface
        width, height = alloc.width, alloc.height
        self._surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context (self._surface)
        # Draw background
        cr.set_source_surface (self._base_surface)
        cr.paint ()
        # Draw
        self.draw (cr, alloc.width, alloc.height)
        # Queue expose event if required
        if queue:
            self.queue_draw ()

    def expose (self, widget, event):
        '''Expose event handler'''
        cr = self.window.cairo_create ()
        if not self._surface:
            self.redraw ()
        cr.set_source_surface (self._surface)
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
        x0 = 25
        y0 = 33
        x1 = 175
        y1 = 125
        x2 = x0 + 40
        x3 = x1 - 40
        y2 = y0 + 27
        y3 = y1 - 27
        cradius = 20
        radius = 13

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

        if not len (edge):
            return
        if edge in self._current:
            self._current.remove (edge)
        else:
            self._current.append (edge)
        self.redraw (queue = True)

# Key Grabber
#
class keyGrabber (gtk.Button):

    key     = 0
    mods    = 0
    handler = None

    def __init__ (self, key = 0, mods = 0):
        '''Prepare widget'''
        super (keyGrabber, self).__init__ ()

        self.key = key
        self.mods = mods

        self.connect ("clicked", self.begin_key_grab)
        self.set_label ()

    def begin_key_grab (self, widget):
        self.add_events (gtk.gdk.KEY_PRESS_MASK)
        self.handler = self.connect ("key-press-event",
                                     self.on_key_press_event)
        while gtk.gdk.keyboard_grab (self.window) != gtk.gdk.GRAB_SUCCESS:
            time.sleep (0.1)

    def end_key_grab (self):
        gtk.gdk.keyboard_ungrab (gtk.get_current_event_time ())
        self.disconnect (self.handler)

    def on_key_press_event (self, widget, event):

        if event.keyval in (gtk.keysyms.Escape, gtk.keysyms.Return,
                            gtk.keysyms.BackSpace):
            if event.keyval == gtk.keysyms.BackSpace:
                self.key = 0
                self.mods = 0
            self.end_key_grab ()
            self.set_label ()

        key = gtk.gdk.keyval_to_lower (event.keyval)
        if (key == gtk.keysyms.ISO_Left_Tab):
            key = gtk.keysyms.Tab

        mods = event.state & gtk.accelerator_get_default_mod_mask ()

        if gtk.accelerator_valid (key, mods):
            self.end_key_grab ()
            self.key = key
            self.mods = mods

        self.set_label (key, mods)

    def set_label (self, key = None, mods = None):
        if key == None and mods == None:
            key = self.key
            mods = self.mods
        label = gtk.accelerator_name (key, mods)
        if not len (label):
            label = "Disabled"
        gtk.Button.set_label (self, label)

# About Dialog
#
class AboutDialog (gtk.AboutDialog):
    def __init__ (self):
        gtk.AboutDialog.__init__ (self)

        self.set_name (_("CompizConfig Settings Manager"))
        self.set_version (Version)
        self.set_comments (_("This is a settings manager for the CompizConfig configuration system."))
        self.set_copyright ("Copyright \xC2\xA9 2007 Patrick Niklaus/Quinn Storm")
        self.set_translator_credits (_("translator-credits"))
        self.set_authors (["Patrick Niklaus <marex@opencompositing.org>",
                           "Quinn Storm <quinn@beryl-project.org>"])
        self.set_artists (["Andrew Wedderburn <andrew.wedderburn@gmail.com>",
                           "Patrick Niklaus <marex@opencompositing.org>",
                           "Gnome Icon Theme Team"])
        self.set_icon (gtk.gdk.pixbuf_new_from_file (IconDir+"/apps/ccsm.svg"))
        self.set_logo (gtk.gdk.pixbuf_new_from_file (IconDir+"/apps/ccsm.svg"))
        self.set_website ("http://www.compiz-fusion.org")


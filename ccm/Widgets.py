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


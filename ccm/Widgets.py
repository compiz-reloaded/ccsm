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

# Selector Buttons
#
class SelectorButtons(gtk.HBox):
	def __init__(self):
		gtk.HBox.__init__(self)
		self.set_border_width(10)
		self.set_spacing(5)
		self.Buttons = []
		self.Arrows = []

	def clear_buttons(self):
		for widget in (self.Arrows + self.Buttons):
			widget.destroy()

		self.Arrows = []
		self.Buttons = []

	def add_button(self, label, callback):
		arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)
		button = gtk.Button(label)
		button.set_relief(gtk.RELIEF_NONE)
		button.connect('clicked', callback, label)
		if len(self.get_children()) > 0:
			self.pack_start(arrow, False, False)
			self.Arrows.append(arrow)
		self.pack_start(button, False, False)
		self.Buttons.append(button)
		self.show_all()

	def remove_button(self, pos):
		if pos > len(self.Buttons)-1:
			return
		self.Buttons[pos].destroy()
		self.Buttons.remove(self.Buttons[pos])
		if pos > 0:
			self.Arrows[pos-1].destroy()
			self.Arrows.remove(self.Arrows[pos-1])

# Selector Box
#
class SelectorBox(gtk.ScrolledWindow):
	def __init__(self, backgroundColor):
		gtk.ScrolledWindow.__init__(self)
		self.SelectedItem = None
		self.Viewport = gtk.Viewport()
		self.Viewport.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(backgroundColor))
		self.props.hscrollbar_policy = gtk.POLICY_NEVER
		self.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
		self.set_size_request(210, 150)
		self.Box = gtk.VBox()
		self.Box.set_spacing(5)
		self.Viewport.add(self.Box)
		self.add(self.Viewport)

	def close(self):
		self.destroy()
		self.Viewport.destroy()
		for button in self.Box.get_children():
			button.destroy()
		self.Box.destroy()

	def add_item(self, item, callback, markup="%s"):
		button = gtk.Button()
		label = Label()
		item = item.replace("&", "&amp;")
		label.set_markup(markup % item or _("General"))
		button.add(label)
		button.connect("clicked", callback, item)
		button.set_relief(gtk.RELIEF_NONE)
		self.Box.pack_start(button, False, False)

	def clear_list(self):
		for button in self.Box.get_children():
			button.destroy()
	
	def set_item_list(self, list, callback):
		self.clear_list()
		for item in list:
			self.add_item(item)
			
		self.Box.show_all()

# Scrolled List
#
class ScrolledList(gtk.ScrolledWindow):
	def __init__(self, name):
		gtk.ScrolledWindow.__init__(self)

		self.props.hscrollbar_policy = gtk.POLICY_NEVER
		self.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC

		self.Store = gtk.ListStore(gobject.TYPE_STRING)

		self.Style = Style()

		viewport = gtk.Viewport()
		viewport.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.Style.BackgroundColor))
	
		self.ListView = gtk.TreeView(self.Store)
		self.ListView.set_headers_visible(True)
		self.ListView.insert_column_with_attributes(-1, name, gtk.CellRendererText(), text=0)
		
		self.set_size_request(300, 300)
		
		viewport.add(self.ListView)
		self.add(viewport)
		
		self.Select = self.ListView.get_selection()
		self.Select.set_mode(gtk.SELECTION_SINGLE)

	def get_list(self):
		values = []
		iter = self.Store.get_iter_first()
		while iter:
			value = self.Store.get(iter, 0)[0]
			if value != "":
				values.append(value)
			iter = self.Store.iter_next(iter)	
		return values

	def clear(self):
		self.Store.clear()
	
	def append(self, value):
		iter = self.Store.append()
		self.Store.set(iter, 0, value)

	def set(self, pos, value):
		iter = self.Store.get_iter(pos)
		self.Store.set(iter, 0, value)

	def delete(self, b):
		selectedRows = self.Select.get_selected_rows()[1]
		for path in selectedRows:
			iter = self.Store.get_iter(path)
			self.Store.remove(iter)
	
	def move_up(self, b):
		selectedRows = self.Select.get_selected_rows()[1]
		if len(selectedRows) == 1:
			iter = self.Store.get_iter(selectedRows[0])
			prev = self.Store.get_iter_first()
			if not self.Store.get_path(prev) == self.Store.get_path(iter):
				while prev is not None and not self.Store.get_path(self.Store.iter_next(prev)) == self.Store.get_path(iter):
					prev = self.Store.iter_next(prev)
				self.Store.swap(iter, prev)

	def move_down(self, b):
		selectedRows = self.Select.get_selected_rows()[1]
		if len(selectedRows) == 1:
			iter = self.Store.get_iter(selectedRows[0])
			next = self.Store.iter_next(iter)
			if next is not None:
				self.Store.swap(iter, next)

# About Dialog
#
class AboutDialog(gtk.AboutDialog):
	def __init__(self):
		gtk.AboutDialog.__init__(self)

		self.set_name(_("CompizConfig Settings Manager"))
		self.set_version(Version)
		self.set_comments(_("This is a settings manager for the CompizConfig configuration system."))
		self.set_copyright("Copyright \xC2\xA9 2007 Patrick Niklaus/Quinn Storm")
		self.set_translator_credits(_("translator-credits"))
		self.set_authors(["Patrick Niklaus <marex@opencompositing.org>",
						  "Quinn Storm <quinn@beryl-project.org>"])
		self.set_artists(["Andrew Wedderburn <andrew.wedderburn@gmail.com>",
						  "Patrick Niklaus <marex@opencompositing.org>",
						  "Gnome Icon Theme Team"])
		self.set_icon(gtk.gdk.pixbuf_new_from_file(IconDir+"/apps/ccsm.svg"))
		self.set_logo(gtk.gdk.pixbuf_new_from_file(IconDir+"/apps/ccsm.svg"))
		self.set_website("http://www.opencompositing.org")

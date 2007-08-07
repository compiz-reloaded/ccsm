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

import compizconfig
ccs = compizconfig

from ccm.Constants import *
from ccm.Settings import *
from ccm.Conflicts import *
from ccm.Utils import *

import locale
import gettext
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("ccsm", DataDir + "/locale")
gettext.textdomain("ccsm")
_ = gettext.gettext

# Action Page
#
class ActionPage:
	def __init__(self, context, plugin = None, filter = None):
		self.EdgeList = ['None', 'TopLeft', 'Top', 'TopRight', 'Left', 'Right', 'BottomLeft', 'Bottom', 'BottomRight']
		self.Widget = gtk.VBox()
		self.Plugin = plugin
		self.Filter = filter
		self.Context = context
		self.Scroll = gtk.ScrolledWindow()
		self.Scroll.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
		self.Scroll.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
		self.Store = gtk.TreeStore(
				gobject.TYPE_STRING, 	#0-Name
				gobject.TYPE_UINT, 		#1-Key
				gobject.TYPE_UINT, 		#2-KeyMods
				gobject.TYPE_STRING, 	#3-Button
				gobject.TYPE_STRING, 	#4-Edges
				gobject.TYPE_STRING,	#5-EdgeButton
				gobject.TYPE_BOOLEAN, 	#6-Visible/Editable
				gobject.TYPE_BOOLEAN, 	#7-Bell
				gobject.TYPE_BOOLEAN,   #8-KeyPossible
				gobject.TYPE_BOOLEAN,   #9-ButPossible
				gobject.TYPE_BOOLEAN,   #10-EdgePossible
				gobject.TYPE_BOOLEAN,   #11-BellPossible
				gobject.TYPE_STRING, 	#12-group
				gobject.TYPE_STRING, 	#13-subgroup
				gobject.TYPE_STRING, 	#14-setting
				gobject.TYPE_STRING, 	#15-plugin
				gobject.TYPE_STRING, 	#16-disp/scn str XXX
				)
		
		self.TreeView = gtk.TreeView(self.Store)
		self.TreeView.set_headers_visible(True)
		# Name
		self.TreeView.insert_column_with_attributes(-1, _("Name"), gtk.CellRendererText(), markup=0)
		# Key
		keyRenderer = gtk.CellRendererAccel()
		keyRenderer.connect('accel-edited', self.KeyEdited)
		keyRenderer.connect('accel-cleared', self.KeyCleared)
		self.TreeView.insert_column_with_attributes(-1, _("Key"), keyRenderer, accel_key=1, accel_mods=2, editable=8, visible=6, sensitive=8)
		# Button
		buttonRenderer = gtk.CellRendererText()
		buttonRenderer.connect('edited', self.ButtonEdited)
		self.TreeView.insert_column_with_attributes(-1, _("Button"), buttonRenderer, text=3, editable=9, visible=6, sensitive=9)
		# Edges
		edgeRenderer = gtk.CellRendererText()
		self.TreeView.insert_column_with_attributes(-1, _("Screen Edge"), edgeRenderer, text=4, visible=6, sensitive=10)
		# Edge Button
		self.EdgeButtonStore = gtk.ListStore(gobject.TYPE_STRING)
		for number in range(0, 6):
			iter = self.EdgeButtonStore.append()
			text = ""
			if number != 0:
				text = _("Button %i") % number
			else:
				text = _("None")
			self.EdgeButtonStore.set(iter, 0, text)
		edgeButtonRenderer = gtk.CellRendererCombo()
		edgeButtonRenderer.props.has_entry = False
		edgeButtonRenderer.props.model = self.EdgeButtonStore
		edgeButtonRenderer.props.text_column = 0
		edgeButtonRenderer.connect('edited', self.EdgeButtonEdited)
		self.TreeView.insert_column_with_attributes(-1, _("Edge Button"), edgeButtonRenderer, text=5, visible=6, editable=10, sensitive=10)
		# Bell -- may replace with one setting in general
		bellRenderer = gtk.CellRendererToggle()
		bellRenderer.props.xalign = 0
		bellRenderer.connect('toggled', self.BellEdited)
		self.TreeView.insert_column_with_attributes(-1, _("On System Bell"), bellRenderer, activatable=11, visible=6, sensitive=11, active=7) 
		
		for col in self.TreeView.get_columns():
			col.set_resizable(True)
		
		self.Scroll.add(self.TreeView)
		self.Widget.pack_start(self.Scroll, True, True)
		self.TreeView.connect('row-activated', self.Activated)

		self.UpdateTreeView()
		
	def UpdateTreeView(self):
		self.Store.clear()
		self.Empty = True

		self.Plugins = {}
		if self.Plugin:
			self.DoGroups(self.Plugin.Groups, None, self.Plugin.Name)
		else:
			for plugin in sorted(self.Context.Plugins.values(), PluginSortCompare):
				pluginIter = self.Store.append(None)
				markup = "%s"
				if plugin.Enabled:
					markup = "<b>%s</b>"
				self.Store.set(pluginIter, 0, markup % plugin.ShortDesc, 6, False, 8, False, 9, False, 10, False, 11, False)
				if not self.DoGroups(plugin.Groups, pluginIter, plugin.Name):
					self.Store.remove(pluginIter)
	
	def DoGroups(self, groupList, iter, pluginName):
		self.Plugins[pluginName] = {}
		pluginEmpty = True
		
		for groupName, group in groupList.items():
			groupEmpty = True
			groupIter = self.Store.append(iter)
			name = (groupName == '' and _("General") or groupName)
			self.Store.set(groupIter, 0, name, 6, False, 8, False, 9, False, 10, False, 11, False)
			self.Plugins[pluginName][groupName] = {}

			subGroupsSorted = sorted(group.items(), FirstItemSortCompare)
			for subGroupName, subGroup in subGroupsSorted:
				if subGroupName != '':
					subGroupIter = self.Store.append(groupIter)
					self.Store.set(subGroupIter, 0, subGroupName, 6, False, 8, False, 9, False, 10, False, 11, False)
				self.Plugins[pluginName][groupName][subGroupName] = {}
				subGroupEmpty = True
				
				settings = sum((v.values() for v in [subGroup.Display]+[subGroup.Screens[CurrentScreenNum]]), [])
				settings = sorted(FilterSettings(settings, self.Filter), SettingSortCompare)

				for setting in settings:
					if setting.Type == 'Action':
						if subGroupName != '':
							i = self.Store.append(subGroupIter)
						else:
							i = self.Store.append(groupIter)

						key, mods = gtk.accelerator_parse(setting.Value[0])
						edges = 'None'
						if len(setting.Value[3]) > 0:
							edges = " | ".join(setting.Value[3])

						edgeButton = setting.Value[4]
						if edgeButton != 0:
							edgeButton = _("Button %i") % edgeButton
						else:
							edgeButton = _("None")

						markup = "%s"
						if setting.Integrated:
							markup = "<span color='blue'>%s</span>"
						
						self.Store.set(i, 0, markup % setting.ShortDesc, 1, key, 2, mods, 3, setting.Value[1], 4,
									   edges, 5, edgeButton, 6, True, 7, setting.Value[2], 8, setting.Info[0], 9, setting.Info[1], 10,
									   setting.Info[3], 11, setting.Info[2], 12, groupName, 13, subGroupName, 14,
									   setting.Name, 15, pluginName)
						self.Plugins[pluginName][groupName][subGroupName][setting.Name] = setting
						
						groupEmpty = False
						subGroupEmpty = False
						pluginEmpty = False
						self.Empty = False
				
				if subGroupEmpty:
					if subGroupName != '':
						self.Store.remove(subGroupIter)
			if groupEmpty:
				self.Store.remove(groupIter)
		
		return not pluginEmpty
	
	def Activated(self, object, path, col):
		def ResetButton(object, setting, iter):
			if setting.Info[0]:
				keyEntry.set_text(setting.DefaultValue[0])
			if setting.Info[1]:
				buttonEntry.set_text(setting.DefaultValue[1])
			if setting.Info[2]:
				bellButton.set_active(setting.DefaultValue[2])
			if setting.Info[3]:
				children = edgeTable.get_children()
				edges = setting.DefaultValue[3]
				for checkBox in children:
					checkBox.set_active(False)
					for edge in edges:
						if checkBox.get_label() == edge:
							checkBox.set_active(True)
							break
				edgeButtonCombo.set_active(setting.DefaultValue[4])

		iter = self.Store.get_iter(path)
		store = self.Store.get(iter, 12, 13, 14, 15, 1, 2, 3, 4, 5, 7)
		groupName, subGroupName, settingName, pluginName, key, keyModifier, button, edges, edgeButton, bell = store

		if subGroupName is None or groupName is None or settingName is None:
			if self.TreeView.row_expanded(path):
				self.TreeView.collapse_row(path)
			else:
				self.TreeView.expand_row(path, False)
			return

		edges = edges.split(" | ")
		setting = self.Plugins[pluginName][groupName][subGroupName][settingName]

		dlg = gtk.Dialog(_("Edit Action: %s") % setting.ShortDesc)
		dlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
		dlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK).grab_default()
		dlg.set_default_response(gtk.RESPONSE_OK)
		table = gtk.Table()
		dlg.vbox.pack_start(table, False, False)
		
		# Key
		if setting.Info[0]:
			keyEntry = gtk.Entry()
			keyEntry.set_text(gtk.accelerator_name(key, keyModifier) or 'None')
			keyLabel = gtk.Label(_("Key"))
			keyLabel.props.xalign = 0
			table.attach(keyLabel, 0, 1, 0, 1, TableDef, TableDef, TableX, TableY)
			table.attach(keyEntry, 1, 2, 0, 1, TableDef, TableDef, TableX, TableY)
		
		# Button
		if setting.Info[1]:
			buttonEntry = gtk.Entry()
			buttonEntry.set_text(button)
			buttonLabel = gtk.Label(_("Button"))
			buttonLabel.props.xalign = 0
			table.attach(buttonLabel, 0, 1, 1, 2, TableDef, TableDef, TableX, TableY)
			table.attach(buttonEntry, 1, 2, 1, 2, TableDef, TableDef, TableX, TableY)
		
		# Edge + EdgeButton
		if setting.Info[3]:
			edgeTable = gtk.Table()
			row = 0
			col = 0
			for e in self.EdgeList:
				if e == 'None':
					continue
				
				edgeCheck = gtk.CheckButton(e)
				if edges.count(e) > 0:
					edgeCheck.set_active(True)
				edgeTable.attach(edgeCheck, col, col+1, row, row+1, TableDef, TableDef, TableX, TableY)

				col += 1
				if col > 2:
					row += 1
					col = 0

				if (row == 1 and col > 0):
					col += 1
					
			edgeLabel = gtk.Label(_("Screen Edges"))
			edgeLabel.props.xalign = 0
			table.attach(edgeLabel, 0, 1, 2, 3, TableDef, TableDef, TableX, TableY)
			table.attach(edgeTable, 1, 2, 2, 3, TableDef, TableDef, TableX, TableY)

			edgeButtonCombo = gtk.ComboBox(self.EdgeButtonStore)
			if edgeButton == _("None"):
				edgeButtonCombo.set_active(0)
			else:
				edgeButtonCombo.set_active(int(edgeButton[-1]))
			edgeButtonComboRenderer = gtk.CellRendererText()
			edgeButtonCombo.pack_start(edgeButtonComboRenderer)
			edgeButtonCombo.add_attribute(edgeButtonComboRenderer,'text',0)
			edgeButtonLabel = gtk.Label(_("Edge Button"))
			edgeButtonLabel.props.xalign = 0
			table.attach(edgeButtonLabel, 0, 1, 3, 4, TableDef, TableDef, TableX, TableY)
			table.attach(edgeButtonCombo, 1, 2, 3, 4, TableDef, TableDef, TableX, TableY)
		
		# Bell
		if setting.Info[2]:
			bellButton = gtk.CheckButton(_("On System Bell"))
			bellButton.set_active(bell)
			table.attach(bellButton, 0, 2, 4, 5, TableDef, TableDef, TableX, TableY)
		
		# Reset
		box = gtk.HBox()
		box.pack_start(Label(_("Reset To Defaults")), True, True)
		resetButton = gtk.Button()
		resetImage = gtk.Image()
		resetImage.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
		resetButton.set_image(resetImage)
		box.pack_end(resetButton, False, False)
		resetButton.connect('clicked', ResetButton, setting, iter)
		table.attach(box, 0, 2, 5, 6, TableDef, TableDef, TableX, TableY)
		
		dlg.show_all()
		resp = dlg.run()
		if setting.Info[0]:
			key = keyEntry.get_text()
		if setting.Info[1]:
			button = buttonEntry.get_text()
		if setting.Info[2]:
			bell = bellButton.get_active()
		if setting.Info[3]:
			children = edgeTable.get_children()
			edges = []
			for checkBox in children:
				if checkBox.get_active():
					edges.append(checkBox.get_label())
			edges = " | ".join(edges)
			edgeButton = edgeButtonCombo.get_active_text()
		
		dlg.destroy()
		if resp == gtk.RESPONSE_OK:
			if setting.Info[0]:
				akey, amods = gtk.accelerator_parse(key)
				self.Store.set(iter, 1, akey, 2, amods)
			if setting.Info[1]:
				self.Store.set(iter, 3, button)
			if setting.Info[2]:
				self.Store.set(iter, 7, bell)
			if setting.Info[3]:
				self.Store.set(iter, 4, edges)
				self.Store.set(iter, 5, edgeButton)
			self.WriteSetting(iter)
	
	def WriteSetting(self, iter):
		store = self.Store.get(iter, 12, 13, 14, 15, 1, 2, 3, 4, 5, 7)
		groupName, subGroupName, settingName, pluginName, key, keyModifier, button, edges, edgeButton, bell = store
		
		setting = self.Plugins[pluginName][groupName][subGroupName][settingName]
		realKey = gtk.accelerator_name(key, keyModifier)
		edges = edges.split(" | ")
		if edgeButton != _("None"):
			edgeButton = int(edgeButton[-1])
		else:
			edgeButton = 0
		
		conflict = ActionConflict(setting, realKey, button, bell, edges, edgeButton)
		if conflict.Resolve():
			setting.Value = [realKey, button, bell, edges, edgeButton]
			setting.Plugin.Context.Write()
			
		realKey, button, bell, edges, edgeButton = setting.Value
		key, keyModifier = gtk.accelerator_parse(realKey)
		if len(edges) > 0:
			edges = " | ".join(setting.Value[3])
		else:
			edges = 'None'
		if edgeButton != 0:
			edgeButton = _("Button %i") % edgeButton
		else:
			edgeButton = _("None")

		self.Store.set(iter, 1, key, 2, keyModifier, 3, button, 4, edges, 5, edgeButton, 7, bell)
	
	def KeyEdited(self, obj, path, key, mods, code):
		iter = self.Store.get_iter_from_string(path)
		self.Store.set(iter, 1, key, 2, mods)
		self.WriteSetting(iter)
	
	def KeyCleared(self, obj, path):
		iter = self.Store.get_iter_from_string(path)
		self.Store.set(iter, 1, 0, 2, 0)
		self.WriteSetting(iter)
	
	def ButtonEdited(self, obj, path, val):
		iter = self.Store.get_iter_from_string(path)
		self.Store.set(iter, 3, val)
		self.WriteSetting(iter)
	
	def EdgeEdited(self, obj, path, val):
		iter = self.Store.get_iter_from_string(path)
		self.Store.set(iter, 4, val)
		self.WriteSetting(iter)

	def EdgeButtonEdited(self, obj, path, val):
		iter = self.Store.get_iter_from_string(path)
		self.Store.set(iter, 5, val)
		self.WriteSetting(iter)
	
	def BellEdited(self, obj, path):
		iter = self.Store.get_iter_from_string(path)
		value = self.Store.get(iter, 7)[0]
		if value:
			value = False
		else:
			value = True
		self.Store.set(iter, 7, value)
		self.WriteSetting(iter)

# Plugin Page
#
class PluginPage:
	def __init__(self, plugin, main):
		self.Plugin = plugin
		self.Main = main
		self.LeftWidget = gtk.VBox(False, 10)
		self.LeftWidget.set_border_width(15)
		pluginLabel = Label()
		pluginLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Main.Style.BrightColor, plugin.ShortDesc))
		pluginImg = Image(plugin.Name, ImagePlugin, 64)
		filterLabel = Label()
		filterLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Main.Style.BrightColor, _("Filter")))
		if has_sexy:
			self.FilterEntry = sexy.IconEntry()
			self.FilterEntry.add_clear_button()
		else:
			self.FilterEntry = gtk.Entry()
		self.FilterEntry.connect("changed", self.FilterChanged)
		self.LeftWidget.pack_start(pluginImg, False, False)
		self.LeftWidget.pack_start(filterLabel, False, False)
		self.LeftWidget.pack_start(self.FilterEntry, False, False)
		self.LeftWidget.pack_start(pluginLabel, False, False)
		infoLabelCont = gtk.HBox()
		infoLabelCont.set_border_width(10)
		self.LeftWidget.pack_start(infoLabelCont, False, False)
		infoLabel = Label(plugin.LongDesc, 180)
		infoLabelCont.pack_start(infoLabel, True, True)

		self.NotFoundBox = None
		
		if plugin.Name != 'core':
			Tooltips.set_tip(self.FilterEntry, _("Search %s Plugin Options") % plugin.ShortDesc)
			enableLabel = Label()
			enableLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Main.Style.BrightColor, _("Use This Plugin")))
			self.LeftWidget.pack_start(enableLabel, False, False)
			enableCheckCont = gtk.HBox()
			enableCheckCont.set_border_width(10)
			self.LeftWidget.pack_start(enableCheckCont, False, False)
			enableCheck = gtk.CheckButton()
			enableCheck.add(Label(_("Enable %s") % plugin.ShortDesc, 120))
			Tooltips.set_tip(enableCheck, plugin.LongDesc)
			enableCheck.set_active(plugin.Enabled)
			enableCheck.set_sensitive(plugin.Context.AutoSort)
			enableCheckCont.pack_start(enableCheck, True, True)
			enableCheck.connect('toggled', self.EnablePlugin)
		else:
			Tooltips.set_tip(self.FilterEntry, _("Search Compiz Core Options"))
		
		backButton = gtk.Button(gtk.STOCK_GO_BACK)
		backButton.set_use_stock(True)
		self.LeftWidget.pack_end(backButton, False, False)
		backButton.connect('clicked', main.BackToMain)
		self.RightWidget = gtk.Notebook()
		self.Pages = []

		groupsSorted = sorted(plugin.Groups.items(), FirstItemSortCompare)
		for name, group in groupsSorted:
			name = name or _("General")
			groupPage = GroupPage(name, group)
			if not groupPage.Empty:
				self.RightWidget.append_page(groupPage.Widget, gtk.Label(name))
				self.Pages = self.Pages + [groupPage]
		
		self.ActionPage = ActionPage(self.Main.Context, plugin)
		if not self.ActionPage.Empty:
			self.RightWidget.append_page(self.ActionPage.Widget, gtk.Label(_("Actions")))
			self.Pages = self.Pages + [self.ActionPage]
		else:
			self.ActionPage = None
			self.RightWidget.connect('size-allocate', self.ResetFocus)

		self.Block = 0

	def ResetFocus(self, widget, data):
		pos = self.FilterEntry.get_position() 
		self.FilterEntry.grab_focus()
		self.FilterEntry.set_position(pos)

	def FilterChanged(self, widget):
		filter = widget.get_text().lower()
		if filter == "":
			filter = None

		groups = []

		for name, group in self.Plugin.Groups.items():
			name = name or _("General")
			groupPage = GroupPage(name, group, filter)
			if not groupPage.Empty:
				groups.append((name, groupPage))

		for page in self.RightWidget.get_children():
			label = self.RightWidget.get_tab_label(page).get_label()
			if label != _("Actions") and label != _("Error"):
				self.RightWidget.remove_page(self.RightWidget.page_num(page))
				page.destroy()

		for name, groupPage in groups:
			self.RightWidget.append_page(groupPage.Widget, gtk.Label(name))

		if self.ActionPage:
			self.ActionPage.Filter = filter
			self.ActionPage.UpdateTreeView()
			if self.ActionPage.Empty and self.ActionPage.Widget.get_parent():
				self.RightWidget.remove_page(self.RightWidget.page_num(self.ActionPage.Widget))
			elif not self.ActionPage.Empty and not self.ActionPage.Widget.get_parent():
				self.RightWidget.append_page(self.ActionPage.Widget, gtk.Label(_("Actions")))

		# Add
		if len(self.RightWidget.get_children()) == 0 and not self.NotFoundBox:
			self.NotFoundBox = NotFoundBox(filter)
			self.RightWidget.append_page(self.NotFoundBox, gtk.Label(_("Error")))
		# Update
		elif len(self.RightWidget.get_children()) == 1 and self.NotFoundBox:
			self.NotFoundBox.update(filter)
		# Cleanup
		elif len(self.RightWidget.get_children()) > 1 and self.NotFoundBox:
			self.RightWidget.remove_page(self.RightWidget.page_num(self.NotFoundBox))
			self.NotFoundBox.destroy()
			self.NotFoundBox = None

		self.RightWidget.show_all()

	def EnablePlugin(self, widget):
		if self.Block > 0:
			return
		self.Block += 1
		# attempt to resolve conflicts...
		conflicts = self.Plugin.Enabled and self.Plugin.DisableConflicts or self.Plugin.EnableConflicts
		conflict = PluginConflict(self.Plugin, conflicts)
		if conflict.Resolve():
			self.Plugin.Enabled = widget.get_active()
		else:
			widget.set_active(self.Plugin.Enabled)
		self.Plugin.Context.Write()
		self.Block = self.Block-1

# Filter Page
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

def PluginSortCompare(p1, p2):
	return cmp(p1.ShortDesc, p2.ShortDesc)

class FilterPage:
	def __init__(self, main, context):
		self.Context = context
		self.Main = main
		self.LeftWidget = gtk.VBox(False, 10)
		self.LeftWidget.set_border_width(15)
		self.RightWidget = gtk.Notebook()
		self.RightChild = gtk.VBox()

		# Image + Label
		filterLabel = Label()
		filterLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Main.Style.BrightColor, _("Filter")))
		filterImg = Image("search", ImageCategory, 64)
		self.LeftWidget.pack_start(filterImg, False, False)
		self.LeftWidget.pack_start(filterLabel, False, False)
		
		# Entry
		if has_sexy:
			filterEntry = sexy.IconEntry()
			filterEntry.add_clear_button()
		else:
			filterEntry = gtk.Entry()
		filterEntry.connect("changed", self.FilterChanged)
		self.LeftWidget.pack_start(filterEntry, False, False)

		# Search in...
		filterSearchLabel = Label()
		filterSearchLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Main.Style.BrightColor, _("Search in...")))
		self.LeftWidget.pack_start(filterSearchLabel, False, False)

		# Options
		self.FilterName = gtk.CheckButton()
		filterLabel = Label(_("Short description and name"))
		self.FilterName.add(filterLabel)
		self.FilterName.set_active(True)
		
		self.FilterLongDesc = gtk.CheckButton()
		filterLabel = Label(_("Long description"))
		self.FilterLongDesc.add(filterLabel)
		self.FilterLongDesc.set_active(True)
		
		self.FilterValue = gtk.CheckButton()
		filterLabel = Label(_("Settings value"))
		self.FilterValue.add(filterLabel)
		self.FilterValue.set_active(False)

		self.LeftWidget.pack_start(self.FilterName, False, False)
		self.LeftWidget.pack_start(self.FilterLongDesc, False, False)
		self.LeftWidget.pack_start(self.FilterValue, False, False)

		# Back Button
		self.BackButton = gtk.Button(gtk.STOCK_GO_BACK)
		self.BackButton.set_use_stock(True)
		self.BackButton.connect('clicked', self.Main.BackToMain)
		self.LeftWidget.pack_end(self.BackButton, False, False)

		self.FilteredPlugins = []
		self.Filter = None

		# Selector
		self.CurrentPlugin = None
		self.CurrentGroup = None
		self.CurrentSubGroup = None
		self.SelectorButtons = SelectorButtons()
		self.PluginBox = SelectorBox(main.Style.BackgroundColor)
		self.GroupBox = SelectorBox(main.Style.BackgroundColor)
		self.SubGroupBox = SelectorBox(main.Style.BackgroundColor)
		self.SelectorBoxes = gtk.HBox()
		self.SelectorBoxes.set_border_width(5)
		self.SelectorBoxes.set_spacing(5)
		self.PluginBox.set_no_show_all(True)
		self.GroupBox.set_no_show_all(True)
		self.SubGroupBox.set_no_show_all(True)
		self.SelectorBoxes.pack_start(self.PluginBox, False, False)
		self.SelectorBoxes.pack_start(self.GroupBox, False, False)
		self.SelectorBoxes.pack_start(self.SubGroupBox, False, False)
		self.RightChild.pack_start(self.SelectorButtons, False, False)
		self.RightChild.pack_start(self.SelectorBoxes, False, False)
		self.SettingsArea = gtk.ScrolledWindow()
		viewport = gtk.Viewport()
		self.SettingsBox = gtk.VBox()
		self.SettingsBox.set_border_width(5)
		self.SettingsBox.set_spacing(5)
		viewport.add(self.SettingsBox)
		self.SettingsArea.props.hscrollbar_policy = gtk.POLICY_NEVER
		self.SettingsArea.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
		self.SettingsArea.set_border_width(5)
		self.SettingsArea.add(viewport)
		self.SettingsArea.set_no_show_all(True)
		self.RightChild.pack_start(self.SettingsArea, True, True)

		self.ActionPage = ActionPage(self.Context)
		self.NotFoundBox = None

		# Notebook
		self.RightWidget.append_page(self.RightChild, gtk.Label(_("Settings")))
		self.RightWidget.append_page(self.ActionPage.Widget, gtk.Label(_("Actions")))

		self.FilterChanged(filterEntry)

	def UpdateBoxes(self):
		self.PluginBox.clear_list()
		self.GroupBox.clear_list()
		self.SubGroupBox.clear_list()
		for child in self.SettingsBox.get_children():
			child.destroy()

		singleGroup = None
		singleSubGroup = None
		
		# Plugins
		for plugin, groups in self.FilteredPlugins:
			if plugin.Enabled:
				self.PluginBox.add_item(plugin.ShortDesc, self.PluginChanged, "<b>%s</b>")
			else:
				self.PluginBox.add_item(plugin.ShortDesc, self.PluginChanged)
			# Groups
			if self.CurrentPlugin == plugin.ShortDesc:
				if len(groups) == 1:
					singleGroup = groups[0][0]

				groupsSorted = sorted(groups, FirstItemSortCompare)
				for group, subGroups in groupsSorted:
					self.GroupBox.add_item(group, self.GroupChanged)
					# SubGroups
					if self.CurrentGroup == group or singleGroup == group:
						if len(subGroups) == 1:
							singleSubGroup = subGroups[0][0]

						subGroupsSorted = sorted(subGroups, FirstItemSortCompare)
						for name, subGroup, settings in subGroupsSorted:
							self.SubGroupBox.add_item(name, self.SubGroupChanged)
							# Settings
							if self.CurrentSubGroup == name:
								sga = SubGroupArea('', subGroup, self.Filter)
								self.SettingsBox.pack_start(sga.Widget, False, False)
							elif self.CurrentSubGroup == None:
								sga = SubGroupArea(name, subGroup, self.Filter)
								self.SettingsBox.pack_start(sga.Widget, False, False)

		if len(self.FilteredPlugins) == 0:
			self.SelectorButtons.clear_buttons()
			self.CurrentPlugin = None
			self.CurrentGroup = None
			self.CurrentSubGroup = None

		self.PluginBox.hide()
		self.PluginBox.set_no_show_all(len(self.FilteredPlugins) == 0)
		self.GroupBox.hide()
		self.GroupBox.set_no_show_all(self.CurrentPlugin == None or singleGroup != None)
		self.SubGroupBox.hide()
		self.SubGroupBox.set_no_show_all(self.CurrentGroup == None or singleSubGroup != None)
		self.SettingsArea.hide()
		self.SettingsArea.set_no_show_all(len(self.SettingsBox.get_children()) == 0)

		self.RightChild.show_all()

		if self.CurrentPlugin != None and singleGroup != None:
			self.CurrentGroup = singleGroup

		if self.CurrentGroup != None and singleSubGroup != None:
			self.CurrentSubGroup = singleSubGroup

	def PluginChanged(self, widget, plugin):
		if self.CurrentSubGroup != None:
			self.SelectorButtons.remove_button(2)
		if self.CurrentGroup != None:
			self.SelectorButtons.remove_button(1)
		if self.CurrentPlugin != None:
			self.SelectorButtons.remove_button(0)

		self.CurrentPlugin = plugin
		self.CurrentGroup = None
		self.CurrentSubGroup = None

		self.SelectorButtons.add_button(plugin, self.PluginChanged)
		self.UpdateBoxes()

	def GroupChanged(self, widget, group):
		if self.CurrentSubGroup != None:
			self.SelectorButtons.remove_button(2)
		if self.CurrentGroup != None:
			self.SelectorButtons.remove_button(1)

		self.CurrentGroup = group
		self.CurrentSubGroup = None

		self.SelectorButtons.add_button(group or _("General"), self.GroupChanged)
		self.UpdateBoxes()

	def SubGroupChanged(self, widget, subGroup):
		if self.CurrentGroup != None:
			self.SelectorButtons.remove_button(2)

		self.CurrentSubGroup = subGroup

		self.SelectorButtons.add_button(subGroup or _("General"), self.SubGroupChanged)
		self.UpdateBoxes()

	def FilterChanged(self, widget):
		self.Filter = widget.get_text()
		runLevels = []
		if self.FilterName.get_active():
			runLevels.append(0)
		if self.FilterLongDesc.get_active():
			runLevels.append(1)
		if self.FilterValue.get_active():
			runLevels.append(2)
		plugins = []
		for plugin in sorted(self.Context.Plugins.values(), PluginSortCompare):
			groups = []
			for group in plugin.Groups:
				subGroups = []
				for name, subGroup in plugin.Groups[group].items():
					settings = sum((v.values() for v in [subGroup.Display]+[subGroup.Screens[CurrentScreenNum]]), [])
					settings = sorted(settings, SettingSortCompare)
					settings = FilterSettings(settings, self.Filter, run=runLevels, noActions=True, singleRun=True)
					if len(settings) > 0:
						subGroups.append((name, subGroup, settings))
				if len(subGroups) > 0:
					groups.append((group, subGroups))
			if len(groups) > 0:
				plugins.append((plugin, groups))

		self.FilteredPlugins = plugins
		self.UpdateBoxes()

		# No settings found, remove page
		if len(self.FilteredPlugins) == 0 and self.RightChild.get_parent():
			self.RightWidget.remove_page(self.RightWidget.page_num(self.RightChild))
		# Restore page
		elif len(self.FilteredPlugins) > 0 and not self.RightChild.get_parent():
			self.RightWidget.append_page(self.RightChild, gtk.Label(_("Settings")))

		self.ActionPage.Filter = self.Filter
		self.ActionPage.UpdateTreeView()
		# No actions found, remove page
		if self.ActionPage.Empty and self.ActionPage.Widget.get_parent():
			self.RightWidget.remove_page(self.RightWidget.page_num(self.ActionPage.Widget))
		# Restore page
		elif not self.ActionPage.Empty and not self.ActionPage.Widget.get_parent():
			self.RightWidget.append_page(self.ActionPage.Widget, gtk.Label(_("Actions")))

		# Nothing found
		if not self.RightChild.get_parent() and not self.ActionPage.Widget.get_parent():
			if self.NotFoundBox:
				self.NotFoundBox.update(self.Filter)
			else:
				self.NotFoundBox = NotFoundBox(self.Filter)
				self.RightWidget.append_page(self.NotFoundBox, gtk.Label(_("Error")))
		elif self.NotFoundBox:
			self.RightWidget.remove_page(self.RightWidget.page_num(self.NotFoundBox))
			self.NotFoundBox.destroy()
			self.NotFoundBox = None

		self.RightWidget.show_all()

# Profile and Backend Page
#
class ProfileBackendPage:
	def __init__(self, main, context):
		self.Context = context
		self.Main = main
		rightChild = gtk.VBox()
		rightChild.set_border_width(10)

		# Profiles
		profileBox = gtk.HBox()
		profileBox.set_spacing(5)
		profileAdd = gtk.Button()
		Tooltips.set_tip(profileAdd, _("Add a New Profile"))
		profileAdd.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
		profileRemove = gtk.Button()
		Tooltips.set_tip(profileRemove, _("Remove This Profile"))
		profileRemove.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON))
		self.ProfileComboBox = gtk.combo_box_new_text()
		self.ProfileComboBox.set_sensitive(self.Context.CurrentBackend.ProfileSupport)
		self.ProfileComboBox.append_text(_("Default"))
		for profile in self.Context.Profiles.values():
			self.ProfileComboBox.append_text(profile.Name)
		if self.Context.CurrentProfile.Name == '':
			self.ProfileComboBox.set_active(0)
		else:
			name = self.Context.CurrentProfile.Name
			index = self.Context.Profiles.values().index(self.Context.Profiles[name])
			self.ProfileComboBox.set_active(index+1)
		self.ProfileComboBox.connect("changed", self.ProfileChanged)
		profileAdd.connect("clicked", self.AddProfile)
		profileRemove.connect("clicked", self.RemoveProfile)
		profileBox.pack_start(self.ProfileComboBox, True, True)
		profileBox.pack_start(profileAdd, False, False)
		profileBox.pack_start(profileRemove, False, False)
		profileLabel = Label()
		profileLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Main.Style.BrightColor, _("Profile")))
		self.ProfileImportExportBox = gtk.HBox()
		self.ProfileImportExportBox.set_spacing(5)
		profileImportButton = gtk.Button(_("Import"))
		Tooltips.set_tip(profileImportButton, _("Import a CompizConfig Profile"))
		profileExportButton = gtk.Button(_("Export"))
		Tooltips.set_tip(profileExportButton, _("Export your CompizConfig Profile"))
		profileImportButton.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
		profileExportButton.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE, gtk.ICON_SIZE_BUTTON))
		profileImportButton.connect("clicked", self.ImportProfile)
		profileExportButton.connect("clicked", self.ExportProfile)
		self.ProfileImportExportBox.pack_start(profileImportButton, False, False)
		self.ProfileImportExportBox.pack_start(profileExportButton, False, False)
		rightChild.pack_start(profileLabel, False, False, 5)
		rightChild.pack_start(profileBox, False, False, 5)
		rightChild.pack_start(self.ProfileImportExportBox, False, False, 5)

		# Backends
		backendBox = gtk.combo_box_new_text()
		for backend in self.Context.Backends.values():
			backendBox.append_text(backend.ShortDesc)
		name = self.Context.CurrentBackend.Name
		index = self.Context.Backends.values().index(self.Context.Backends[name])
		backendBox.set_active(index)
		backendBox.connect("changed", self.BackendChanged)
		backendLabel = Label()
		backendLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Main.Style.BrightColor, _("Backend")))
		rightChild.pack_start(backendLabel, False, False, 5)
		rightChild.pack_start(backendBox, False, False, 5)

		# Integration
		integrationLabel = Label()
		integrationLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Main.Style.BrightColor, _("Integration")))
		self.IntegrationButton = gtk.CheckButton(_("Enable integration into the desktop environment"))
		self.IntegrationButton.set_active(self.Context.Integration)
		self.IntegrationButton.set_sensitive(self.Context.CurrentBackend.IntegrationSupport)
		self.IntegrationButton.connect("toggled", self.IntegrationChanged)
		rightChild.pack_start(integrationLabel, False, False, 5)
		rightChild.pack_start(self.IntegrationButton, False, False, 5)

		self.Widget = rightChild
	
	def UpdateProfiles(self, default = _("Default")):
		self.Context.Read()
		self.Context.UpdateProfiles()

		self.ProfileComboBox.get_model().clear()
		self.ProfileComboBox.append_text(_("Default"))
		for profile in self.Context.Profiles.values():
			self.ProfileComboBox.append_text(profile.Name)

		index = -1
		counter = 0
		for m in self.ProfileComboBox.get_model():
			if m[0] == default:
				index=counter
			counter += 1
		if index >= 0:
			self.ProfileComboBox.set_active(index)

	def IntegrationChanged(self, widget):
		value = widget.get_active()
		self.Context.Integration = value

	def ProfileChanged(self, widget):
		name = widget.get_active_text()
		if name == _("Default"):
			self.Context.ResetProfile()
		else:
			self.Context.CurrentProfile = self.Context.Profiles[name]
		
		self.Context.Read()
		self.Context.Write()

	def CreateFilter(self, chooser):
		filter = gtk.FileFilter()
		filter.add_pattern("*.profile")
		filter.set_name(_("Profiles (*.profile)"))
		chooser.add_filter(filter)

		filter = gtk.FileFilter()
		filter.add_pattern("*")
		filter.set_name(_("All files"))
		chooser.add_filter(filter)
	
	def ExportProfile(self, widget):
		b = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK)
		chooser = gtk.FileChooserDialog(title=_("Save file.."), parent=self.Main, buttons=b, action=gtk.FILE_CHOOSER_ACTION_SAVE)
		chooser.set_current_folder(os.environ.get("HOME"))
		self.CreateFilter(chooser)
		ret = chooser.run()

		path = chooser.get_filename()
		chooser.destroy()
		if ret == gtk.RESPONSE_OK:
			self.Context.Export(path)

	def ImportProfile(self, widget):
		b = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
		chooser = gtk.FileChooserDialog(title=_("Open file.."), parent=self.Main, buttons=b)
		chooser.set_current_folder(os.environ.get("HOME"))
		self.CreateFilter(chooser)
		ret = chooser.run()

		path = chooser.get_filename()
		chooser.destroy()
		if ret == gtk.RESPONSE_OK:
			self.Context.Import(path)

	def AddProfile(self, widget):
		dlg = gtk.Dialog(_("Enter a profile name"), self.Main, gtk.DIALOG_MODAL)
		dlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
		dlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
		
		entry = gtk.Entry()
		label = gtk.Label(_("Please enter a name for the new profile:"))
		dlg.vbox.pack_start(label, False, False, 5)
		dlg.vbox.pack_start(entry, False, False, 5)

		dlg.set_size_request(340, 120)
		dlg.show_all()
		ret = dlg.run()
		if ret == gtk.RESPONSE_OK:
			self.Context.CurrentProfile = ccs.Profile(self.Context, entry.get_text())
			self.UpdateProfiles(entry.get_text())
		dlg.destroy()
	
	def RemoveProfile(self, widget):
		name = self.ProfileComboBox.get_active_text()
		if name != _("Default"):
			self.Context.ResetProfile()
			self.Context.Profiles[name].Delete()
			self.UpdateProfiles()
	
	def BackendChanged(self, widget):
		shortDesc = widget.get_active_text()
		name = ""
		for backend in self.Context.Backends.values():
			if backend.ShortDesc == shortDesc:
				name = backend.Name
				break
		
		if name != "":
			self.Context.ResetProfile()
			self.Context.CurrentBackend = self.Context.Backends[name]
			self.UpdateProfiles()
		else:
			raise Exception, _("Backend not found.")

		self.ProfileComboBox.set_sensitive(self.Context.CurrentBackend.ProfileSupport)
		self.IntegrationButton.set_sensitive(self.Context.CurrentBackend.IntegrationSupport)

# ScrolledList Widget
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

# Plugin List Page
#
class PluginListPage:
	def __init__(self, main, context):
		self.Context = context
		self.Main = main
		self.Blocked = False
		rightChild = gtk.VBox()
		rightChild.set_border_width(10)
		
		# Auto sort
		autoSort = gtk.CheckButton(_("Automatically plugin sorting"))
		rightChild.pack_start(autoSort, False, False, 10)
		
		# Lists
		listBox = gtk.HBox()
		listBox.set_spacing(5)

		self.DisabledPluginsList = ScrolledList(_("Disabled Plugins"))
		self.EnabledPluginsList = ScrolledList(_("Enabled Plugins"))

		# Left/Right buttons
		buttonBox = gtk.VBox()
		buttonBox.set_spacing(5)
		boxAlignment = gtk.Alignment(0.0, 0.5, 0.0, 0.0)
		boxAlignment.add(buttonBox)

		rightButton = gtk.Button()
		rightImage = Image(gtk.STOCK_GO_FORWARD, ImageStock, gtk.ICON_SIZE_BUTTON)
		rightButton.set_image(rightImage)
		rightButton.connect("clicked", self.EnablePlugins)

		leftButton = gtk.Button()
		leftImage = Image(gtk.STOCK_GO_BACK, ImageStock, gtk.ICON_SIZE_BUTTON)
		leftButton.set_image(leftImage)
		leftButton.connect("clicked", self.EnabledPluginsList.delete)

		buttonBox.pack_start(rightButton, False, False)
		buttonBox.pack_start(leftButton, False, False)

		# Up/Down buttons
		enabledBox = gtk.VBox()
		enabledBox.set_spacing(10)

		enabledAlignment = gtk.Alignment(0.5, 0.0, 0.0, 0.0)
		enabledButtonBox = gtk.HBox()
		enabledButtonBox.set_spacing(5)
		enabledAlignment.add(enabledButtonBox)

		upButton = gtk.Button(gtk.STOCK_GO_UP)
		downButton = gtk.Button(gtk.STOCK_GO_DOWN)
		upButton.set_use_stock(True)
		downButton.set_use_stock(True)
		upButton.connect('clicked', self.EnabledPluginsList.move_up)
		downButton.connect('clicked', self.EnabledPluginsList.move_down)

		# Add buttons
		addButton = gtk.Button(gtk.STOCK_ADD)
		addButton.set_use_stock(True)
		addButton.connect('clicked', self.AddPlugin)

		enabledButtonBox.pack_start(addButton, False, False)
		enabledButtonBox.pack_start(upButton, False, False)
		enabledButtonBox.pack_start(downButton, False, False)

		enabledBox.pack_start(self.EnabledPluginsList, False, False)
		enabledBox.pack_start(enabledAlignment, False, False)

		listBox.pack_start(self.DisabledPluginsList, True, False)
		listBox.pack_start(boxAlignment, True, False)
		listBox.pack_start(enabledBox, True, False)

		self.UpdateEnabledPluginsList()
		self.UpdateDisabledPluginsList()

		# Connect Store
		self.EnabledPluginsList.Store.connect('row-changed', self.ListChanged)
		self.EnabledPluginsList.Store.connect('row-deleted', self.ListChanged)
		self.EnabledPluginsList.Store.connect('rows-reordered', self.ListChanged)

		rightChild.pack_start(listBox, False, False)

		# Auto sort
		autoSort.connect('toggled', self.AutoSortChanged)
		autoSort.set_active(self.Context.AutoSort)

		self.Widget = rightChild

	def AutoSortChanged(self, widget):
		self.Context.AutoSort = widget.get_active()
		self.EnabledPluginsList.set_sensitive(not self.Context.AutoSort)
		self.DisabledPluginsList.set_sensitive(not self.Context.AutoSort)

	def UpdateEnabledPluginsList(self):
		activePlugins = self.Context.Plugins['core'].Display['active_plugins'].Value
		
		self.EnabledPluginsList.clear()

		for name in activePlugins:
			self.EnabledPluginsList.append(name)

	def UpdateDisabledPluginsList(self):
		activePlugins = self.Context.Plugins['core'].Display['active_plugins'].Value

		self.DisabledPluginsList.clear()

		for plugin in sorted(self.Context.Plugins.values(), PluginSortCompare):
			if not plugin.Name in activePlugins:
				self.DisabledPluginsList.append(plugin.Name)

	def AddPlugin(self, widget):
		dlg = gtk.Dialog(_("Add plugin"))
		dlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
		dlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK).grab_default()
		dlg.set_default_response(gtk.RESPONSE_OK)
		
		ebox = gtk.EventBox()
		label = gtk.Label(_("Plugin name:"))
		ebox.add(label)
		
		Tooltips.set_tip(ebox, _("Insert plugin name"))
		dlg.vbox.pack_start(ebox)
		
		entry = gtk.Entry()
		entry.props.activates_default = True
		dlg.vbox.pack_start(entry)

		dlg.vbox.set_spacing(5)
		
		dlg.vbox.show_all()
		ret = dlg.run()
		dlg.destroy()

		if ret == gtk.RESPONSE_OK:
			self.EnabledPluginsList.append(entry.get_text())

	def EnablePlugins(self, widget):
		selectedRows = self.DisabledPluginsList.Select.get_selected_rows()[1]
		for path in selectedRows:
			iter = self.DisabledPluginsList.Store.get_iter(path)
			name = self.DisabledPluginsList.Store.get(iter, 0)[0]
			self.EnabledPluginsList.append(name)
		self.DisabledPluginsList.delete(widget)
	
	def ListChanged(self, *args, **kwargs):
		if self.Blocked:
			return
		self.Blocked = True
		plugins = self.EnabledPluginsList.get_list()

		self.Context.Plugins['core'].Display['active_plugins'].Value = plugins
		self.Context.Write()
		self.UpdateDisabledPluginsList()
		self.Blocked = False

# About Dialog
#
class AboutDialog(gtk.AboutDialog):
	def __init__(self):
		gtk.AboutDialog.__init__(self)

		self.set_name(_("CompizConfig Settings Manager"))
		self.set_version("0.1.0")
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

# Preferences Page
#
class PreferencesPage:
	def __init__(self, main, context):
		self.Context = context
		self.Main = main
		self.LeftWidget = gtk.VBox(False, 10)
		self.LeftWidget.set_border_width(15)
		self.RightWidget = gtk.Notebook()

		# Left Pane
		self.DescLabel = Label()
		self.DescLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Main.Style.BrightColor, _("Preferences")))
		self.DescImg = Image("profiles",ImageCategory, 64)
		self.LeftWidget.pack_start(self.DescImg, False, False)
		self.LeftWidget.pack_start(self.DescLabel, False, False)
		self.InfoLabelCont = gtk.HBox()
		self.InfoLabelCont.set_border_width(10)
		self.LeftWidget.pack_start(self.InfoLabelCont, False, False)
		self.InfoLabel = Label(_("Configure the backend, profile and other internal settings used by the Compiz Configuration System."), 180)
		self.InfoLabelCont.pack_start(self.InfoLabel, True, True)

		# About Button
		aboutLabel = Label()
		aboutLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Main.Style.BrightColor, _("About")))
		aboutButton = gtk.Button()
		aboutButton.set_relief(gtk.RELIEF_NONE)
		aboutImage = Image(gtk.STOCK_ABOUT, ImageStock, gtk.ICON_SIZE_BUTTON)
		aboutFrame = gtk.HBox()
		aboutFrame.set_spacing(5)
		aboutFrame.pack_start(aboutImage, False, False)
		aboutFrame.pack_start(Label(_("About CCSM...")), False, False)
		aboutButton.add(aboutFrame)
		Tooltips.set_tip(aboutButton, _("About"))
		aboutButton.connect('clicked', self.ShowAboutDialog)
		aboutBin = gtk.HBox()
		aboutBin.set_border_width(10)
		aboutBin.pack_start(aboutButton, False, False)
		self.LeftWidget.pack_start(aboutLabel, False, False)
		self.LeftWidget.pack_start(aboutBin, False, False)
	
		# Back Button
		backButton = gtk.Button(gtk.STOCK_GO_BACK)
		backButton.set_use_stock(True)
		backButton.connect('clicked', self.Main.BackToMain)
		self.LeftWidget.pack_end(backButton, False, False)

		# Profile & Backend Page
		self.ProfileBackendPage = ProfileBackendPage(main, context)
		self.RightWidget.append_page(self.ProfileBackendPage.Widget, gtk.Label(_("Profile & Backend")))

		# Plugin List
		self.PluginListPage = PluginListPage(main, context)
		self.RightWidget.append_page(self.PluginListPage.Widget, gtk.Label(_("Plugin List")))

	def ShowAboutDialog(self, widget):
		about = AboutDialog()
		about.show_all()
		about.run()
		about.destroy()

# Page
#
class Page:
	def __init__(self):
		self.Widget = gtk.VBox()
		self.SetContainer = gtk.VBox()
		
		scroll = gtk.ScrolledWindow()
		scroll.props.hscrollbar_policy = gtk.POLICY_NEVER
		scroll.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
		
		view = gtk.Viewport()
		view.set_border_width(5)
		view.set_shadow_type(gtk.SHADOW_NONE)
		
		scroll.add(view)
		view.add(self.SetContainer)
		self.Widget.pack_start(scroll, True, True)
		
		self.Empty = True

# Group Page
#
class GroupPage(Page):
	def __init__(self, name, group, filter=None):
		Page.__init__(self)

		self.subGroupAreas = []

		if (group.has_key('')):
			sga = SubGroupArea('', group[''], filter)
			if not sga.Empty:
				self.SetContainer.pack_start(sga.Widget, False, False)
				self.Empty = False
				self.subGroupAreas = self.subGroupAreas + [sga]

		subGroupsSorted = sorted(group.keys(), cmp)
		for subGroup in subGroupsSorted:
			if not subGroup == '':
				sga = SubGroupArea(subGroup, group[subGroup], filter)
				if not sga.Empty:
					self.SetContainer.pack_start(sga.Widget, False, False)
					self.Empty = False
					self.subGroupAreas = self.subGroupAreas + [sga]

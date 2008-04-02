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

import pygtk
import gtk
import gtk.gdk

from ccm.Pages import *
from ccm.Utils import *
from ccm.Constants import *
from ccm.Conflicts import *

import locale
import gettext
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("ccsm", DataDir + "/locale")
gettext.textdomain("ccsm")
_ = gettext.gettext

class MainWin(gtk.Window):

    currentCategory = None

    def __init__(self, Context, pluginPage=None, categoryName=None):
        gtk.Window.__init__(self)
        self.ShowingPlugin = None
        self.Context = Context
        self.connect("destroy", self.Quit)
        self.set_default_size(990, 580)
        self.set_title(_("CompizConfig Settings Manager"))
        
        # build the panes
        self.MainBox = gtk.HBox()
        self.add(self.MainBox)
        self.LeftPane = gtk.VBox()
        self.RightPane = gtk.VBox()
        self.RightPane.set_border_width(5)
        self.MainBox.pack_start(self.LeftPane, False, False)
        self.MainBox.pack_start(self.RightPane, True, True)
        self.Categories = {}
        self.PluginImages = {}

        for pluginName, plugin in self.Context.Plugins.items():
            self.PluginImages[pluginName] = Image(plugin.Name, ImagePlugin, size=32)
        
        for category in sorted(self.Context.Categories, key=self.CatKeyFunc):
            self.Categories[category] = []
            for pluginName, plugin in self.Context.Plugins.items():
                if plugin.Category == category:
                    self.Categories[category].append(plugin)
        
        self.BlockEnablePlugin = 0
        self.ResetMainWidgets()

        if pluginPage in self.Context.Plugins:
            self.ShowPlugin(None, self.Context.Plugins[pluginPage])
        if categoryName in self.Context.Categories:
            self.ToggleCategory(None, categoryName)

    def Quit(self, *args):
        gtk.main_quit()

    def ResetMainWidgets(self):
        pluginsVPort = gtk.Viewport()
        pluginsVPort.connect("style-set", self.ViewportStyleSet)
        leftChild = gtk.VBox(False, 10)
        leftChild.set_border_width(10)
        
        # Filter
        filterLabel = Label()
        filterLabel.set_markup(HeaderMarkup % (_("Filter")))
        filterLabel.connect("style-set", self.HeaderStyleSet)
        filterLabel.props.xalign = 0.1
        if has_sexy:
            filterEntry = sexy.IconEntry()
            filterEntry.add_clear_button()
        else:
            filterEntry = gtk.Entry()
        Tooltips.set_tip(filterEntry, _("Filter your Plugin list"))
        filterEntry.connect("changed", self.FilterTable)
        self.filterEntry = filterEntry
        leftChild.pack_start(filterLabel, False, False)
        leftChild.pack_start(filterEntry, False, False)

        # Screens
        if len(getScreens()) > 1:
            screenBox = gtk.combo_box_new_text()
            for screen in getScreens():
                screenBox.append_text(_("Screen %i") % screen)
            name = self.Context.CurrentBackend.Name
            screenBox.set_active(CurrentScreenNum)
            screenBox.connect("changed", self.ScreenChanged)
            screenLabel = Label()
            screenLabel.set_markup(HeaderMarkup % (_("Screen")))
            screenLabel.connect("style-set", self.HeaderStyleSet)
            leftChild.pack_start(screenLabel, False, False)
            leftChild.pack_start(screenBox, False, False)

        # Categories
        categoryBox = gtk.VBox()
        categoryBox.set_border_width(5)
        categories = ['All'] + sorted(self.Categories, key=self.CatKeyFunc)
        for category in categories:
            # name: untranslated name/interal identifier
            # label: translated name
            name = category or 'Uncategorized'
            label = _(name)
            iconName = name.lower ().replace (" ", "_")
            categoryToggleIcon = Image (name = iconName, type = ImageCategory,
                                        size = 22)
            categoryToggleLabel = Label (label)
            align = gtk.Alignment (0, 0.5, 1, 1)
            align.set_padding (0, 0, 0, 10)
            align.add (categoryToggleIcon)
            categoryToggleBox = gtk.HBox ()
            categoryToggleBox.pack_start (align, False, False)
            categoryToggleBox.pack_start (categoryToggleLabel, True, True)
            categoryToggle = PrettyButton ()
            categoryToggle.add(categoryToggleBox)
            categoryToggle.connect("clicked", self.ToggleCategory, category)
            categoryBox.pack_start(categoryToggle, False, False)
        categoryLabel = Label()
        categoryLabel.props.xalign = 0.1
        categoryLabel.set_markup(HeaderMarkup % (_("Category")))
        categoryLabel.connect("style-set", self.HeaderStyleSet)
        leftChild.pack_start(categoryLabel, False, False)
        leftChild.pack_start(categoryBox, False, False)

        # Exit Button
        exitButton = gtk.Button(gtk.STOCK_CLOSE)
        exitButton.set_use_stock(True)
        exitButton.connect('clicked', self.Quit)
        leftChild.pack_end(exitButton, False, False)

        # Advanced Search
        searchLabel = Label()
        searchLabel.set_markup(HeaderMarkup % (_("Advanced Search")))
        searchLabel.connect("style-set", self.HeaderStyleSet)
        searchImage = gtk.Image()
        searchImage.set_from_stock(gtk.STOCK_GO_FORWARD, gtk.ICON_SIZE_BUTTON)
        searchButton = gtk.Button()
        searchButton.connect("clicked", self.ShowAdvancedFilter)
        searchButton.set_relief(gtk.RELIEF_NONE)
        searchFrame = gtk.HBox()
        searchFrame.pack_start(searchLabel, False, False)
        searchFrame.pack_end(searchImage, False, False)
        searchButton.add(searchFrame)
        leftChild.pack_end(searchButton, False, False)

        # Preferences
        prefLabel = Label()
        prefLabel.set_markup(HeaderMarkup % (_("Preferences")))
        prefLabel.connect("style-set", self.HeaderStyleSet)
        prefImage = gtk.Image()
        prefImage.set_from_stock(gtk.STOCK_GO_FORWARD, gtk.ICON_SIZE_BUTTON)
        prefButton = gtk.Button()
        prefButton.connect("clicked", self.ShowPreferences)
        prefButton.set_relief(gtk.RELIEF_NONE)
        prefFrame = gtk.HBox()
        prefFrame.pack_start(prefLabel, False, False)
        prefFrame.pack_end(prefImage, False, False)
        prefButton.add(prefFrame)
        leftChild.pack_end(prefButton, False, False)

        rightChild = gtk.ScrolledWindow()
        rightChild.props.hscrollbar_policy = gtk.POLICY_NEVER
        rightChild.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        pluginsVPort.set_focus_vadjustment (rightChild.get_vadjustment ())
        rightChild.set_size_request (220,-1)
        rightChild.add(pluginsVPort)
        self.BuildTable(pluginsVPort)
        rightChild.connect('size-allocate', self.RebuildTable)

        self.LeftPane.pack_start(leftChild, True, True)
        self.RightPane.pack_start(rightChild, True, True)
        self.MainWidgets = (leftChild, rightChild)

        self.LeftPane.show_all()
        self.RightPane.show_all()
        self.LeftPane.set_size_request(self.LeftPane.size_request()[0], -1)

    StyleBlock = 0

    def HeaderStyleSet(self, widget, previous):
        if self.StyleBlock > 0:
            return
        self.StyleBlock += 1
        for state in (gtk.STATE_NORMAL, gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE):
            widget.modify_fg(state, widget.style.bg[gtk.STATE_SELECTED])
        self.StyleBlock -= 1

    def ViewportStyleSet(self, widget, previous):
        if self.StyleBlock > 0:
            return
        self.StyleBlock += 1
        widget.modify_bg(gtk.STATE_NORMAL, widget.style.base[gtk.STATE_NORMAL])
        self.StyleBlock -= 1

    def BuildTable(self, viewPort):
        pluginWindow = gtk.VBox()
        pluginWindow.set_border_width(10)
        viewPort.add(pluginWindow)

        self.TableCats = {}
        self.TableAttached = False
        self.LastCols = -1
        currentCategory = None
        for category in sorted(self.Categories, key=self.CatKeyFunc):
            if currentCategory:
                alignment = gtk.Alignment (0, 0, 1, 1)
                alignment.set_padding (0, 20, 0, 0)
                alignment.add (gtk.HSeparator ())
                categoryBox.pack_start (alignment)
                categoryBox.separatorAlignment = alignment
            currentCategory = category

            pluginList = sorted(self.Categories[category], key=PluginKeyFunc)

            categoryBox = gtk.VBox()
            categoryHeader = gtk.HBox()
            categoryHeader.set_spacing(10)
            categoryLabel = Label('', -1)
            pluginWindow.pack_start(categoryBox, False, False)

            name = category or 'Uncategorized'
            label = _(name)

            categoryLabel.set_markup("<span color='#aaa' size='x-large' weight='800'>%s</span>" % label)

            if category == "":
                iconName = "uncategorized"
            else:
                iconName = name.lower().replace (" ", "_")

            categoryImg = Image(iconName, ImageCategory)
            if categoryImg:
                categoryHeader.pack_start(categoryImg, False, False)
            categoryHeader.pack_start(categoryLabel, False, False)
            categoryBox.pack_start(categoryHeader, False, False)
            
            categoryTab = gtk.Table()
            categoryTab.set_border_width(10)
            self.TableCats[category] = (categoryTab, [], [])
            categoryBox.pack_start(categoryTab, False, False)
            
            for plugin in pluginList:
                pluginButton = PrettyButton ()
                pluginButton.connect('clicked', self.ShowPlugin, plugin)
                pluginButton.set_size_request(200, -1)
                pluginButtonBox = gtk.HBox(False, 10)
                pluginButtonBox.set_border_width(5)
                pluginImage = self.PluginImages[plugin.Name]
                pluginLabel = Label(plugin.ShortDesc, 120)
                pluginButtonBox.pack_start(pluginImage, False, False)
                pluginButtonBox.pack_start(pluginLabel, True, True)
                pluginButton.add(pluginButtonBox)
                pluginBox = gtk.HBox()

                if plugin.Name !=  'core':
                    pluginEnable = gtk.CheckButton()
                    PluginSetting (plugin, pluginEnable)
                    Tooltips.set_tip(pluginEnable, _("Enable %s") % plugin.ShortDesc)
                    pluginEnable.set_active(plugin.Enabled)
                    pluginEnable.connect("toggled", self.EnablePlugin, plugin)
                    pluginEnable.set_sensitive(self.Context.AutoSort)
                    pluginBox.pack_start(pluginEnable, False, False)

                Tooltips.set_tip(pluginButton, plugin.LongDesc)
                pluginBox.pack_start(pluginButton, True, True)
                pluginBox.set_size_request(220, -1)
                self.TableCats[category][1].append(pluginBox)
                self.TableCats[category][2].append(plugin)

    # targets:
    # 0 = plugin name and short description
    # 1 = plugin long description
    # 2 = category
    def FilterTable(self, widget, target = 0):
        text = widget.get_text().lower()
        cols = self.LastCols
        foundPlugin = False

        if self.TableAttached:
            for categoryName, categoryContainer in self.TableCats.items():
                for pluginButton in categoryContainer[1]:
                    if pluginButton.get_parent():
                        categoryContainer[0].remove(pluginButton)

        for categoryName, categoryContainer in self.TableCats.items():
            col = 0
            row = 0
            empty = True
            for pluginButton in categoryContainer[1]:
                if not self.currentCategory in (None, categoryName):
                    break
                index = categoryContainer[1].index(pluginButton)
                shortDesc = categoryContainer[2][index].ShortDesc.lower()
                longDesc = categoryContainer[2][index].LongDesc.lower()
                name = categoryContainer[2][index].Name.lower()
                category = categoryName.lower()
                show = False

                if target == 0:
                    show = name.find(text) != -1 \
                    or shortDesc.find(text) != -1
                elif target == 1:
                    show = name.find(text) != -1 \
                    or shortDesc.find(text) != -1 \
                    or longDesc.find(text) != -1
                elif target == 2:
                    show = category.find(text) != -1

                if show:
                    empty = False
                    foundPlugin = True
                    categoryContainer[0].attach(pluginButton, col, col+1, row, row+1, 0)
                    col = col+1
                    if col >=  cols:
                        col = 0
                        row = row+1

            categoryBox = categoryContainer[0].get_parent ()
            if empty:
                categoryBox.set_no_show_all(True)
                categoryBox.hide()
            else:
                categoryBox.set_no_show_all(False)
                categoryContainer[0].attach (gtk.Label (), cols + 5, cols + 6,
                                             0, 1, gtk.EXPAND)

            if hasattr (categoryBox, "separatorAlignment"):
                sep = categoryBox.separatorAlignment
                if self.currentCategory == categoryName:
                    sep.set_no_show_all (True)
                    sep.hide ()
                else:
                    sep.set_no_show_all (False)
    
        # Search in long description
        if not foundPlugin and target == 0:
            self.FilterTable(widget, 1)
        # Search in category
        elif not foundPlugin and target == 1:
            self.FilterTable(widget, 2)
        # Nothing found -- Ported from Gnome-Control-Center.
        elif not foundPlugin and target == 2:

            # Already created only update message
            if not self.TableAttached:
                notFound = self.MainWidgets[1].get_child().get_child().get_children()[-1]
                notFound.update(text)
                return
            
            self.TableAttached = False
            
            box = self.MainWidgets[1].get_child().get_child()
            notFound = NotFoundBox(text)
            box.pack_start(notFound, True, False)
            
            self.show_all()
        # Something found, display it
        elif foundPlugin:
            # Clean up not found Message
            if not self.TableAttached:
                self.MainWidgets[1].get_child().get_child().get_children()[-1].destroy()
            
            self.TableAttached = True
            self.show_all()

    def RebuildTable(self, widget, request):
        cols = (request.width - 40) / 220
        if cols == self.LastCols:
            return
        
        self.LastCols = cols
        if self.TableAttached:
            for categoryName, categoryContainer in self.TableCats.items():
                for pluginButton in categoryContainer[1]:
                    categoryContainer[0].remove(pluginButton)
        
        for categoryName, categoryContainer in self.TableCats.items():
            col = 0
            row = 0
            for pluginButton in categoryContainer[1]:
                categoryContainer[0].attach(pluginButton, col, col+1, row, row+1, 0)
                col = col+1
                if col >= cols:
                    col = 0
                    row = row+1
            categoryContainer[0].attach(gtk.Label(), cols+5, cols+6, 0, 1, gtk.EXPAND)
        self.TableAttached = True
        self.show_all()

    def SetMainWidgets(self, leftWidget, rightWidget):

        for widget in self.MainWidgets:
            widget.hide_all()
            widget.props.no_show_all = True

        self.LeftPane.pack_start(leftWidget, True, True)
        self.RightPane.pack_start(rightWidget, True, True)
        self.show_all()

        self.NonMainWidgets = leftWidget, rightWidget

    def CatKeyFunc(self, cat):
        if self.Context.Plugins['core'].Category == cat:
            return ''
        else:
            return cat or 'zzzzzzzz'

    def ShowPlugin(self, obj, select):
        pluginPage = PluginPage(select, self)
        self.ShowingPlugin = pluginPage
        self.SetMainWidgets(pluginPage.LeftWidget, pluginPage.RightWidget)
    
    def ShowAdvancedFilter(self, widget):
        filterPage = FilterPage(self, self.Context)
        self.SetMainWidgets(filterPage.LeftWidget, filterPage.RightWidget)
    
    def ShowPreferences(self, widget):
        preferencesPage = PreferencesPage(self, self.Context)
        self.SetMainWidgets(preferencesPage.LeftWidget, preferencesPage.RightWidget)

    def UpdatePlugins(self):
        for category, container, plugins in self.TableCats.values():
                for i in range(len(plugins)):
                    if plugins[i].Name != 'core':
                        check = container[i].get_children()[0]
                        self.BlockEnablePlugin += 1
                        check.set_active(plugins[i].Enabled)
                        self.BlockEnablePlugin -= 1
    
    def EnablePlugin(self, widget, plugin):
        if self.BlockEnablePlugin > 0:
            return
        self.BlockEnablePlugin += 1
        
        # attempt to resolve conflicts...
        conflicts = plugin.Enabled and plugin.DisableConflicts or plugin.EnableConflicts
        conflict = PluginConflict(plugin, conflicts)
        if conflict.Resolve():
            plugin.Enabled = widget.get_active()
            self.UpdatePlugins()
        else:
            widget.set_active(plugin.Enabled)
        plugin.Context.Write()
        
        self.BlockEnablePlugin -= 1

    def ToggleCategory(self, widget, category):
        self.currentCategory = category is not 'All' and category or None
        self.FilterTable (widget = self.filterEntry) 

    def ScreenChanged(self, widget):
        self.Context.Write()
        self.CurrentScreenNum = widget.get_active()
        self.Context.Read()

    def BackToMain(self, widget, run=0):
        # make sure its cleaned up here, since this is a nice safe place to do so
        for widget in self.NonMainWidgets:
            widget.get_parent().remove(widget)
            widget.destroy()
        self.NonMainWidgets = None

        for widget in self.MainWidgets:
            widget.props.no_show_all = False
            widget.show_all()

        self.ShowingPlugin = None

gtk.window_set_default_icon_name('ccsm')

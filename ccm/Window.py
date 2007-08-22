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

    currentCategory = ""

    def __init__(self, Context):
        gtk.Window.__init__(self)
        self.ShowingPlugin = None
        self.Context = Context
        self.connect("destroy", self.Quit)
        self.set_default_size(960, 580)
        self.set_title(_("CompizConfig Settings Manager"))
        try:
            self.set_icon (gtk.gdk.pixbuf_new_from_file(IconDir+"/apps/ccsm.svg"))
        except:
            pass
        
        self.Style = Style()
        
        # build the panes
        self.MainBox = gtk.HBox()
        self.add(self.MainBox)
        self.LeftPane = gtk.Alignment()
        self.LeftPane.set_size_request(230, 520)
        self.RightPane = gtk.Alignment()
        self.RightPane.set_border_width(5)
        self.RightPane.props.yscale = 1
        self.RightPane.props.xscale = 1
        self.RightPane.props.xalign = 0
        self.RightPane.props.yalign = 0
        self.LeftPane.props.yscale = 1
        self.LeftPane.props.xscale = 1
        self.LeftPane.props.xalign = 0
        self.LeftPane.props.yalign = 0
        self.MainBox.pack_start(self.LeftPane, False, False)
        self.MainBox.pack_start(self.RightPane, True, True)
        self.Categories = {}
        self.PluginImages = {}
        self.RightVadj = 0.0
        
        for pluginName, plugin in self.Context.Plugins.items():
            self.PluginImages[pluginName] = Image(plugin.Name, ImagePlugin)
        
        for category in sorted(self.Context.Categories, self.CatSortCompare):
            self.Categories[category] = []
            for pluginName, plugin in self.Context.Plugins.items():
                if plugin.Category == category:
                    self.Categories[category].append(plugin)
        
        self.BlockEnablePlugin = 0
        self.ResetMainWidgets()

    def Quit(self, foo):
        gtk.main_quit()

    def ResetMainWidgets(self):
        pluginsVPort = gtk.Viewport()
        leftChild = gtk.VBox(False, 10)
        leftChild.set_border_width(15)
        
        # Filter
        filterLabel = Label()
        filterLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Style.BrightColor, _("Filter")))
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
            screenLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Style.BrightColor, _("Screen")))
            leftChild.pack_start(screenLabel, False, False)
            leftChild.pack_start(screenBox, False, False)

        # Categories
        categoryBox = gtk.VBox()
        categoryBox.set_border_width(10)
        categories = [_("All")] + sorted(self.Categories, self.CatSortCompare)
        for category in categories:
            name = category or _("Uncategorized")
            categoryToggleLabel = Label(name)
            categoryToggle = gtk.Button()
            categoryToggle.set_relief(gtk.RELIEF_NONE)
            categoryToggle.add(categoryToggleLabel)
            categoryToggle.connect("clicked", self.ToggleCategory, category)
            categoryBox.pack_start(categoryToggle, False, False)
        categoryLabel = Label()
        categoryLabel.props.xalign = 0.1
        categoryLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Style.BrightColor, _("Category")))
        leftChild.pack_start(categoryLabel, False, False)
        leftChild.pack_start(categoryBox, False, False)

        # Exit Button
        exitButton = gtk.Button(gtk.STOCK_CLOSE)
        exitButton.set_use_stock(True)
        exitButton.connect('clicked', self.Quit)
        leftChild.pack_end(exitButton, False, False)

        # Advanced Search
        searchLabel = Label()
        searchLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Style.BrightColor, _("Advanced Search")))
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
        prefLabel.set_markup("<span color='%s' size='large' weight='800'>%s</span>" % (self.Style.BrightColor, _("Preferences")))
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

        pluginsVPort.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.Style.BackgroundColor))
        rightChild = gtk.ScrolledWindow()
        rightChild.props.hscrollbar_policy = gtk.POLICY_NEVER
        rightChild.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        rightChild.set_size_request(280,-1)
        rightChild.add(pluginsVPort)
        self.BuildTable(pluginsVPort)
        rightChild.connect('size-allocate', self.RebuildTable)
        self.SetMainWidgets(leftChild, rightChild)

    def BuildTable(self, viewPort):
        pluginWindow = gtk.VBox()
        pluginWindow.set_border_width(10)
        viewPort.add(pluginWindow)

        self.TableCats = {}
        self.TableAttached = False
        self.LastCols = -1
        for category in sorted(self.Categories, self.CatSortCompare):
            pluginList = sorted(self.Categories[category], PluginSortCompare)
            categoryBox = gtk.VBox()
            categoryHeader = gtk.HBox()
            categoryHeader.set_spacing(10)
            categoryLabel = Label('', -1)
            pluginWindow.pack_start(categoryBox, False, False)

            name = category or _("Uncategorized")
            categoryLabel.set_markup("<span color='#aaa' size='x-large' weight='800'>%s</span>" % name)
            categoryImg = Image(name.lower().replace(" ", "_"), ImageCategory)
            if categoryImg:
                categoryHeader.pack_start(categoryImg, False, False)
            categoryHeader.pack_start(categoryLabel, False, False)
            categoryBox.pack_start(categoryHeader, False, False)
            
            categoryTab = gtk.Table()
            categoryTab.set_border_width(10)
            self.TableCats[category] = (categoryTab, [], [])
            categoryBox.pack_start(categoryTab, False, False)
            
            for plugin in pluginList:
                pluginButton = gtk.Button()
                pluginButton.connect('clicked', self.ShowPlugin, plugin)
                pluginButton.set_size_request(200, -1)
                pluginButton.set_relief(gtk.RELIEF_NONE)
                pluginButtonBox = gtk.HBox(False, 10)
                pluginButtonBox.set_border_width(10)
                pluginImage = self.PluginImages[plugin.Name]
                pluginLabel = Label(plugin.ShortDesc, 120)
                pluginButtonBox.pack_start(pluginImage, False, False)
                pluginButtonBox.pack_start(pluginLabel, True, True)
                pluginButton.add(pluginButtonBox)
                pluginBox = gtk.HBox()

                if plugin.Name !=  'core':
                    pluginEnable = gtk.CheckButton()
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
                if not self.currentCategory in ("", categoryName):
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
            if empty:
                categoryContainer[0].get_parent().set_no_show_all(True)
                categoryContainer[0].get_parent().hide()
            else:
                categoryContainer[0].get_parent().set_no_show_all(False)
                categoryContainer[0].attach(gtk.Label(), cols+5, cols+6, 0, 1, gtk.EXPAND)
    
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
                notFound = self.RightPane.get_child().get_child().get_child().get_children()[-1]
                notFound.update(text)
                return
            
            self.TableAttached = False
            
            box = self.RightPane.get_child().get_child().get_child()
            notFound = NotFoundBox(text)
            box.pack_start(notFound, True, False)
            
            self.show_all()
        # Something found, display it
        elif foundPlugin:
            # Clean up not found Message
            if not self.TableAttached:
                self.RightPane.get_child().get_child().get_child().get_children()[-1].destroy()
            
            self.TableAttached = True
            self.show_all()

    def RebuildTable(self, widget, request):
        cols = (request.width - 60) / 220
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
        self.RightPane.get_child().props.vadjustment.value = self.RightVadj

    def SetMainWidgets(self, leftWidget, rightWidget):
        pane = self.LeftPane.get_child()
        if pane:
            pane.destroy()
        pane = self.RightPane.get_child()
        if (pane):
            pane.destroy()
        self.LeftPane.add(leftWidget)
        self.RightPane.add(rightWidget)
        self.show_all()

    def CatSortCompare(self, v1, v2):
        if v1 == v2:
            return cmp(v1, v2)
        if self.Context.Plugins['core'].Category == v1:
            return cmp('', v2 or 'zzzzzzzz')
        if self.Context.Plugins['core'].Category == v2:
            return cmp(v1 or 'zzzzzzz', '')
        return cmp(v1 or 'zzzzzzzz', v2 or 'zzzzzzzz')

    def ShowPlugin(self, obj, select):
        self.RightVadj = self.RightPane.get_child().get_vadjustment().get_value()
        for name, value in self.PluginImages.items():
            widget = value.get_parent()
            if widget:
                widget.remove(value)
        pluginPage = PluginPage(select, self)
        self.ShowingPlugin = pluginPage
        self.SetMainWidgets(pluginPage.LeftWidget, pluginPage.RightWidget)
    
    def ShowAdvancedFilter(self, widget, run=0):
        if run == 0: # Well thats rather a hack but it works...
            self.TitleBuffer = self.get_title()
            self.set_title(self.TitleBuffer + " - Loading...")
            gobject.timeout_add(100, self.ShowAdvancedFilter, widget, 1)
            return

        self.RightVadj = self.RightPane.get_child().get_vadjustment().get_value()
        for name, value in self.PluginImages.items():
            widget = value.get_parent()
            if widget:
                widget.remove(value)
        filterPage = FilterPage(self, self.Context)
        self.SetMainWidgets(filterPage.LeftWidget, filterPage.RightWidget)
    
        self.set_title(self.TitleBuffer)
        self.TitleBuffer = False

        return False
    
    def ShowPreferences(self, widget):
        self.RightVadj = self.RightPane.get_child().get_vadjustment().get_value()
        for name, value in self.PluginImages.items():
            widget = value.get_parent()
            if widget:
                widget.remove(value)
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

        # attempt to resolve conflicts...
        conflicts = plugin.Enabled and plugin.DisableConflicts or plugin.EnableConflicts
        conflict = PluginConflict(plugin, conflicts)
        if conflict.Resolve():
            plugin.Enabled = widget.get_active()
            self.UpdatePlugins()
        else:
            widget.set_active(plugin.Enabled)
        plugin.Context.Write()

    def ToggleCategory(self, widget, category):
        if category == _("All"):
            category = ""
        self.currentCategory = category
        self.FilterTable (widget = self.filterEntry) 

    def ScreenChanged(self, widget):
        self.Context.Write()
        self.CurrentScreenNum = widget.get_active()
        self.Context.Read()

    def BackToMain(self, obj):
        self.VisibleSettings = []
        self.ResetMainWidgets()
        del self.ShowingPlugin
        # make sure its cleaned up here, since this is a nice safe place to do so
        self.ShowingPlugin = None

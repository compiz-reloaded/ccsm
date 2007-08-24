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

import compizconfig
ccs = compizconfig

from ccm.Constants import *
from ccm.Settings import *
from ccm.Conflicts import *
from ccm.Utils import *
from ccm.Widgets import *

import locale
import gettext
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("ccsm", DataDir + "/locale")
gettext.textdomain("ccsm")
_ = gettext.gettext

CurrentUpdater = None

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
        self.RightWidget.set_scrollable(True)
        self.Pages = []

        groupsSorted = sorted(plugin.Groups.items(), FirstItemSortCompare)
        for name, group in groupsSorted:
            name = name or _("General")
            groupPage = GroupPage(name, group)
            if not groupPage.Empty:
                self.RightWidget.append_page(groupPage.Widget, gtk.Label(name))
                self.Pages = self.Pages + [groupPage]
        
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

        self.NotFoundBox = None

        # Notebook
        self.RightWidget.append_page(self.RightChild, gtk.Label(_("Settings")))

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
                    settings = FilterSettings(settings, self.Filter, run=runLevels, singleRun=True)
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

        # Nothing found
        if not self.RightChild.get_parent():
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
        if self.Context.CurrentProfile.Name == '' or self.Context.CurrentProfile.Name == 'Default':
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
        profileResetButton = gtk.Button(_("Reset to defaults"))
        Tooltips.set_tip(profileResetButton, _("Reset your CompizConfig Profile to the global defaults"))
        profileResetButton.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON))
        profileImportButton.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
        profileExportButton.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE, gtk.ICON_SIZE_BUTTON))
        profileImportButton.connect("clicked", self.ImportProfile)
        profileExportButton.connect("clicked", self.ExportProfile)
        profileResetButton.connect("clicked", self.ResetProfile)
        self.ProfileImportExportBox.pack_start(profileImportButton, False, False)
        self.ProfileImportExportBox.pack_start(profileExportButton, False, False)
        self.ProfileImportExportBox.pack_start(profileResetButton, False, False)
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

    def ResetProfile(self, widget):
        
        for plugin in self.Context.Plugins.values():
            settings = sum((v.values() for v in [plugin.Display]+[plugin.Screens[CurrentScreenNum]]), [])
            for setting in settings:
                setting.Reset()

        activePlugins = self.Context.Plugins['core'].Display['active_plugins'].Value
        for plugin in self.Context.Plugins.values():
            plugin.Enabled = plugin.Name in activePlugins
        self.Context.Write()
    
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
        autoSort = gtk.CheckButton(_("Automatic plugin sorting"))
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

        enabledBox.pack_start(self.EnabledPluginsList, True, True)
        enabledBox.pack_start(enabledAlignment, False, False)

        listBox.pack_start(self.DisabledPluginsList, True, True)
        listBox.pack_start(boxAlignment, True, False)
        listBox.pack_start(enabledBox, True, True)

        self.UpdateEnabledPluginsList()
        self.UpdateDisabledPluginsList()

        # Connect Store
        self.EnabledPluginsList.store.connect('row-changed', self.ListChanged)
        self.EnabledPluginsList.store.connect('row-deleted', self.ListChanged)
        self.EnabledPluginsList.store.connect('rows-reordered', self.ListChanged)

        rightChild.pack_start(listBox, True, True)

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
            if not plugin.Name in activePlugins and plugin.Name != "core":
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
        selectedRows = self.DisabledPluginsList.select.get_selected_rows()[1]
        for path in selectedRows:
            iter = self.DisabledPluginsList.store.get_iter(path)
            name = self.DisabledPluginsList.store.get(iter, 0)[0]
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

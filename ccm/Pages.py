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

from gi.repository import GObject, GLib, Gtk, Gdk

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

# Generic Page
#
class GenericPage(GObject.GObject):
    __gsignals__    = {"go-back" : (GObject.SignalFlags.RUN_FIRST,
                                    None,
                                    [])}

    LeftWidget = None
    RightWidget = None

    def __init__(self):
        GObject.GObject.__init__(self)

    def GoBack(self, widget):
        self.emit('go-back')

    def HeaderLabelSet(self, widget, label):
        self.HeaderStyleUpdated(widget, label)
        if Gtk.check_version(3, 16, 0) is None:
            widget.connect("style-updated", self.HeaderStyleUpdated, label)
        else:
            widget.connect("style-set", self.HeaderStyleSet, label)

    StyleBlock = 0
    def HeaderStyleUpdated(self, widget, label):
        if self.StyleBlock > 0:
            return
        self.StyleBlock += 1
        textRGB = None
        if Gtk.check_version(3, 6, 0) is None:
            style = widget.get_style_context ()
            style.save()
            style.add_class(Gtk.STYLE_CLASS_VIEW)
            bgColor = style.get_background_color(style.get_state())
            style.set_state(Gtk.StateFlags.SELECTED)
            textColor = style.get_background_color(style.get_state())
            if not textColor.equal(bgColor) and textColor.alpha != 0.0:
                textRGB = "#%.4X%.4X%.4X" % (int(textColor.red * 0xFFFF),
                                             int(textColor.green * 0xFFFF),
                                             int(textColor.blue * 0xFFFF))
                widget.set_markup(HeaderMarkup % (textRGB, label))
            else:
                widget.set_markup(HeaderMarkupDefault % label)
            style.restore()
        else:
            textColor = widget.get_style().lookup_color("selected_bg_color")
            if textColor[0] != False:
                textRGB = "#%.4X%.4X%.4X" % (textColor[1].red,
                                             textColor[1].green,
                                             textColor[1].blue)
                widget.set_markup(HeaderMarkup % (textRGB, label))
            else:
                widget.set_markup(HeaderMarkupDefault % label)
        self.StyleBlock -= 1

    if Gtk.check_version(3, 16, 0) is not None:
        def HeaderStyleSet(self, widget, previous, label):
            self.HeaderStyleUpdated(widget, label)

# Plugin Page
#
class PluginPage(GenericPage):

    def __init__(self, plugin):
        GenericPage.__init__(self)
        self.Plugin = plugin
        self.LeftWidget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                  homogeneous=False, spacing=10)
        if Gtk.check_version(3, 0, 0) is None:
            self.LeftWidget.props.margin = 10
        else:
            self.LeftWidget.set_border_width(10)

        pluginLabel = Label()
        self.HeaderLabelSet(pluginLabel, plugin.ShortDesc)
        pluginImg = Image(plugin.Name, ImagePlugin, 64)
        filterLabel = Label()
        self.HeaderLabelSet(filterLabel, _("Filter"))
        self.FilterEntry = ClearEntry()
        self.FilterEntry.connect("changed", self.FilterChanged)

        self.LeftWidget.pack_start(pluginImg, False, False, 0)
        self.LeftWidget.pack_start(filterLabel, False, False, 0)
        self.LeftWidget.pack_start(self.FilterEntry, False, False, 0)
        self.LeftWidget.pack_start(pluginLabel, False, False, 0)
        infoLabel = Label(plugin.LongDesc, 180)
        infoLabelCont = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if Gtk.check_version(3, 0, 0) is None:
            infoLabelCont.props.margin = 10
        else:
            infoLabelCont.set_border_width(10)
        infoLabelCont.pack_start(infoLabel, True, True, 0)
        self.LeftWidget.pack_start(infoLabelCont, False, False, 0)

        self.NotFoundBox = None

        if plugin.Name != 'core':
            self.FilterEntry.set_tooltip_text(_("Search %s Plugin Options") % plugin.ShortDesc)
            enableLabel = Label()
            enableLabel.title = _("Use This Plugin")
            self.HeaderLabelSet(enableLabel, _("Use This Plugin"))
            self.LeftWidget.pack_start(enableLabel, False, False, 0)
            enableCheckCont = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            if Gtk.check_version(3, 0, 0) is None:
                enableCheckCont.props.margin = 10
            else:
                enableCheckCont.set_border_width(10)
            self.LeftWidget.pack_start(enableCheckCont, False, False, 0)
            enableCheck = Gtk.CheckButton()
            enableCheck.add(Label(_("Enable %s") % plugin.ShortDesc, 120))
            enableCheck.set_tooltip_text(plugin.LongDesc)
            enableCheck.set_active(plugin.Enabled)
            enableCheck.set_sensitive(plugin.Context.AutoSort)
            enableCheckCont.pack_start(enableCheck, True, True, 0)
            enableCheck.connect('toggled', self.EnablePlugin)
        else:
            self.FilterEntry.set_tooltip_text(_("Search Compiz Core Options"))

        backButton = Gtk.Button.new_with_mnemonic(_("_Back"))
        backButton.set_image(Gtk.Image.new_from_icon_name("go-previous",
                                                          Gtk.IconSize.BUTTON))
        self.LeftWidget.pack_end(backButton, False, False, 0)
        backButton.connect('clicked', self.GoBack)
        self.RightWidget = Gtk.Notebook()
        self.RightWidget.set_scrollable(True)
        self.Pages = []

        sortedGroups = sorted(plugin.Groups.items(), key=GroupIndexKeyFunc)
        for (name, (groupIndex, group)) in sortedGroups:
            name = name or _("General")
            groupPage = GroupPage(name, group)
            groupPage.Wrap()
            if not groupPage.Empty:
                self.RightWidget.append_page(groupPage.Scroll,
                                             Gtk.Label(label=name))
                self.Pages.append(groupPage)

        self.Block = 0

    def GetPageSpot(self, new):
        vpos = 0 #visible position
        for page in self.Pages:
            if page is new:
                break
            if page.Visible:
                vpos += 1
        return vpos

    def ShowFilterError(self, text):

        if self.NotFoundBox is None:
            self.NotFoundBox = NotFoundBox(text)
            self.RightWidget.append_page(self.NotFoundBox,
                                         Gtk.Label(label=_("Error")))
        else:
            self.NotFoundBox.update(text)

    def HideFilterError(self):
        if self.NotFoundBox is None:
            return
        num = self.RightWidget.page_num(self.NotFoundBox)
        if num >= 0:
            self.RightWidget.remove_page(num)
        self.NotFoundBox.destroy()
        self.NotFoundBox = None

        self.RightWidget.set_current_page(0)

    def FilterChanged(self, widget):
        text = widget.get_text().lower()
        if text == "":
            text = None

        empty = True
        for page in self.Pages:
            num = self.RightWidget.page_num(page.Scroll)
            if page.Filter(text):
                empty = False
                if num < 0:
                    self.RightWidget.insert_page(page.Scroll,
                                                 Gtk.Label(label=page.Name),
                                                 self.GetPageSpot(page))
            else:
                if num >= 0:
                    self.RightWidget.remove_page(num)

        if empty:
            self.ShowFilterError(text)
        else:
            self.HideFilterError()

        self.RightWidget.show_all()

        # This seems to be necessary to ensure all gaps from hidden settings are removed on all tabs
        for page in self.Pages:
            page.Scroll.queue_resize_no_redraw()


    def EnablePlugin(self, widget):
        if self.Block > 0:
            return
        self.Block += 1
        # attempt to resolve conflicts...
        conflicts = self.Plugin.Enabled and self.Plugin.DisableConflicts or self.Plugin.EnableConflicts
        conflict = PluginConflict(widget.get_toplevel(), self.Plugin, conflicts)
        if conflict.Resolve():
            self.Plugin.Enabled = widget.get_active()
        else:
            widget.set_active(self.Plugin.Enabled)
        self.Plugin.Context.Write()
        self.Block -= 1
        GlobalUpdater.UpdatePlugins()

    # Checks if any edit dialog is open, and if so, makes sure a refresh
    # happens when it closes.
    def CheckDialogs(self, basePlugin, main):
        for groupPage in self.Pages:
            if isinstance(groupPage, GroupPage):
                for sga in groupPage.subGroupAreas:
                    for setting in sga.MySettings:
                        if isinstance(setting, BaseListSetting) and \
                        setting.EditDialog and setting.EditDialogOpen:
                            setting.PageToBeRefreshed = (self, basePlugin, main)
                            return False
        return True

    def RefreshPage(self, basePlugin, main):
        curPage = self.RightWidget.get_current_page ()
        main.BackToMain (None)
        main.MainPage.ShowPlugin (None, basePlugin)
        main.CurrentPage.RightWidget.set_current_page (curPage)

# Filter Page
#
class FilterPage(GenericPage):
    def __init__(self, context):
        GenericPage.__init__(self)
        self.Context = context
        self.LeftWidget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                  homogeneous=False, spacing=10)
        if Gtk.check_version(3, 0, 0) is None:
            self.LeftWidget.props.margin = 10
        else:
            self.LeftWidget.set_border_width(10)
        self.RightWidget = Gtk.Notebook()
        self.RightChild = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Image + Label
        filterLabel = Label()
        self.HeaderLabelSet(filterLabel, _("Filter"))
        filterImg = Image("search", ImageCategory, 64)
        self.LeftWidget.pack_start(filterImg, False, False, 0)
        self.LeftWidget.pack_start(filterLabel, False, False, 0)

        # Entry FIXME find a solution with std gtk
        self.FilterEntry = ClearEntry()
        self.FilterEntry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "input-keyboard")
        self.FilterEntry.set_icon_tooltip_text(Gtk.EntryIconPosition.PRIMARY, _("Grab Keys"))
        self.FilterEntry.connect('icon-press', self.GrabKey)

        self.FilterEntry.set_tooltip_text(_("Enter a filter.\nClick the keyboard image to grab a key for which to search."))
        self.FilterEntry.connect("changed", self.FilterChanged)
        self.LeftWidget.pack_start(self.FilterEntry, False, False, 0)

        # Search in...
        filterSearchLabel = Label()
        self.HeaderLabelSet(filterSearchLabel, _("Search in..."))
        self.LeftWidget.pack_start(filterSearchLabel, False, False, 0)

        # Options
        self.FilterNameCheck = check = Gtk.CheckButton(label=_("Short description and name"))
        check.set_active(True)
        check.connect("toggled", self.LevelChanged, FilterName)
        self.LeftWidget.pack_start(check, False, False, 0)

        self.FilterLongDescCheck = check = Gtk.CheckButton(label=_("Long description"))
        check.set_active(True)
        check.connect("toggled", self.LevelChanged, FilterLongDesc)
        self.LeftWidget.pack_start(check, False, False, 0)

        self.FilterValueCheck = check = Gtk.CheckButton(label=_("Settings value"))
        check.set_active(False)
        check.connect("toggled", self.LevelChanged, FilterValue)
        self.LeftWidget.pack_start(check, False, False, 0)

        # Back Button
        self.BackButton = Gtk.Button.new_with_mnemonic(_("_Back"))
        self.BackButton.set_image(Gtk.Image.new_from_icon_name("go-previous",
                                                               Gtk.IconSize.BUTTON))
        self.BackButton.connect('clicked', self.GoBack)
        self.LeftWidget.pack_end(self.BackButton, False, False, 0)

        self.NotFoundBox = None

        # Selector
        self.CurrentPlugin = None
        self.CurrentGroup = None
        self.CurrentSubGroup = None

        self.PackedPlugins = ()
        self.PackedGroups = ()
        self.PackedSubGroups = ()

        self.SelectorButtons = SelectorButtons()
        self.PluginBox = PluginView(context.Plugins)
        self.PluginBox.SelectionHandler = self.PluginChanged
        self.GroupBox = GroupView(_("Group"))
        self.GroupBox.SelectionHandler = self.GroupChanged
        self.SubGroupBox = GroupView(_("Subgroup"))
        self.SubGroupBox.SelectionHandler = self.SubGroupChanged

        self.SelectorButtons.set_size_request(-1, 50)

        self.SelectorBoxes = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if Gtk.check_version(3, 0, 0) is None:
            self.SelectorBoxes.props.margin = 5
        else:
            self.SelectorBoxes.set_border_width(5)
        self.SelectorBoxes.set_spacing(5)

        scroll = Gtk.ScrolledWindow()
        scroll.set_size_request(250, 180)
        scroll.props.hscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        scroll.props.vscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        scroll.add(self.PluginBox)
        self.SelectorBoxes.pack_start(scroll, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_size_request(220, 180)
        scroll.props.hscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        scroll.props.vscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        scroll.add(self.GroupBox)
        self.SelectorBoxes.pack_start(scroll, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.SubGroupBox)
        scroll.set_size_request(220, 180)
        scroll.props.hscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        scroll.props.vscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        self.SelectorBoxes.pack_start(scroll, False, False, 0)
        self.RightChild.pack_start(self.SelectorButtons, False, False, 0)
        self.RightChild.pack_start(self.SelectorBoxes, False, False, 0)
        self.SettingsArea = Gtk.ScrolledWindow()
        ebox = Gtk.EventBox()
        if Gtk.check_version (3, 0, 0) is None:
            ebox.get_style_context().add_class(Gtk.STYLE_CLASS_NOTEBOOK)
        self.SettingsBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        ebox.add(self.SettingsBox)
        self.SettingsArea.props.hscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        self.SettingsArea.props.vscrollbar_policy = Gtk.PolicyType.ALWAYS
        if Gtk.check_version (3, 8, 0) is None:
            self.SettingsBox.props.margin = 5
            self.SettingsArea.props.margin = 5
            self.SettingsArea.add(ebox)
        else:
            self.SettingsBox.set_border_width(5)
            self.SettingsArea.set_border_width(5)
            self.SettingsArea.add_with_viewport(ebox)
        self.RightChild.pack_start(self.SettingsArea, True, True, 0)

        GlobalUpdater.Block += 1

        # Notebook
        self.NotebookLabel = Gtk.Label(label=_("Settings"))
        self.NotebookChild = Gtk.EventBox()
        if Gtk.check_version (3, 0, 0) is None:
            self.NotebookChild.get_style_context().add_class(Gtk.STYLE_CLASS_NOTEBOOK)
        self.NotebookChild.add(self.RightChild)
        self.RightWidget.append_page(self.NotebookChild, self.NotebookLabel)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        if Gtk.check_version(3, 0, 0) is None:
            box.props.margin = 5
        else:
            box.set_border_width(5)
        progress = Popup(child=box)
        progress.connect("delete-event", lambda *a: True)
        progress.set_title(_("Loading Advanced Search"))
        bar = Gtk.ProgressBar()
        box.pack_start(bar, False, False, 0)

        label = Gtk.Label()
        label.set_max_width_chars(0)
        box.pack_start(label, False, False, 0)

        progress.set_size_request(300, -1)

        progress.show_all()

        self.GroupPages = {}

        length = len(context.Plugins)

        for index, n in enumerate(context.Plugins):
            plugin = context.Plugins[n]
            bar.set_fraction((index+1)/float(length))
            label.set_markup("<i>%s</i>" %protect_pango_markup(plugin.ShortDesc))
            gtk_process_events()

            groups = []
            sortedGroups = sorted(plugin.Groups.items(), key=GroupIndexKeyFunc)
            for (name, (groupIndex, group)) in sortedGroups:
                groups.append((name, GroupPage(name or _('General'), group)))
            self.GroupPages[n] = groups

        self.Level = FilterName | FilterLongDesc

        self.FilterChanged()

        progress.destroy()

        gtk_process_events()

        GlobalUpdater.Block -= 1

    def Filter(self, text, level=FilterAll):
        text = text.lower()
        for plugin in self.GroupPages:
            groups = self.GroupPages[plugin]
            results = dict((n, sg) for (n, sg) in groups if sg.Filter(text, level=level))
            if results:
                yield plugin, results

    def GotKey(self, widget, key, mods):
        new = GetAcceleratorName (key, mods)
        for mod in KeyModifier:
            if "%s_L" % mod in new:
                new = new.replace ("%s_L" % mod, "<%s>" % mod)
            if "%s_R" % mod in new:
                new = new.replace ("%s_R" % mod, "<%s>" % mod)

        widget.destroy()
        self.FilterValueCheck.set_active(True)
        self.FilterEntry.set_text(new)

    def GrabKey(self, widget, pos, event):
        if pos != Gtk.EntryIconPosition.PRIMARY:
            return
        grabber = KeyGrabber(label = _("Grab key combination"))
        self.LeftWidget.pack_start(grabber, False, False, 0)
        grabber.hide()
        grabber.set_no_show_all(True)
        grabber.connect('changed', self.GotKey)
        grabber.begin_key_grab(None)

    def ShowFilterError(self, text):

        if self.NotFoundBox is None:
            self.NotFoundBox = NotFoundBox(text)
            self.NotebookChild.remove(self.RightChild)
            self.NotebookChild.add(self.NotFoundBox)
            self.NotebookLabel.set_text(_("Error"))
            self.NotebookChild.show_all()
        else:
            self.NotFoundBox.update(text)

    def HideFilterError(self):
        if self.NotFoundBox is None:
            return
        num = self.RightWidget.page_num(self.NotFoundBox)
        if num >= 0:
            self.RightWidget.remove_page(num)

        self.NotebookChild.remove(self.NotFoundBox)
        self.NotebookChild.add(self.RightChild)

        self.NotFoundBox.destroy()
        self.NotFoundBox = None

        self.NotebookLabel.set_text(_("Settings"))

        self.NotebookChild.show_all()

    def UpdatePluginBox(self):
        self.PluginBox.Filter(self.Results)

        self.UpdateGroupBox()

    def UpdateGroupBox(self):
        if self.CurrentPlugin is not None and \
           self.CurrentPlugin.Name in self.Results:
            self.GroupBox.Update(self.Results[self.CurrentPlugin.Name])
        else:
            self.GroupBox.Update(())
        self.UpdateSubGroupBox()

    def UpdateSubGroupBox(self):
        if self.CurrentPlugin is not None and \
           self.CurrentPlugin.Name in self.Results and \
           self.CurrentGroup in self.Results[self.CurrentPlugin.Name]:
            grouppage = self.Results[self.CurrentPlugin.Name][self.CurrentGroup]
            self.SubGroupBox.Update(sga.Name for sga in grouppage.VisibleAreas)
        else:
            self.SubGroupBox.Update(())

    def UpdateSelectorButtons(self):
        self.SelectorButtons.clear_buttons()
        if self.CurrentPlugin is not None:
            self.SelectorButtons.add_button(self.CurrentPlugin.ShortDesc, self.PluginChanged)
            if self.CurrentGroup is not None:
                self.SelectorButtons.add_button(self.CurrentGroup or _("General"), self.GroupChanged)
                if self.CurrentSubGroup is not None:
                    self.SelectorButtons.add_button(self.CurrentSubGroup or _("General"), self.SubGroupChanged)

    def PluginChanged(self, plugin=None, selector=False):
        if not selector:
            self.CurrentPlugin = plugin
        self.CurrentGroup = None
        self.CurrentSubGroup = None

        self.UpdateSelectorButtons()
        if not selector:
            self.UpdateGroupBox()
        else:
            self.GroupBox.get_selection().unselect_all()
            self.UpdateSubGroupBox()

        if self.CurrentPlugin is not None:
            self.PackSettingsBox(plugins=[self.CurrentPlugin])
        else:
            self.PackSettingsBox()

        self.RightChild.show_all()

    def GroupChanged(self, group=None, selector=False):

        if group == 'All':
            self.PluginChanged(selector=True)
            return

        if not selector:
            self.CurrentGroup = group
        self.CurrentSubGroup = None

        self.UpdateSelectorButtons()

        if not selector:
            self.UpdateSubGroupBox()
        else:
            self.SubGroupBox.get_selection().unselect_all()

        if self.CurrentGroup is not None and self.CurrentGroup in self.Results[self.CurrentPlugin.Name]:
            page = self.Results[self.CurrentPlugin.Name][self.CurrentGroup]
            self.PackSettingsBox(groups=[page])
        else:
            self.PackSettingsBox()

        self.RightChild.show_all()

    def SubGroupChanged(self, subGroup=None, selector=False):

        if subGroup == 'All':
            self.GroupChanged(selector=True)
            return

        if not selector:
            self.CurrentSubGroup = subGroup

        self.UpdateSelectorButtons()

        if self.CurrentSubGroup is not None and self.CurrentGroup in self.Results[self.CurrentPlugin.Name]:
            sgas = self.Results[self.CurrentPlugin.Name][self.CurrentGroup].VisibleAreas
            sga = [sga for sga in sgas if sga.Name == self.CurrentSubGroup]
            self.PackSettingsBox(subgroups=sga)
        else:
            self.PackSettingsBox()
        self.RightChild.show_all()

    def LevelChanged(self, widget, level):

        if widget.get_active():
            if level & self.Level:
                return
            self.Level |= level
        else:
            if not level & self.Level:
                return
            self.Level &= ~level

        self.FilterChanged()

    def PackSettingsBox(self, plugins=None, groups=None, subgroups=None):

        for pluginbox in self.PackedPlugins:
            for child in pluginbox.get_children():
                pluginbox.remove(child)
            pluginbox.destroy()
        self.PackedPlugins = ()
        for group in self.PackedGroups:
            if group.Widget.get_parent():
                group.Widget.get_parent().remove(group.Widget)
        self.PackedGroups = ()
        for subgroup in self.PackedSubGroups:
            if subgroup.Widget.get_parent():
                subgroup.Widget.get_parent().remove(subgroup.Widget)
            subgroup.Widget.destroy()
        self.PackedSubGroups = ()

        if plugins is not None:
            self.PackedPlugins = []
            self.PackedGroups = []
            for plugin in plugins:
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                for (pageName, page) in self.GroupPages[plugin.Name]:
                    box.pack_start(page.Label, False, False, 0)
                    box.pack_start(page.Widget, False, False, 0)

                    self.PackedGroups.append(page)
                self.SettingsBox.pack_start(box, False, False, 0)
                self.PackedPlugins.append(box)

        if groups is not None:
            self.PackedGroups = []
            for page in groups:
                self.SettingsBox.pack_start(page.Widget, False, False, 0)
                self.PackedGroups.append(page)

        if subgroups is not None:
            self.PackedSubGroups = []
            for area in subgroups:
                sga = SubGroupArea('', area.SubGroup)
                sga.Filter(self.FilterEntry.get_text().lower())
                self.SettingsBox.pack_start(sga.Widget, False, False, 0)
                self.PackedSubGroups.append(sga)

        self.SettingsBox.show_all()

    def FilterChanged(self, widget=None):

        self.Results = dict(self.Filter(self.FilterEntry.get_text(), level=self.Level))

        self.PluginBox.Filter(self.Results)
        self.UpdateGroupBox()

        self.UpdateSelectorButtons()

        for sga in self.PackedSubGroups:
            sga.Filter(self.FilterEntry.get_text().lower())

        self.SettingsBox.queue_resize_no_redraw()

        self.RightWidget.show_all()

        if not self.Results:
            self.ShowFilterError(self.FilterEntry.get_text())
        elif self.NotFoundBox:
            self.HideFilterError()

    def GoBack(self, widget):
        for groups in self.GroupPages.values():
            for (pageName, page) in groups:
                page.SetContainer.destroy()
        self.GroupPages = None

        self.emit('go-back')

# Profile and Backend Page
#
class ProfileBackendPage(object):
    def __init__(self, context):
        self.Context = context
        rightChild = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        if Gtk.check_version(3, 0, 0) is None:
            rightChild.props.margin = 10
        else:
            rightChild.set_border_width(10)

        # Profiles
        profileBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        profileBox.set_spacing(5)
        profileAdd = Gtk.Button()
        profileAdd.set_tooltip_text(_("Add a New Profile"))
        profileAdd.set_image(Gtk.Image.new_from_icon_name("list-add",
                                                          Gtk.IconSize.BUTTON))
        self.ProfileRemoveButton = profileRemove = Gtk.Button()
        profileRemove.set_tooltip_text(_("Remove This Profile"))
        profileRemove.set_image(Gtk.Image.new_from_icon_name("list-remove",
                                                             Gtk.IconSize.BUTTON))
        self.ProfileComboBox = Gtk.ComboBoxText.new()
        self.ProfileComboBox.set_sensitive(self.Context.CurrentBackend.ProfileSupport)
        self.ProfileComboBox.append_text(_("Default"))
        active = -1
        for i, name in enumerate(self.Context.Profiles):
            profile = self.Context.Profiles[name]
            self.ProfileComboBox.append_text(profile.Name)
            if name == self.Context.CurrentProfile.Name:
                active = i
        self.ProfileHandler = self.ProfileComboBox.connect("changed",
            self.ProfileChangedAddTimeout)
        self.ProfileComboBox.set_active(active+1)
        profileAdd.connect("clicked", self.AddProfile)
        profileRemove.connect("clicked", self.RemoveProfile)
        profileBox.pack_start(self.ProfileComboBox, True, True, 0)
        profileBox.pack_start(profileAdd, False, False, 0)
        profileBox.pack_start(profileRemove, False, False, 0)
        profileLabel = Label()
        self.HeaderLabelSet(profileLabel, _("Profile"))
        self.ProfileImportExportBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.ProfileImportExportBox.set_spacing(5)
        profileImportButton = Gtk.Button(label=_("Import"))
        profileImportButton.set_tooltip_text(_("Import a CompizConfig Profile"))
        profileImportAsButton = Gtk.Button(label=_("Import as..."))
        profileImportAsButton.set_tooltip_text(_("Import a CompizConfig Profile as a new profile"))
        profileExportButton = Gtk.Button(label=_("Export"))
        profileExportButton.set_tooltip_text(_("Export your CompizConfig Profile"))
        profileResetButton = Gtk.Button(label=_("Reset to defaults"))
        profileResetButton.set_tooltip_text(_("Reset your CompizConfig Profile to the global defaults"))
        profileResetButton.set_image(Gtk.Image.new_from_icon_name("edit-clear",
                                                                  Gtk.IconSize.BUTTON))
        profileImportButton.set_image(Gtk.Image.new_from_icon_name("document-open",
                                                                   Gtk.IconSize.BUTTON))
        profileImportAsButton.set_image(Gtk.Image.new_from_icon_name("document-open",
                                                                     Gtk.IconSize.BUTTON))
        profileExportButton.set_image(Gtk.Image.new_from_icon_name("document-save",
                                                                   Gtk.IconSize.BUTTON))
        profileImportButton.connect("clicked", self.ImportProfile)
        profileImportAsButton.connect("clicked", self.ImportProfileAs)
        profileExportButton.connect("clicked", self.ExportProfile)
        profileResetButton.connect("clicked", self.ResetProfile)
        self.ProfileImportExportBox.pack_start(profileImportButton, False, False, 0)
        self.ProfileImportExportBox.pack_start(profileImportAsButton, False, False, 0)
        self.ProfileImportExportBox.pack_start(profileExportButton, False, False, 0)
        self.ProfileImportExportBox.pack_start(profileResetButton, False, False, 0)
        rightChild.pack_start(profileLabel, False, False, 5)
        rightChild.pack_start(profileBox, False, False, 5)
        rightChild.pack_start(self.ProfileImportExportBox, False, False, 5)

        # Backends
        backendBox = Gtk.ComboBoxText.new()
        active = 0
        for i, name in enumerate(self.Context.Backends):
            backend = self.Context.Backends[name]
            backendBox.append_text(backend.ShortDesc)
            if name == self.Context.CurrentBackend.Name:
                active = i
        backendBox.set_active(active)
        backendBox.connect("changed", self.BackendChangedAddTimeout)
        backendLabel = Label()
        self.HeaderLabelSet(backendLabel, _("Backend"))
        rightChild.pack_start(backendLabel, False, False, 5)
        rightChild.pack_start(backendBox, False, False, 5)

        # Integration
        integrationLabel = Label()
        self.HeaderLabelSet(integrationLabel, _("Integration"))
        self.IntegrationButton = Gtk.CheckButton(label=_("Enable integration into the desktop environment"))
        self.IntegrationButton.set_active(self.Context.Integration)
        self.IntegrationButton.set_sensitive(self.Context.CurrentBackend.IntegrationSupport)
        self.IntegrationButton.connect("toggled", self.IntegrationChanged)
        rightChild.pack_start(integrationLabel, False, False, 5)
        rightChild.pack_start(self.IntegrationButton, False, False, 5)

        self.Widget = rightChild

    def HeaderLabelSet(self, widget, label):
        self.HeaderStyleUpdated(widget, label)
        if Gtk.check_version(3, 16, 0) is None:
            widget.connect("style-updated", self.HeaderStyleUpdated, label)
        else:
            widget.connect("style-set", self.HeaderStyleSet, label)

    StyleBlock = 0
    def HeaderStyleUpdated(self, widget, label):
        if self.StyleBlock > 0:
            return
        self.StyleBlock += 1
        textRGB = None
        if Gtk.check_version(3, 6, 0) is None:
            style = widget.get_style_context ()
            style.save()
            style.add_class(Gtk.STYLE_CLASS_VIEW)
            bgColor = style.get_background_color(style.get_state())
            style.set_state(Gtk.StateFlags.SELECTED)
            textColor = style.get_background_color(style.get_state())
            if not textColor.equal(bgColor) and textColor.alpha != 0.0:
                textRGB = "#%.4X%.4X%.4X" % (int(textColor.red * 0xFFFF),
                                             int(textColor.green * 0xFFFF),
                                             int(textColor.blue * 0xFFFF))
                widget.set_markup(HeaderMarkup % (textRGB, label))
            else:
                widget.set_markup(HeaderMarkupDefault % label)
            style.restore()
        else:
            textColor = widget.get_style().lookup_color("selected_bg_color")
            if textColor[0] != False:
                textRGB = "#%.4X%.4X%.4X" % (textColor[1].red,
                                             textColor[1].green,
                                             textColor[1].blue)
                widget.set_markup(HeaderMarkup % (textRGB, label))
            else:
                widget.set_markup(HeaderMarkupDefault % label)
        self.StyleBlock -= 1

    if Gtk.check_version(3, 16, 0) is not None:
        def HeaderStyleSet(self, widget, previous, label):
            self.HeaderStyleUpdated(widget, label)

    def UpdateProfiles (self, current=_("Default")):

        self.ProfileComboBox.handler_block (self.ProfileHandler)

        self.Context.Read ()
        self.Context.UpdateProfiles ()

        self.ProfileComboBox.get_model ().clear ()
        set = False
        for index, profile in enumerate ([_("Default")] + list (self.Context.Profiles)):
            self.ProfileComboBox.append_text (profile)
            if profile == current and not set:
                self.ProfileComboBox.set_active (index)
                set = True
        self.ProfileRemoveButton.set_sensitive (self.ProfileComboBox.get_active() != 0)

        self.ProfileComboBox.handler_unblock (self.ProfileHandler)

        GlobalUpdater.UpdatePlugins()

    def IntegrationChanged(self, widget):
        value = widget.get_active()
        self.Context.Integration = value

    def ProfileChanged(self, widget):
        try:
            name = widget.do_get_active_text(widget)
        except (AttributeError, NameError, TypeError):
            name = widget.get_active_text()
        if name == _("Default"):
            self.Context.ResetProfile()
        elif name in self.Context.Profiles:
            self.Context.CurrentProfile = self.Context.Profiles[name]
        else:
            self.ProfileComboBox.set_active (0)
            return

        self.ProfileRemoveButton.set_sensitive (self.ProfileComboBox.get_active() != 0)

        self.Context.Read()
        self.Context.Write()
        GlobalUpdater.UpdatePlugins()
        return False

    def ProfileChangedAddTimeout(self, widget):
        GLib.timeout_add (500, self.ProfileChanged, widget)

    def CreateFilter(self, chooser):
        filter = Gtk.FileFilter()
        filter.add_pattern("*.profile")
        filter.set_name(_("Profiles (*.profile)"))
        chooser.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.add_pattern("*")
        filter.set_name(_("All files"))
        chooser.add_filter(filter)

    def ResetProfile(self, widget):

        for plugin in self.Context.Plugins.values():
            settings = GetSettings(plugin)
            for setting in settings:
                setting.Reset()

        # Compiz 0.9.x and Compiz 0.8.x compatibility.
        try:
            activePlugins = self.Context.Plugins['core'].Screen['active_plugins'].Value
        except (AttributeError, TypeError):
            activePlugins = self.Context.Plugins['core'].Display['active_plugins'].Value
        for plugin in self.Context.Plugins.values():
            plugin.Enabled = plugin.Name in activePlugins
        self.Context.Write()
        GlobalUpdater.UpdatePlugins()

    def ExportProfile(self, widget):
        main = widget.get_toplevel()
        chooser = Gtk.FileChooserDialog(title=_("Save file.."),
                                        transient_for=main,
                                        action=Gtk.FileChooserAction.SAVE)

        button = chooser.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)
        button.set_image(Gtk.Image.new_from_icon_name("gtk-cancel",
                                                      Gtk.IconSize.BUTTON))
        button = chooser.add_button(_("_Save"), Gtk.ResponseType.OK)
        button.set_image(Gtk.Image.new_from_icon_name("document-save",
                                                      Gtk.IconSize.BUTTON))
        button.grab_default()
        chooser.set_default_response(Gtk.ResponseType.OK)

        chooser.set_current_folder(os.environ.get("HOME"))
        self.CreateFilter(chooser)
        ret = chooser.run()

        path = chooser.get_filename()
        chooser.destroy()
        if ret == Gtk.ResponseType.OK:
            dlg = Gtk.MessageDialog(message_type=Gtk.MessageType.QUESTION,
                                    buttons=Gtk.ButtonsType.YES_NO,
                                    transient_for=main)
            dlg.set_markup(_("Do you want to skip default option values while exporting your profile?"))
            ret = dlg.run()
            dlg.destroy()
            if not path.endswith(".profile"):
                path = "%s.profile" % path
            self.Context.Export(path, ret == Gtk.ResponseType.YES)

    def ImportProfileDialog (self, main):
        chooser = Gtk.FileChooserDialog (title=_("Open file.."),
                                         transient_for=main)

        button = chooser.add_button (_("_Cancel"), Gtk.ResponseType.CANCEL)
        button.set_image (Gtk.Image.new_from_icon_name ("gtk-cancel",
                                                        Gtk.IconSize.BUTTON))
        button = chooser.add_button (_("_Open"), Gtk.ResponseType.OK)
        button.set_image (Gtk.Image.new_from_icon_name ("document-open",
                                                        Gtk.IconSize.BUTTON))
        button.grab_default ()
        chooser.set_default_response (Gtk.ResponseType.OK)

        chooser.set_current_folder (os.environ.get ("HOME"))
        self.CreateFilter (chooser)
        ret = chooser.run ()

        path = chooser.get_filename ()
        chooser.destroy ()
        if ret == Gtk.ResponseType.OK:
            return path
        return None

    def ProfileNameDialog (self, main):
        dlg = Gtk.Dialog (title=_("Enter a profile name"),
                          transient_for=main, modal=True)

        button = dlg.add_button (_("_Cancel"), Gtk.ResponseType.CANCEL)
        button.set_image (Gtk.Image.new_from_icon_name ("gtk-cancel",
                                                        Gtk.IconSize.BUTTON))
        button = dlg.add_button (_("_Add"), Gtk.ResponseType.OK)
        button.set_image (Gtk.Image.new_from_icon_name ("list-add",
                                                        Gtk.IconSize.BUTTON))
        button.grab_default ()
        dlg.set_default_response (Gtk.ResponseType.OK)

        entry = Gtk.Entry ()
        label = Gtk.Label (label=_("Please enter a name for the new profile:"))
        dlg.vbox.pack_start (label, False, False, 5)
        dlg.vbox.pack_start (entry, False, False, 5)

        dlg.set_size_request (340, 120)
        dlg.show_all ()
        ret = dlg.run ()
        text = entry.get_text ()
        dlg.destroy()
        if ret == Gtk.ResponseType.OK:
            return text
        return None

    def ImportProfile (self, widget):
        main = widget.get_toplevel ()
        path = self.ImportProfileDialog (main)
        if path:
            self.Context.Import (path)
        GlobalUpdater.UpdatePlugins()

    def ImportProfileAs (self, widget):
        main = widget.get_toplevel ()
        path = self.ImportProfileDialog (main)
        if not path:
            return
        name = self.ProfileNameDialog (main)
        if not name:
            return
        self.Context.CurrentProfile = ccs.Profile (self.Context, name)
        self.UpdateProfiles (name)
        self.Context.Import (path)

    def AddProfile (self, widget):
        main = widget.get_toplevel ()
        name = self.ProfileNameDialog (main)
        if name:
            self.Context.CurrentProfile = ccs.Profile (self.Context, name)
            self.UpdateProfiles (name)

    def RemoveProfile(self, widget):
        try:
            name = self.ProfileComboBox.do_get_active_text(self.ProfileComboBox)
        except (AttributeError, NameError, TypeError):
            name = self.ProfileComboBox.get_active_text()
        if name != _("Default"):
            self.Context.ResetProfile()
            self.Context.Profiles[name].Delete()
            self.UpdateProfiles()

    def BackendChanged(self, widget):
        try:
            shortDesc = widget.do_get_active_text(widget)
        except (AttributeError, NameError, TypeError):
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
            raise Exception(_("Backend not found."))

        self.ProfileComboBox.set_sensitive(self.Context.CurrentBackend.ProfileSupport)
        self.IntegrationButton.set_sensitive(self.Context.CurrentBackend.IntegrationSupport)
        GlobalUpdater.UpdatePlugins()
        return False

    def BackendChangedAddTimeout(self, widget):
        GLib.timeout_add (500, self.BackendChanged, widget)

# Plugin List Page
#
class PluginListPage(object):
    def __init__(self, context):
        self.Context = context
        self.Block = 0
        rightChild = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        if Gtk.check_version(3, 0, 0) is None:
            rightChild.props.margin = 10
        else:
            rightChild.set_border_width(10)

        # Auto sort
        autoSort = Gtk.CheckButton(label=_("Automatic plugin sorting"))
        rightChild.pack_start(autoSort, False, False, 10)

        # Lists
        listBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        listBox.set_spacing(5)

        self.DisabledPluginsList = ScrolledList(_("Disabled Plugins"))
        self.DisabledPluginsList.set_shadow_type(Gtk.ShadowType.IN)

        self.EnabledPluginsList = ScrolledList(_("Enabled Plugins"))
        self.EnabledPluginsList.set_shadow_type(Gtk.ShadowType.IN)

        # Left/Right buttons
        buttonBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        buttonBox.set_spacing(5)
        if Gtk.check_version(3, 0, 0) is None:
            buttonBox.set_valign(Gtk.Align.CENTER)
        else:
            boxAlignment = Gtk.Alignment(yalign=0.5, xscale=0.0, yscale=0.0)
            boxAlignment.add(buttonBox)
        self.MiddleButtonBox = buttonBox

        rightButton = Gtk.Button()
        rightImage = Gtk.Image.new_from_icon_name("go-next",
                                                  Gtk.IconSize.BUTTON)
        rightButton.set_image(rightImage)
        rightButton.connect("clicked", self.EnablePlugins)

        leftButton = Gtk.Button()
        leftImage = Gtk.Image.new_from_icon_name("go-previous",
                                                 Gtk.IconSize.BUTTON)
        leftButton.set_image(leftImage)
        leftButton.connect("clicked", self.EnabledPluginsList.delete)

        buttonBox.pack_start(rightButton, False, False, 0)
        buttonBox.pack_start(leftButton, False, False, 0)

        # Up/Down buttons
        enabledBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        enabledBox.set_spacing(10)

        enabledButtonBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        enabledButtonBox.set_spacing(5)
        if Gtk.check_version(3, 0, 0) is None:
            enabledButtonBox.set_halign(Gtk.Align.CENTER)
        else:
            enabledAlignment = Gtk.Alignment(xalign=0.5, xscale=0.0, yscale=0.0)
            enabledAlignment.add(enabledButtonBox)
        self.EnabledButtonBox = enabledButtonBox

        upButton = Gtk.Button.new_with_mnemonic(_("_Up"))
        downButton = Gtk.Button.new_with_mnemonic(_("_Down"))
        upButton.set_image(Gtk.Image.new_from_icon_name("go-up",
                                                        Gtk.IconSize.BUTTON))
        downButton.set_image(Gtk.Image.new_from_icon_name("go-down",
                                                          Gtk.IconSize.BUTTON))
        upButton.connect('clicked', self.EnabledPluginsList.move_up)
        downButton.connect('clicked', self.EnabledPluginsList.move_down)

        # Add buttons
        addButton = Gtk.Button.new_with_mnemonic(_("_Add"))
        addButton.set_image(Gtk.Image.new_from_icon_name("list-add",
                                                         Gtk.IconSize.BUTTON))
        addButton.connect('clicked', self.AddPlugin)

        enabledButtonBox.pack_start(addButton, False, False, 0)
        enabledButtonBox.pack_start(upButton, False, False, 0)
        enabledButtonBox.pack_start(downButton, False, False, 0)

        enabledBox.pack_start(self.EnabledPluginsList, True, True, 0)
        if Gtk.check_version(3, 0, 0) is None:
            enabledBox.pack_start(enabledButtonBox, False, False, 0)
        else:
            enabledBox.pack_start(enabledAlignment, False, False, 0)

        listBox.pack_start(self.DisabledPluginsList, True, True, 0)
        if Gtk.check_version(3, 0, 0) is None:
            listBox.pack_start(buttonBox, True, False, 0)
        else:
            listBox.pack_start(boxAlignment, True, False, 0)
        listBox.pack_start(enabledBox, True, True, 0)

        self.UpdateEnabledPluginsList()
        self.UpdateDisabledPluginsList()

        # Connect Store
        self.EnabledPluginsList.store.connect('row-changed', self.ListChanged)
        self.EnabledPluginsList.store.connect('row-deleted', self.ListChanged)
        self.EnabledPluginsList.store.connect('rows-reordered', self.ListChanged)

        rightChild.pack_start(listBox, True, True, 0)

        # Auto sort
        autoSort.connect('toggled', self.AutoSortChanged)
        autoSort.set_active(self.Context.AutoSort)

        self.Widget = rightChild

    def AutoSortChanged(self, widget):
        if self.Block > 0:
            return

        autoSort = widget.get_active()
        if not autoSort:
            dlg = Gtk.MessageDialog(message_type=Gtk.MessageType.WARNING,
                                    buttons=Gtk.ButtonsType.YES_NO,
                                    transient_for=widget.get_toplevel())
            dlg.set_markup(_("Do you really want to disable automatic plugin sorting? This will also disable conflict handling. You should only do this if you know what you are doing."))
            response = dlg.run()
            dlg.destroy()
            if response == Gtk.ResponseType.NO:
                self.Block += 1
                widget.set_active(True)
                self.Block -= 1
                return

        self.Context.AutoSort = autoSort

        for widget in (self.EnabledPluginsList.view, self.DisabledPluginsList.view,
                self.MiddleButtonBox, self.EnabledButtonBox):
            widget.set_sensitive(not self.Context.AutoSort)

        GlobalUpdater.UpdatePlugins()

    def UpdateEnabledPluginsList(self):
        # Compiz 0.9.x and Compiz 0.8.x compatibility.
        try:
            activePlugins = self.Context.Plugins['core'].Screen['active_plugins'].Value
        except (AttributeError, TypeError):
            activePlugins = self.Context.Plugins['core'].Display['active_plugins'].Value

        self.EnabledPluginsList.clear()

        for name in activePlugins:
            self.EnabledPluginsList.append(name)

    def UpdateDisabledPluginsList(self):
        # Compiz 0.9.x and Compiz 0.8.x compatibility.
        try:
            activePlugins = self.Context.Plugins['core'].Screen['active_plugins'].Value
        except (AttributeError, TypeError):
            activePlugins = self.Context.Plugins['core'].Display['active_plugins'].Value

        self.DisabledPluginsList.clear()

        for plugin in sorted(self.Context.Plugins.values(), key=PluginKeyFunc):
            if not plugin.Name in activePlugins and plugin.Name != "core":
                self.DisabledPluginsList.append(plugin.Name)

    def AddPlugin(self, widget):
        dlg = Gtk.Dialog(title=_("Add plugin"),
                         transient_for=widget.get_toplevel())

        button = dlg.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)
        button.set_image(Gtk.Image.new_from_icon_name("gtk-cancel",
                                                      Gtk.IconSize.BUTTON))
        button = dlg.add_button(_("_OK"), Gtk.ResponseType.OK)
        button.set_image(Gtk.Image.new_from_icon_name("gtk-ok",
                                                      Gtk.IconSize.BUTTON))
        button.grab_default()
        dlg.set_default_response(Gtk.ResponseType.OK)

        label = Gtk.Label(label=_("Plugin name:"))
        label.set_tooltip_text(_("Insert plugin name"))
        dlg.vbox.pack_start(label, True, True, 0)

        entry = Gtk.Entry()
        entry.set_activates_default(True)
        dlg.vbox.pack_start(entry, True, True, 0)

        dlg.vbox.set_spacing(5)

        dlg.vbox.show_all()
        ret = dlg.run()
        dlg.destroy()

        if ret == Gtk.ResponseType.OK:
            self.EnabledPluginsList.append(entry.get_text())

    def EnablePlugins(self, widget):
        selectedRows = self.DisabledPluginsList.select.get_selected_rows()[1]
        for path in selectedRows:
            iter = self.DisabledPluginsList.store.get_iter(path)
            name = self.DisabledPluginsList.store.get(iter, 0)[0]
            self.EnabledPluginsList.append(name)
        self.DisabledPluginsList.delete(widget)

    def ListChanged(self, *args, **kwargs):
        if self.Block > 0:
            return
        self.Block += 1
        plugins = self.EnabledPluginsList.get_list()

        # Compiz 0.9.x and Compiz 0.8.x compatibility.
        try:
            self.Context.Plugins['core'].Screen['active_plugins'].Value = plugins
        except (AttributeError, TypeError):
            self.Context.Plugins['core'].Display['active_plugins'].Value = plugins
        self.Context.Write()
        self.UpdateDisabledPluginsList()
        self.Block -= 1

# Preferences Page
#
class PreferencesPage(GenericPage):
    def __init__(self, context):
        GenericPage.__init__(self)
        self.Context = context
        self.LeftWidget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                  homogeneous=False, spacing=10)
        if Gtk.check_version(3, 0, 0) is None:
            self.LeftWidget.props.margin = 10
        else:
            self.LeftWidget.set_border_width(10)
        if Gtk.check_version(3, 12, 0) is None:
            self.RightWidget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                       spacing=6)
            self.RightWidgetStack = Gtk.Stack()
            RightWidgetStackSwitcher = Gtk.StackSwitcher()
            RightWidgetStackSwitcher.set_stack(self.RightWidgetStack)
            RightWidgetStackSwitcherBox = Gtk.Box()
            RightWidgetStackSwitcherBox.set_center_widget(RightWidgetStackSwitcher)
            self.RightWidget.pack_start(RightWidgetStackSwitcherBox, False, False, 0)
            self.RightWidget.pack_end(self.RightWidgetStack, True, True, 0)
        else:
            self.RightWidget = Gtk.Notebook()

        # Left Pane
        self.DescLabel = Label()
        self.HeaderLabelSet(self.DescLabel, _("Preferences"))
        self.DescImg = Image("profiles",ImageCategory, 64)
        self.LeftWidget.pack_start(self.DescImg, False, False, 0)
        self.LeftWidget.pack_start(self.DescLabel, False, False, 0)
        self.InfoLabelCont = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if Gtk.check_version(3, 0, 0) is None:
            self.InfoLabelCont.props.margin = 10
        else:
            self.InfoLabelCont.set_border_width(10)
        self.LeftWidget.pack_start(self.InfoLabelCont, False, False, 0)
        self.InfoLabel = Label(_("Configure the backend, profile and other internal settings used by the Compiz Configuration System."), 180)
        self.InfoLabelCont.pack_start(self.InfoLabel, True, True, 0)

        # About Button
        aboutLabel = Label()
        self.HeaderLabelSet(aboutLabel, _("About"))
        aboutButton = Gtk.Button()
        aboutButton.set_relief(Gtk.ReliefStyle.NONE)
        aboutImage = Gtk.Image.new_from_icon_name("help-about",
                                                  Gtk.IconSize.BUTTON)
        aboutFrame = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        aboutFrame.set_spacing(5)
        aboutFrame.pack_start(aboutImage, False, False, 0)
        aboutFrame.pack_start(Label(_("About CCSM...")), False, False, 0)
        aboutButton.add(aboutFrame)
        aboutButton.set_tooltip_text(_("About"))
        aboutButton.connect('clicked', self.ShowAboutDialog)
        aboutBin = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if Gtk.check_version(3, 0, 0) is None:
            aboutBin.props.margin = 10
        else:
            aboutBin.set_border_width(10)
        aboutBin.pack_start(aboutButton, False, False, 0)
        self.LeftWidget.pack_start(aboutLabel, False, False, 0)
        self.LeftWidget.pack_start(aboutBin, False, False, 0)

        # Back Button
        backButton = Gtk.Button.new_with_mnemonic(_("_Back"))
        backButton.set_image(Gtk.Image.new_from_icon_name("go-previous",
                                                          Gtk.IconSize.BUTTON))
        backButton.connect('clicked', self.GoBack)
        self.LeftWidget.pack_end(backButton, False, False, 0)

        # Profile & Backend Page
        self.ProfileBackendPage = ProfileBackendPage(context)
        if Gtk.check_version(3, 12, 0) is None:
            self.RightWidgetStack.add_titled(self.ProfileBackendPage.Widget, "ProfileBackend", _("Profile & Backend"))
        else:
            self.RightWidget.append_page(self.ProfileBackendPage.Widget,
                                         Gtk.Label(label=_("Profile & Backend")))

        # Plugin List
        self.PluginListPage = PluginListPage(context)
        if Gtk.check_version(3, 12, 0) is None:
            self.RightWidgetStack.add_titled(self.PluginListPage.Widget, "PluginList", _("Plugin List"))
        else:
            self.RightWidget.append_page(self.PluginListPage.Widget,
                                         Gtk.Label(label=_("Plugin List")))

    def ShowAboutDialog(self, widget):
        about = AboutDialog(widget.get_toplevel())
        about.show_all()
        about.run()
        about.destroy()

# Main Page
#
class MainPage(object):
    def __init__(self, main, context):
        self.Context = context
        self.Main    = main
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                          homogeneous=False, spacing=10)
        if Gtk.check_version(3, 0, 0) is None:
            sidebar.props.margin = 10
        else:
            sidebar.set_border_width(10)

        pluginWindow = PluginWindow(self.Context)
        pluginWindow.connect('show-plugin', self.ShowPlugin)

        # Filter
        filterLabel = Label()
        filterLabel.title = _("Filter")
        self.HeaderLabelSet(filterLabel, _("Filter"))
        filterLabel.props.xalign = 0.1
        filterEntry = ClearEntry()
        filterEntry.set_tooltip_text(_("Filter your Plugin list"))
        filterEntry.connect("changed", self.FilterChanged)
        self.filterEntry = filterEntry

        # Screens
        if len(get_screens()) > 1:
            screenBox = Gtk.ComboBoxText.new()
            for screen in get_screens():
                screenBox.append_text(_("Screen %i") % screen)
            name = self.Context.CurrentBackend.Name
            screenBox.set_active(CurrentScreenNum)
            screenBox.connect("changed", self.ScreenChanged)
            screenLabel = Label()
            screenLabel.props.xalign = 0.1
            self.HeaderLabelSet(screenLabel, _("Screen"))

            sidebar.pack_start(screenLabel, False, False, 0)
            sidebar.pack_start(screenBox, False, False, 0)

        # Categories
        categoryBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        if Gtk.check_version(3, 0, 0) is None:
            categoryBox.props.margin = 5
        else:
            categoryBox.set_border_width(5)
        categories = ['All'] + sorted(pluginWindow.get_categories(), key=CategoryKeyFunc)
        for category in categories:
            # name: untranslated name/interal identifier
            # label: translated name
            name = category or 'Uncategorized'
            label = _(name)
            iconName = name.lower ().replace (" ", "_")
            categoryToggleIcon = Image (name = iconName, type = ImageCategory,
                                        size = 22)
            categoryToggleLabel = Label (label)
            categoryToggleBox = Gtk.Box (orientation=Gtk.Orientation.HORIZONTAL)
            if Gtk.check_version (3, 12, 0) is None:
                categoryToggleIcon.set_margin_end(10)
                categoryToggleBox.pack_start (categoryToggleIcon,
                                              False, False, 0)
            else:
                alignment = Gtk.Alignment (xalign=0.0)
                alignment.set_padding (0, 0, 0, 10)
                alignment.add (categoryToggleIcon)
                categoryToggleBox.pack_start (alignment, False, False, 0)
            categoryToggleBox.pack_start (categoryToggleLabel, True, True, 0)
            categoryToggle = PrettyButton ()
            categoryToggle.add(categoryToggleBox)
            categoryToggle.connect("clicked", self.ToggleCategory, category)
            categoryBox.pack_start(categoryToggle, False, False, 0)
        categoryLabel = Label()
        categoryLabel.props.xalign = 0.1
        self.HeaderLabelSet(categoryLabel, _("Category"))

        # Exit Button
        exitButton = Gtk.Button.new_with_mnemonic(_("_Close"))
        exitButton.set_image(Gtk.Image.new_from_icon_name("window-close",
                                                          Gtk.IconSize.BUTTON))
        exitButton.connect('clicked', self.Main.Quit)

        # Advanced Search
        searchLabel = Label()
        self.HeaderLabelSet(searchLabel, _("Advanced Search"))
        searchImage = Gtk.Image.new_from_icon_name("go-next",
                                                   Gtk.IconSize.BUTTON)
        searchButton = PrettyButton()
        searchButton.connect("clicked", self.ShowAdvancedFilter)
        searchButton.set_relief(Gtk.ReliefStyle.NONE)
        searchFrame = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        searchFrame.pack_start(searchLabel, False, False, 0)
        searchFrame.pack_end(searchImage, False, False, 0)
        searchButton.add(searchFrame)

        # Preferences
        prefLabel = Label()
        self.HeaderLabelSet(prefLabel, _("Preferences"))
        prefImage = Gtk.Image.new_from_icon_name("go-next",
                                                 Gtk.IconSize.BUTTON)
        prefButton = PrettyButton()
        prefButton.connect("clicked", self.ShowPreferences)
        prefButton.set_relief(Gtk.ReliefStyle.NONE)
        prefFrame = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        prefFrame.pack_start(prefLabel, False, False, 0)
        prefFrame.pack_end(prefImage, False, False, 0)
        prefButton.add(prefFrame)

        # Pack widgets into sidebar
        sidebar.pack_start(filterLabel, False, False, 0)
        sidebar.pack_start(filterEntry, False, False, 0)
        sidebar.pack_start(categoryLabel, False, False, 0)
        sidebar.pack_start(categoryBox, False, False, 0)
        sidebar.pack_end(exitButton, False, False, 0)
        sidebar.pack_end(searchButton, False, False, 0)
        sidebar.pack_end(prefButton, False, False, 0)

        self.LeftWidget = sidebar
        self.RightWidget = pluginWindow

    def HeaderLabelSet(self, widget, label):
        self.HeaderStyleUpdated(widget, label)
        if Gtk.check_version(3, 16, 0) is None:
            widget.connect("style-updated", self.HeaderStyleUpdated, label)
        else:
            widget.connect("style-set", self.HeaderStyleSet, label)

    StyleBlock = 0
    def HeaderStyleUpdated(self, widget, label):
        if self.StyleBlock > 0:
            return
        self.StyleBlock += 1
        textRGB = None
        if Gtk.check_version(3, 6, 0) is None:
            style = widget.get_style_context ()
            style.save()
            style.add_class(Gtk.STYLE_CLASS_VIEW)
            bgColor = style.get_background_color(style.get_state())
            style.set_state(Gtk.StateFlags.SELECTED)
            textColor = style.get_background_color(style.get_state())
            if not textColor.equal(bgColor) and textColor.alpha != 0.0:
                textRGB = "#%.4X%.4X%.4X" % (int(textColor.red * 0xFFFF),
                                             int(textColor.green * 0xFFFF),
                                             int(textColor.blue * 0xFFFF))
                widget.set_markup(HeaderMarkup % (textRGB, label))
            else:
                widget.set_markup(HeaderMarkupDefault % label)
            style.restore()
        else:
            textColor = widget.get_style().lookup_color("selected_bg_color")
            if textColor[0] != False:
                textRGB = "#%.4X%.4X%.4X" % (textColor[1].red,
                                             textColor[1].green,
                                             textColor[1].blue)
                widget.set_markup(HeaderMarkup % (textRGB, label))
            else:
                widget.set_markup(HeaderMarkupDefault % label)
        self.StyleBlock -= 1

    if Gtk.check_version(3, 16, 0) is not None:
        def HeaderStyleSet(self, widget, previous, label):
            self.HeaderStyleUpdated(widget, label)

    def ShowPlugin(self, widget, plugin):
        pluginPage = PluginPage(plugin)
        self.Main.SetPage(pluginPage)

    def ShowAdvancedFilter(self, widget):
        filterPage = FilterPage(self.Context)
        self.Main.SetPage(filterPage)

    def ShowPreferences(self, widget):
        preferencesPage = PreferencesPage(self.Context)
        self.Main.SetPage(preferencesPage)

    def ToggleCategory(self, widget, category):
        if category == 'All':
            category = None
        else:
            category = category.lower()
        self.RightWidget.filter_boxes(category, level=FilterCategory)

    def FilterChanged(self, widget):
        text = widget.get_text().lower()
        self.RightWidget.filter_boxes(text)

    def ScreenChanged(self, widget):
        self.Context.Write()
        self.CurrentScreenNum = widget.get_active()
        self.Context.Read()

# Page
#
class Page(object):

    def __init__(self):
        self.SetContainer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.Widget = Gtk.EventBox()
        self.Widget.add(self.SetContainer)

        if Gtk.check_version (3, 0, 0) is None:
            self.Widget.get_style_context ().add_class (Gtk.STYLE_CLASS_NOTEBOOK)

        self.Empty = True

    def Wrap(self):
        scroll = Gtk.ScrolledWindow()
        scroll.props.hscrollbar_policy = Gtk.PolicyType.NEVER
        scroll.props.vscrollbar_policy = Gtk.PolicyType.AUTOMATIC

        view = Gtk.Viewport()
        if Gtk.check_version(3, 0, 0) is None:
            view.props.margin = 5
        else:
            view.set_border_width(5)
        view.set_shadow_type(Gtk.ShadowType.NONE)

        scroll.add(view)
        view.add(self.Widget)

        self.Scroll = scroll

# Group Page
#
class GroupPage(Page):
    def __init__(self, name, group):
        Page.__init__(self)

        self.Name = name
        self.VisibleAreas = self.subGroupAreas = []
        self.Label = Gtk.Label(label="<b>%s</b>" %
                               (protect_pango_markup(name or _("General"))))
        self.Label.set_use_markup(True)
        if Gtk.check_version(3, 0, 0) is None:
            self.Label.set_halign(Gtk.Align.START)
            self.Label.props.margin = 4
        else:
            label = self.Label
            self.Label = Gtk.Alignment(xalign=0.0, xscale=0.0, yscale=0.0)
            self.Label.set_padding(4, 4, 4, 4)
            self.Label.add(label)
        if '' in group:
            sga = SubGroupArea('', group[''][1])
            if not sga.Empty:
                self.SetContainer.pack_start(sga.Widget, False, False, 0)
                self.Empty = False
                self.subGroupAreas.append(sga)

        sortedSubGroups = sorted(group.items(), key=GroupIndexKeyFunc)
        for (subGroupName, (subGroupIndex, subGroup)) in sortedSubGroups:
            if not subGroupName == '':
                sga = SubGroupArea(subGroupName, subGroup)
                if not sga.Empty:
                    self.SetContainer.pack_start(sga.Widget, False, False, 0)
                    self.Empty = False
                    self.subGroupAreas.append(sga)

        self.Visible = not self.Empty

    def Filter(self, text, level=FilterAll):
        empty = True
        self.VisibleAreas = []
        for area in self.subGroupAreas:
            if area.Filter(text, level=level):
                self.VisibleAreas.append(area)
                empty = False

        self.Visible = not empty

        self.Label.set_no_show_all(empty)
        if empty:
            self.Label.hide()
        else:
            self.Label.show()

        return not empty

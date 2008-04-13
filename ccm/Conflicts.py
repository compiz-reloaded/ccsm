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

from ccm.Constants import *

import locale
import gettext
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("ccsm", DataDir + "/locale")
gettext.textdomain("ccsm")
_ = gettext.gettext

class Conflict:
    def __init__(self, autoResolve = True):
        self.AutoResolve = autoResolve

    # buttons = (text, type/icon, response_id)
    def Ask(self, message, buttons, custom_widgets=None):
        if self.AutoResolve:
            return gtk.RESPONSE_YES

        dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_WARNING)

        for text, icon, response in buttons:
            button = gtk.Button(text)
            button.set_image(gtk.image_new_from_stock(icon, gtk.ICON_SIZE_BUTTON))
            dialog.add_action_widget(button, response)

        if custom_widgets != None:
            for widget in custom_widgets:
                dialog.vbox.pack_start(widget, False, False)

        dialog.set_markup(message)
        dialog.show_all()
        answer = dialog.run()
        dialog.destroy()

        return answer

class ActionConflict (Conflict):
    def __init__ (self, setting, settings = [], autoResolve = False):
        Conflict.__init__(self, autoResolve)
        self.Conflicts = []
        self.Name = ""
        self.Setting = setting
        self.Settings = settings

        if len(settings) == 0:
            for plugin in self.Setting.Plugin.Context.Plugins.values ():
                if plugin.Enabled:
                    sets = sum ((z.values () for z in [plugin.Screens[CurrentScreenNum]]+[plugin.Display]), [])
                    settings += sets

    def Resolve (self, updater = None):
        if len (self.Conflicts):
            for setting in self.Conflicts:
                answer = self.AskUser (self.Setting, setting)
                if answer == gtk.RESPONSE_YES:
                    setting.Value = 'Disabled'
                    if updater:
                        updater.UpdateSetting (setting)
                if answer == gtk.RESPONSE_NO:
                    return False

        return True

    def AskUser (self, setting, conflict):
        msg = _("The new value for the %(binding)s binding for the action <b>%(action)s</b> "\
              "in plugin <b>%(plugin)s</b> conflicts with the action <b>%(action_conflict)s</b> of the <b>%(plugin_conflict)s</b> plugin.\n"\
              "Do you wish to disable <b>%(action_conflict)s</b> in the <b>%(plugin_conflict)s</b> plugin?")

        msg_dict = {'binding': self.Name,
                    'action': setting.ShortDesc,
                    'plugin': setting.Plugin.ShortDesc,
                    'action_conflict': conflict.ShortDesc,
                    'plugin_conflict': conflict.Plugin.ShortDesc}

        msg = msg % msg_dict

        yesButton    = (_("Disable %(action_conflict)s") % msg_dict,  gtk.STOCK_YES,  gtk.RESPONSE_YES)
        noButton     = (_("Don't set %(action)s") %  msg_dict,    gtk.STOCK_NO,   gtk.RESPONSE_NO)
        ignoreButton = (_("Set %(action)s anyway") % msg_dict,    gtk.STOCK_STOP, gtk.RESPONSE_REJECT)

        return self.Ask (msg, (ignoreButton, noButton, yesButton))

class KeyConflict(ActionConflict):
    def __init__(self, setting, newValue, settings = [], autoResolve = False, ignoreOld = False):
        ActionConflict.__init__(self, setting, settings, autoResolve)
        self.Name = _("key")

        if not newValue or len(newValue) < 1:
            return

        newValue = newValue.lower ()
        oldValue = self.Setting.Value.lower ()
        badValues = ["disabled", "none"]
        if not ignoreOld:
            badValues.append (oldValue)
        if newValue in badValues:
            return

        for s in self.Settings:
            if s == setting:
                continue
            if s.Type == 'Key':
                if s.Value.lower() == newValue:
                    self.Conflicts.append (s)

class ButtonConflict(ActionConflict):
    def __init__(self, setting, newValue, settings = [], autoResolve = False, ignoreOld = False):
        ActionConflict.__init__(self, setting, settings, autoResolve)
        self.Name = _("button")

        if not newValue or len(newValue) < 1:
            return

        newValue = newValue.lower ()
        oldValue = self.Setting.Value.lower ()
        badValues = ["disabled", "none"]
        if not ignoreOld:
            badValues.append (oldValue)
        if newValue in badValues:
            return

        for s in self.Settings:
            if s == setting:
                continue
            if s.Type == 'Button':
                if s.Value.lower() == newValue:
                    self.Conflicts.append (s)

class EdgeConflict(ActionConflict):
    def __init__(self, setting, newValue, settings = [], autoResolve = False, ignoreOld = False):
        ActionConflict.__init__(self, setting, settings, autoResolve)
        self.Name = _("edge")

        if not newValue or len(newValue) < 1:
            return

        if not ignoreOld:
            newEdges = map (lambda e: e.lower(), newValue.split ("|"))
            oldEdges = map (lambda e: e.lower(), self.Setting.Value.split ("|"))
            diff = filter (lambda e: e not in newEdges, oldEdges)
            diff += filter (lambda e: e not in oldEdges, newEdges)
            if len (diff) < 1:
                return

        for s in settings:
            if s == setting:
                continue
            elif s.Type == 'Edge':
                for edge in newValue.split ("|"):
                    settingEdges = map (lambda e: e.lower(), s.Value.split ("|"))
                    if edge.lower() in settingEdges:
                        self.Conflicts.append ((s, edge))
                        break

    def Resolve (self, updater = None):
        if len (self.Conflicts):
            for setting, edge in self.Conflicts:
                answer = self.AskUser (self.Setting, setting)
                if answer == gtk.RESPONSE_YES:
                    value = setting.Value.split ("|")
                    value.remove (edge)
                    setting.Value = "|".join (value)
                    if updater:
                        updater.UpdateSetting (setting)
                if answer == gtk.RESPONSE_NO:
                    return False

        return True

# Not used for plugin dependencies (which are handled by ccs) but own feature checking e.g. image support
class FeatureRequirement(Conflict):
    def __init__(self, context, feature, autoResolve = False):
        Conflict.__init__(self, autoResolve)
        self.Requirements = []
        self.Context = context
        self.Feature = feature

        self.Found = False
        for plugin in context.Plugins.values():
            if feature in plugin.Features:
                self.Found = True
                if not plugin.Enabled:
                    self.Requirements.append(plugin)
    
    def Resolve(self):
        if len(self.Requirements) == 0 and self.Found:
            return True
        elif not self.Found:
            answer = self.ErrorAskUser()
            if answer == gtk.RESPONSE_YES:
                return True
            else:
                return False
        
        for plugin in self.Requirements:
            answer = self.AskUser(plugin)
            if answer == gtk.RESPONSE_YES:
                plugin.Enabled = True
                self.Context.Write()
                return True

    def ErrorAskUser(self):
        msg = _("You are trying to use the feature <b>%(feature)s</b> which is <b>not</b> provided by any plugin.\n"\
                "Do you wish to use this feature anyway?")

        msg_dict = {'feature': self.Feature}

        msg = msg % msg_dict

        yesButton = (_("Use %(feature)s") % msg_dict,       gtk.STOCK_YES, gtk.RESPONSE_YES)
        noButton  = (_("Don't use %(feature)s") % msg_dict, gtk.STOCK_NO,  gtk.RESPONSE_NO)

        answer = self.Ask(msg, (noButton, yesButton))

        return answer

    def AskUser(self, plugin):
        msg = _("You are trying to use the feature <b>%(feature)s</b> which is provided by <b>%(plugin)s</b>.\n"\
                "This plugin is currently disabled.\n"\
                "Do you wish to enable <b>%(plugin)s</b> so the feature is available?")

        msg_dict = {'feature': self.Feature,
                    'plugin': plugin.ShortDesc}

        msg = msg % msg_dict

        yesButton = (_("Enable %(plugin)s") % msg_dict,       gtk.STOCK_YES, gtk.RESPONSE_YES)
        noButton  = (_("Don't enable %(feature)s") % msg_dict, gtk.STOCK_NO,  gtk.RESPONSE_NO)

        answer = self.Ask(msg, (noButton, yesButton))

        return answer

class PluginConflict(Conflict):
    def __init__(self, plugin, conflicts, autoResolve = False):
        Conflict.__init__(self, autoResolve)
        self.Conflicts = conflicts
        self.Plugin = plugin

    def Resolve(self):
        for conflict in self.Conflicts:
            if conflict[0] == 'ConflictFeature':
                answer = self.AskUser(self.Plugin, conflict)
                if answer == gtk.RESPONSE_YES:
                    disableConflicts = conflict[2][0].DisableConflicts
                    con = PluginConflict(conflict[2][0], disableConflicts)
                    if con.Resolve():
                        conflict[2][0].Enabled = False
                    else:
                        return False
                else:
                    return False

            elif conflict[0] == 'ConflictPlugin':
                answer = self.AskUser(self.Plugin, conflict)
                if answer == gtk.RESPONSE_YEs:
                    disableConflicts = conflict[2][0].DisableConflicts
                    con = PluginConflict(conflict[2][0], disableConflicts)
                    if con.Resolve():
                        conflict[2][0].Enabled = False
                    else:
                        return False
                else:
                    return False
            
            elif conflict[0] == 'RequiresFeature':
                answer, choise = self.AskUser(self.Plugin, conflict)
                if ret == gtk.RESPONSE_YES:
                    for plg in conflict[2]:
                        if plg.ShortDesc == choise:
                            enableConflicts = plg.EnableConflicts
                            con = PluginConflict(plg, enableConflicts)
                            if con.Resolve():
                                plg.Enabled = True
                            else:
                                return False
                            break
                else:
                    return False

            elif conflict[0] == 'RequiresPlugin':
                answer = self.AskUser(self.Plugin, conflict)
                if answer ==  gtk.RESPONSE_YES:
                    enableConflicts = conflict[2][0].EnableConflicts
                    con = PluginConflict(conflict[2][0], enableConflicts)
                    if con.Resolve():
                        conflict[2][0].Enabled = True
                    else:
                        return False
                else:
                    return False

            elif conflict[0] == 'FeatureNeeded':
                answer = self.AskUser(self.Plugin, conflict)
                if answer == gtk.RESPONSE_YES:
                    for plg in conflict[2]:
                        disableConflicts = plg.DisableConflicts
                        con = PluginConflict(plg, disableConflicts)
                        if con.Resolve():
                            plg.Enabled = False
                        else:
                            return False
                else:
                    return False

            elif conflict[0] == 'PluginNeeded':
                answer = self.AskUser(self.Plugin, conflict)
                if answer == gtk.RESPONSE_YES:
                    for plg in conflict[2]:
                        disableConflicts = plg.DisableConflicts
                        con = PluginConflict(plg, disableConflicts)
                        if con.Resolve():
                            plg.Enabled = False
                        else:
                            return False
                else:
                    return False

        # Only when enabling a plugin
        types = []
        actionConflicts = []
        if not self.Plugin.Enabled:
            for setting in sum ((z.values () for z in [self.Plugin.Screens[CurrentScreenNum]]+[self.Plugin.Display]), []):
                conflict = None
                if setting.Type == 'Key':
                    conflict = KeyConflict(setting, setting.Value, ignoreOld = True)
                elif setting.Type == 'Button':
                    conflict = ButtonConflict(setting, setting.Value, ignoreOld = True)
                elif setting.Type == 'Edge':
                    conflict = KeyConflict(setting, setting.Value, ignoreOld = True)

                # Conflicts were found
                if conflict and conflict.Conflicts:
                    name = conflict.Name
                    if name not in tpes:
                        types.append(name)
                    actionConflicts.append(conflict)

        if len(actionConflicts):
            answer = self.AskUser(self.Plugin, ('ConflictAction', types))
            if answer == gtk.RESPONSE_YES:
                for conflict in actionConflicts:
                    conflict.Resolve()

        return True

    def AskUser(self, plugin, conflict):
        msg = ""
        okMsg = ""
        cancelMsg = ""
        widgets = []

        # CCSM custom conflict
        if conflict[0] == 'ConflictAction':
            msg = _("Some %(bindings)s bindings of Plugin <b>%(plugin)s</b> conflict with"\
                "other plugins. Do you want to resolve this conflicts?")

            types = conflict[1]
            bindings = ", ".join(types[:-1])
            if len(types) > 1:
                bindings = "%s and %s" % (bindings, types[-1])

            msg_dict = {'plugin': plugin.ShortDesc,
                        'bindings': bindings}

            msg = msg % msg_dict

            okMsg     = _("Resolve conflicts") % msg_dict
            cancelMsg = _("Ignore conflicts") % msg_dict

        elif conflict[0] == 'ConflictFeature':
            msg = _("Plugin <b>%(plugin_conflict)s</b> provides feature <b>%(feature)s</b> which is also "\
                "provided by <b>%(plugin)s</b>")
            
            msg_dict = {'plugin_conflict': conflict[2][0].ShortDesc,
                        'feature': conflict[1],
                        'plugin': plugin.ShortDesc}

            msg = msg % msg_dict

            okMsg     = _("Disable %(plugin_conflict)s") % msg_dict
            cancelMsg = _("Don't enable %(plugin)s") % msg_dict
        
        elif conflict[0] == 'ConflictPlugin':
            msg = _("Plugin <b>%(plugin_conflict)s</b> conflicts with <b>%(plugin)s</b>.")
            msg = msg % msg_dict

            okMsg = _("Disable %(plugin_conflict)s") % msg_dict
            cancelMsg = _("Don't enable %(plugin)s") % msg_dict
        
        elif conflict[0] == 'RequiresFeature':
            pluginList = ', '.join("\"%s\"" % plugin.ShortDesc for plugin in conflict[2])
            msg = _("<b>%(plugin)s</b> requires feature <b>%(feature)s</b> which is provided by the following plugins:\n%(plugin_list)s")
            
            msg_dict = {'plugin': plugin.ShortDesc,
                        'feature': conflict[1],
                        'plugin_list': pluginList}

            msg = msg % msg_dict

            cmb = gtk.combo_box_new_text()
            for plugin in conflict[2]:
                cmb.append_text(plugin.ShortDesc)
            cmb.set_active(0)
            widgets.append(cmb)

            okMsg = _("Enable these plugins")
            cancelMsg_("Don't enable %(plugin)s") % msg_dict
        
        elif conflict[0] == 'RequiresPlugin':
            msg = _("<b>%(plugin)s</b> requires the plugin <b>%(require)s</b>.")

            msg_dict = {'plugin': plugin.ShortDesc,
                        'require': conflict[2][0].ShortDesc}

            msg = msg % msg_dict

            okMsg = _("Enable %(require)s") % msg_dict
            cancelMsg = _("Don't enable %(plugin)s") % msg_dict
        
        elif conflict[0] == 'FeatureNeeded':
            pluginList = ', '.join("\"%s\"" % plugin.ShortDesc for plugin in conflict[2])
            msg = _("<b>%(plugin)s</b> provides the feature <b>%(feature)s</b> which is required by the plugins <b>%(plugin_list)s</b>.")
            
            msg_dict = {'plugin': plugin.ShortDesc,
                        'feature': conflict[1],
                        'plugin_list': pluginList}
            
            msg = msg % msg_dict

            okMsg = _("Disable these plugins")
            cancelMsg = _("Don't disable %(plugin)s") % msg_dict
        
        elif conflict[0] == 'PluginNeeded':
            pluginList = ', '.join("\"%s\"" % plugin.ShortDesc for plugin in conflict[2])
            msg = _("<b>%(plugin)s</b> is required by the plugins <b>%(plugin_list)s</b>.")
            
            msg_dict = {'plugin': plugin.ShortDesc,
                        'plugin_list': pluginList}
            
            msg = msg % msg_dict

            okMsg = _("Disable these plugins")
            cancelMsg = _("Don't disable %(plugin)s") % msg_dict

        okButton     = (okMsg,     gtk.STOCK_OK,     gtk.RESPONSE_YES)
        cancelButton = (cancelMsg, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        
        answer = self.Ask(msg, (cancelButton, okButton), widgets)
        if conflict[0] == 'RequiresFeature':
            choise = widgets[0].get_active_text() 
            return answer, choise
        
        return answer
        

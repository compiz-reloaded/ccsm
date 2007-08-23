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

from ccm.Constants import *

import locale
import gettext
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("ccsm", DataDir + "/locale")
gettext.textdomain("ccsm")
_ = gettext.gettext

class Conflict:
    def __init__(self):
        pass

    # buttons = (text, type/icon, response_id)
    def Ask(self, message, buttons, custom_widgets=None):
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
    def __init__ (self, setting, key = None, button = None, edges = None):
        self.KeyConflicts = []
        self.ButtonConflicts = []
        self.EdgeConflicts = []
        self.Setting = setting

        lvalue = self.Setting.Value.lower ()
        checkKey = key and len (key)
        if checkKey:
            checkKey = key.lower () not in ("disabled", "none", lvalue)
        checkButton = button and len (button)
        if checkButton:
            checkButton = button.lower () not in ("disabled", "none", lvalue)
        checkEdges = edges and len (edges)
        if checkEdges:
            newEdges = edges.split ("|")
            oldEdges = self.Setting.Value.split ("|")
            diff = filter (lambda e: e not in newEdges, oldEdges)
            diff += filter (lambda e: e not in oldEdges, newEdges)
            checkEdges = len (diff) > 0 

        if not checkKey and not checkButton and not checkEdges:
            return

        # this might be a bit slow but anyway...
        for plugin in setting.Plugin.Context.Plugins.values ():
            if plugin.Enabled:
                settings = sum ((z.values () for z in [plugin.Screens[CurrentScreenNum]]+[plugin.Display]), [])
                for s in settings:
                    if s == setting:
                        continue
                    if s.Type == 'Key' and checkKey:
                        if s.Value == key:
                            self.KeyConflicts.append (s)
                    elif s.Type == 'Button' and checkButton:
                        if s.Value == button:
                            self.ButtonConflicts.append (s)
                    elif s.Type == 'Edge' and checkEdges:
                        for edge in edges.split ("|"):
                            if edge in s.Value.split ("|"):
                                self.EdgeConflicts.append ((s, edge))
                                break

    def Resolve (self, updater):
        if len (self.KeyConflicts):
            for k in self.KeyConflicts:
                answer = self.AskUser (self.Setting, k, 'Key')
                if answer == gtk.RESPONSE_YES:
                    k.Value = 'Disabled'
                    updater.UpdateSetting (k)
                if answer == gtk.RESPONSE_NO:
                    return False
        
        if len (self.ButtonConflicts):
            for b in self.ButtonConflicts:
                answer = self.AskUser (self.Setting, b, 'Button')
                if answer == gtk.RESPONSE_YES:
                    b.Value = 'Disabled'
                    updater.UpdateSetting (b)
                if answer == gtk.RESPONSE_NO:
                    return False

        if len (self.EdgeConflicts):
            for e, edge in self.EdgeConflicts:
                answer = self.AskUser (self.Setting, e, 'Edge')
                if answer == gtk.RESPONSE_YES:
                    value = e.Value.split ("|")
                    value.remove (edge)
                    e.Value = "|".join (value)
                    updater.UpdateSetting (e)
                if answer == gtk.RESPONSE_NO:
                    return False

        return True

    def AskUser (self, setting, con, typ):
        msg = _("The new value for the %s binding for the action <b>%s</b> "\
              "in plugin <b>%s</b> conflicts with the action <b>%s</b> of the <b>%s</b> plugin.\n"\
              "Do you wish to disable <b>%s</b> in the <b>%s</b> plugin?")
         
        msg = msg % (typ, setting.ShortDesc, setting.Plugin.ShortDesc, con.ShortDesc, con.Plugin.ShortDesc, con.ShortDesc, con.Plugin.ShortDesc)

        yesButton    = (_("Disable %s") % con.ShortDesc,        gtk.STOCK_YES,  gtk.RESPONSE_YES)
        noButton     = (_("Don't set %s") % setting.ShortDesc,  gtk.STOCK_NO,   gtk.RESPONSE_NO)
        ignoreButton = (_("Set %s anyway") % setting.ShortDesc, gtk.STOCK_STOP, gtk.RESPONSE_REJECT)

        return self.Ask (msg, (yesButton, noButton, ignoreButton))

# Not used for plugin dependencies (which are handled by ccs) but own feature checking e.g. image support
class FeatureRequirement(Conflict):
    def __init__(self, context, feature):
        self.Requirements = []
        self.Context = context
        self.Feature = feature

        for plugin in context.Plugins.values():
            if plugin.Features.__contains__(feature):
                if not plugin.Enabled:
                    self.Requirements.append(plugin)
    
    def Resolve(self):
        if len(self.Requirements) == 0:
            return True
        
        for plugin in self.Requirements:
            answer = self.AskUser(plugin)
            if answer == gtk.RESPONSE_YES:
                plugin.Enabled = True
                self.Context.Write()
                return True

    def AskUser(self, plugin):
        msg = _("You are trying to use the feature <b>%s</b> which is provided by <b>%s</b>.\n"\
                "This plugin is currently disabled.\n"\
                "Do you wish to enable <b>%s</b> so the feature is available?")

        msg = msg % (self.Feature, plugin.ShortDesc, plugin.ShortDesc)

        yesButton = (_("Enable %s") % plugin.ShortDesc,       gtk.STOCK_YES, gtk.RESPONSE_YES)
        noButton  = (_("Don't enable %s") % plugin.ShortDesc, gtk.STOCK_NO,  gtk.RESPONSE_NO)

        answer = self.Ask(msg, (yesButton, noButton))
    
        return answer

class PluginConflict(Conflict):
    def __init__(self, plugin, conflicts):
        self.Conflicts = conflicts
        self.Plugin = plugin

    def Resolve(self):
        for conflict in self.Conflicts:
            if conflict[0] == 'ConflictFeature':
                answer = self.AskUser(self.Plugin, conflict)
                if answer == gtk.RESPONSE_OK:
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
                if answer == gtk.RESPONSE_OK:
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
                if ret == gtk.RESPONSE_OK:
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
                if answer ==  gtk.RESPONSE_OK:            
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
                if answer == gtk.RESPONSE_OK:
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
                if answer == gtk.RESPONSE_OK:
                    for plg in conflict[2]:
                        disableConflicts = plg.DisableConflicts
                        con = PluginConflict(plg, disableConflicts)
                        if con.Resolve():
                            plg.Enabled = False
                        else:
                            return False
                else:
                    return False

        return True

    def AskUser(self, plugin, conflict):
        msg = ""
        okMsg = ""
        cancelMsg = ""
        widgets = []
        if conflict[0] == 'ConflictFeature':
            msg = _("Plugin <b>%s</b> provides feature <b>%s</b> which is also "\
                "provided by <b>%s</b>")
            msg = msg % (conflict[2][0].ShortDesc, conflict[1], plugin.ShortDesc)

            okMsg     = _("Disable %s") % conflict[2][0].ShortDesc
            cancelMsg = _("Don't enable %s") % plugin.ShortDesc
        
        elif conflict[0] == 'ConflictPlugin':
            msg = _("Plugin <b>%s</b> conflicts with <b>%s</b>.")
            msg = msg % (conflict[2][0].ShortDesc, plugin.ShortDesc)

            okMsg = _("Disable %s") % conflict[2][0].ShortDesc
            cancelMsg = _("Don't enable %s") % plugin.ShortDesc
        
        elif conflict[0] == 'RequiresFeature':
            pluginList = ', '.join("\"%s\"" % plugin.ShortDesc for plugin in conflict[2])
            msg = _("<b>%s</b> requires feature <b>%s</b> which is provided by the following plugins:\n%s")
            msg = msg % (plugin.ShortDesc, conflict[1], pluginList)

            cmb = gtk.combo_box_new_text()
            for plugin in conflict[2]:
                cmb.append_text(plugin.ShortDesc)
            cmb.set_active(0)
            widgets.append(cmb)

            okMsg = _("Enable these plugins")
            cancelMsg_("Don't enable %s") % plugin.ShortDesc
        
        elif conflict[0] == 'RequiresPlugin':
            msg = _("<b>%s</b> requires the plugin <b>%s</b>.")
            msg = msg % (plugin.ShortDesc, conflict[2][0].ShortDesc)

            okMsg = _("Enable %s") % conflict[2][0].ShortDesc
            cancelMsg = _("Don't enable %s") % plugin.ShortDesc
        
        elif conflict[0] == 'FeatureNeeded':
            pluginList = ', '.join("\"%s\"" % plugin.ShortDesc for plugin in conflict[2])
            msg = _("<b>%s</b> provides the feature <b>%s</b> which is required by the plugins <b>%s</b>.")
            msg = msg % (plugin.ShortDesc, conflict[1], pluginList) 

            okMsg = _("Disable these plugins")
            cancelMsg = _("Don't disable %s") % plugin.ShortDesc
        
        elif conflict[0] == 'PluginNeeded':
            pluginList = ', '.join("\"%s\"" % plugin.ShortDesc for plugin in conflict[2])
            msg = _("<b>%s</b> is required by the plugins <b>%s</b>.")
            msg = msg % (plugin.ShortDesc, pluginList)

            okMsg = _("Disable these plugins")
            cancelMsg = _("Don't disable %s") % plugin.ShortDesc

        okButton     = (okMsg,     gtk.STOCK_OK,     gtk.RESPONSE_OK)
        cancelButton = (cancelMsg, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        
        answer = self.Ask(msg, (okButton, cancelButton), widgets)
        if conflict[0] == 'RequiresFeature':
            choise = widgets[0].get_active_text() 
            return answer, choise
        
        return answer
        

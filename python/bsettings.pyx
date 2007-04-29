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
# Copyright (C) 2007 Quinn Storm

ctypedef unsigned int Bool

cdef enum BSSettingType:
	TypeBool
	TypeInt
	TypeFloat
	TypeString
	TypeAction
	TypeColor
	TypeMatch
	TypeList
	TypeNum

cdef enum BSPluginConflictType:
	#activate
	ConflictRequiresPlugin
	ConflictRequiresFeature
	ConflictSameFeature
	#deactivate
	ConflictFeatureNeeded
	ConflictPluginNeeded
	#once more back to activate
	#this last one is if the
	#plugin requires a plugin
	#that does not exist
	ConflictPluginError

SettingTypeString=[
		'Bool',
		'Int',
		'Float',
		'String',
		'Action',
		'Color',
		'Match',
		'List',
		'Invalid']

ConflictTypeString=[
		'RequiresPlugin', #A
		'RequiresFeature', #A
		'SameFeature', #A
		'FeatureNeeded', #D
		'PluginNeeded', #D
		'PluginError'] #A

cdef struct BSList:
	void * data
	BSList * next
ctypedef BSList BSSettingList
ctypedef BSList BSPluginList
ctypedef BSList BSStringList
ctypedef BSList BSGroupList
ctypedef BSList BSSubGroupList
ctypedef BSList BSPluginConflictList
ctypedef BSList BSSettingValueList

cdef extern struct BSBackend

cdef struct BSSettingActionValue:
	int button
	unsigned int buttonModMask
	int keysym
	unsigned int keyModMask
	Bool onBell
	int edgeMask
	int edgeButton

cdef struct BSSettingColorValueColor:
	unsigned short red
	unsigned short green
	unsigned short blue
	unsigned short alpha

cdef union BSSettingColorValue:
	BSSettingColorValueColor color
	unsigned short array[4]

cdef union BSSettingValueUnion:
	Bool asBool
	int asInt
	float asFloat
	char * asString
	char * asMatch
	BSSettingActionValue asAction
	BSSettingColorValue asColor
	BSSettingValueList * asList

cdef struct BSSettingIntInfo:
	int min
	int max

cdef struct BSSettingFloatInfo:
	float min
	float max
	float precision

cdef struct BSSettingStringInfo:
	BSStringList * allowedValues

cdef struct BSSettingActionInfo:
	Bool key
	Bool button
	Bool bell
	Bool edge

cdef struct BSSettingActionArrayInfo:
	Bool array[4]

cdef struct BSSettingListInfo:
	BSSettingType listType
	void * listInfo				#actually BSSettingInfo *, works around pyrex

cdef union BSSettingInfo:
	BSSettingIntInfo forInt
	BSSettingFloatInfo forFloat
	BSSettingStringInfo forString
	BSSettingActionInfo forAction
	BSSettingActionArrayInfo forActionAsArray
	BSSettingListInfo forList

cdef struct BSSettingValue:
	BSSettingValueUnion value
	void * parent
	Bool isListChild

cdef struct BSGroup:
	char * name
	BSSubGroupList * subGroups

cdef struct BSSubGroup:
	char * name
	BSSettingList * settings

cdef struct BSPluginCategory:
	char * name
	char * shortDesc
	char * longDesc
	BSStringList * plugins

cdef struct BSContext:
	BSPluginList * plugins
	BSPluginCategory * categories
	void * priv
	BSBackend * backend
	char * profile
	Bool deIntegration
	BSSettingList * changedSettings
	Bool pluginsChanged

cdef struct BSPlugin

cdef struct BSSetting:
	char * name
	char * shortDesc
	char * longDesc
	BSSettingType type
	Bool isScreen
	unsigned int screenNum
	BSSettingInfo info
	char * group
	char * subGroup
	char * hints
	BSSettingValue defaultValue
	BSSettingValue * value
	Bool isDefault
	BSPlugin * parent
	void * priv

cdef struct BSPlugin:
	char * name
	char * shortDesc
	char * longDesc
	char * hints
	char * category
	char * filename
	BSStringList * loadAfter
	BSStringList * loadBefore
	BSStringList * requiresPlugin
	BSStringList * providesFeature
	BSStringList * requiresFeature
	BSSettingList * settings
	BSGroupList * groups
	void * priv
	BSContext * context

cdef struct BSPluginConflict:
	char * value
	BSPluginConflictType type
	BSPluginList * plugins


cdef extern BSContext * bsContextNew()
cdef extern void bsContextDestroy(BSContext * context)

cdef extern BSPlugin * bsFindPlugin(BSContext * context, char * name)
cdef extern BSSetting * bsFindSetting(BSPlugin * plugin, char * name, Bool isScreen, int screenNum)

#cdef extern char * bsColorToString(BSSettingColorValue * color)
cdef extern char * bsEdgeToString(BSSettingActionValue * action)
cdef extern char * bsKeyBindingToString(BSSettingActionValue * action)
cdef extern char * bsButtonBindingToString(BSSettingActionValue * action)

#cdef extern Bool bsSetInt(BSSetting * setting, int data)
#cdef extern Bool bsSetFloat(BSSetting * setting, float data)
#cdef extern Bool bsSetBool(BSSetting * setting, Bool data)
#cdef extern Bool bsSetString(BSSetting * setting, char * data)
#cdef extern Bool bsSetColor(BSSetting * setting, BSSettingColorValue data)
#cdef extern Bool bsSetMatch(BSSetting * setting, char * data)
cdef extern from 'string.h':
	ctypedef int size_t
	cdef extern char * strdup(char * s)
	cdef extern void memset(void * s, int c, size_t n)
	cdef extern void free(void * f)
	cdef extern void * malloc(size_t s)


#cdef extern Bool bsStringToColor(char * value, BSSettingColorValue * target)
cdef extern Bool bsStringToKeyBinding(char * value, BSSettingActionValue * target)
cdef extern Bool bsStringToButtonBinding(char * value, BSSettingActionValue * target)
cdef extern Bool bsStringToEdge(char * value, BSSettingActionValue * target)
cdef extern Bool bsSetValue(BSSetting * setting, BSSettingValue * value)
cdef extern void bsFreeSettingValue(BSSettingValue * value)
cdef extern BSSettingValueList * bsSettingValueListAppend(BSSettingValueList * l, BSSettingValue * v)

cdef extern void bsReadSettings(BSContext * c)
cdef extern void bsWriteSettings(BSContext * c)
cdef extern void bsWriteChangedSettings(BSContext * c)
cdef extern void bsResetToDefault(BSSetting * s)

cdef extern void bsPluginConflictListFree(BSPluginConflictList * l, Bool FreOBJ)
cdef extern BSPluginConflictList * bsCanEnablePlugin(BSContext * c, BSPlugin * p)
cdef extern BSPluginConflictList * bsCanDisablePlugin(BSContext * c, BSPlugin * p)

cdef class Context
cdef class Plugin

cdef object UnpackStringList(BSList * list):
	ret=[]
	while list != NULL:
		ret.append(<char *>list.data)
		list=list.next
	return ret

cdef BSSettingType GetType(BSSettingValue * value):
	if (value.isListChild):
		return (<BSSetting *>value.parent).info.forList.listType
	else:
		return (<BSSetting *>value.parent).type

cdef BSSettingValue * EncodeValue(object data, BSSetting * setting, Bool isListChild):
	cdef BSSettingValue * bv
	cdef BSSettingType t
	cdef BSList * l
	bv = <BSSettingValue *>malloc(sizeof(BSSettingValue))
	memset(bv,0,sizeof(BSSettingValue))
	bv.isListChild = isListChild
	bv.parent = setting
	if isListChild:
		t = setting.info.forList.listType
	else:
		t = setting.type
	if t == TypeString:
		bv.value.asString = strdup(data)
	elif t == TypeMatch:
		bv.value.asMatch = strdup(data)
	elif t == TypeInt:
		bv.value.asInt = data
	elif t == TypeFloat:
		bv.value.asFloat = data
	elif t == TypeBool:
		if data:
			bv.value.asBool = 1
		else:
			bv.value.asBool = 0
	elif t == TypeColor:
		bv.value.asColor.color.red = data[0]
		bv.value.asColor.color.green = data[1]
		bv.value.asColor.color.blue = data[2]
		bv.value.asColor.color.alpha = data[3]
	elif t == TypeAction:
		bsStringToKeyBinding(data[0],&bv.value.asAction)
		bsStringToButtonBinding(data[1],&bv.value.asAction)
		if (data[2]):
			bv.value.asAction.onBell = 1
		else:
			bv.value.asAction.onBell = 0
		bsStringToEdge(data[3],&bv.value.asAction)
	elif t == TypeList:
		l = NULL
		for item in data:
			l=bsSettingValueListAppend(l,
					EncodeValue(item,setting,1))
		bv.value.asList=l
	return bv

cdef object DecodeValue(BSSettingValue * value):
	cdef BSSettingType t
	cdef char * s
	cdef BSList * l
	cdef object cs
	cdef object ks
	cdef object bs
	cdef object es
	t = GetType(value)
	if t == TypeString:
		return value.value.asString
	if t == TypeMatch:
		return value.value.asMatch
	if t == TypeBool:
		if value.value.asBool:
			return True
		return False
	if t == TypeInt:
		return value.value.asInt
	if t == TypeFloat:
		return value.value.asFloat
	if t == TypeColor:
		return [value.value.asColor.color.red,
				value.value.asColor.color.green,
				value.value.asColor.color.blue,
				value.value.asColor.color.alpha]
	if t == TypeAction:
		s=bsKeyBindingToString(&value.value.asAction)
		if s != NULL:
			ks=s
			free(s)
		else:
			ks='None'
		s=bsButtonBindingToString(&value.value.asAction)
		if s != NULL:
			bs=s
			free(s)
		else:
			bs='None'
		if bs == 'Button0':
			bs = 'None'
		s=bsEdgeToString(&value.value.asAction)
		if s != NULL:
			es=s
			free(s)
		else:
			es='None'
		bb=False
		if value.value.asAction.onBell:
			bb=True
		return [ks,bs,bb,es]
	if t == TypeList:
		lret=[]
		l = value.value.asList
		while l != NULL:
			lret.append(DecodeValue(<BSSettingValue *>l.data))
			l=l.next
		return lret
	return 'Unhandled'

cdef class Setting:
	cdef BSSetting * bsSetting
	cdef object info
	cdef Plugin plugin

	def __new__(self, Plugin plugin, name, isScreen, screenNum=0):
		cdef BSSettingType t
		cdef BSSettingInfo * i
		self.bsSetting = bsFindSetting(plugin.bsPlugin, 
				name, isScreen, screenNum)
		self.plugin = plugin
		info=()
		t=self.bsSetting.type
		i=&self.bsSetting.info
		if t==TypeList:
			t=self.bsSetting.info.forList.listType
			i=<BSSettingInfo *>self.bsSetting.info.forList.listInfo
		if t == TypeInt:
			info=(i.forInt.min,i.forInt.max)
		elif t == TypeFloat:
			info=(i.forFloat.min,i.forFloat.max,
					i.forFloat.precision)
		elif t == TypeString:
			info=UnpackStringList(i.forString.allowedValues)
		elif t == TypeAction:
			info=(i.forAction.key,i.forAction.button,
					i.forAction.bell,i.forAction.edge)
		if self.bsSetting.type == TypeList:
			info=(SettingTypeString[t],info)
		self.info=info
	
	def Reset(self):
		bsResetToDefault(self.bsSetting)

	property Plugin:
		def __get__(self):
			return self.plugin
	property Name:
		def __get__(self):
			return self.bsSetting.name
	property ShortDesc:
		def __get__(self):
			return self.bsSetting.shortDesc
	property LongDesc:
		def __get__(self):
			return self.bsSetting.longDesc
	property Group:
		def __get__(self):
			return self.bsSetting.group
	property SubGroup:
		def __get__(self):
			return self.bsSetting.subGroup
	property Type:
		def __get__(self):
			return SettingTypeString[self.bsSetting.type]
	property Info:
		def __get__(self):
			return self.info
	property Hints:
		def __get__(self):
			if self.bsSetting.hints == '':
				return []
			else:
				return str(self.bsSetting.hints).split(';')[:-1]
	property IsDefault:
		def __get__(self):
			if self.bsSetting.isDefault:
				return True
			return False
	property DefaultValue:
		def __get__(self):
			return DecodeValue(&self.bsSetting.defaultValue)
	property Value:
		def __get__(self):
			return DecodeValue(self.bsSetting.value)
		def __set__(self, value):
			cdef BSSettingValue * sv
			sv = EncodeValue(value,self.bsSetting,0)
			bsSetValue(self.bsSetting,sv)
			bsFreeSettingValue(sv)
	property Integrated:
		def __get__(self):
			return False
		def __set__(self,val):
			pass
	property ReadOnly:
		def __get__(self):
			return False
		def __set__(self,val):
			pass


cdef class SSGroup:
	cdef object display
	cdef object screens
	def __new__(self,disp,scrn):
		self.display=disp
		self.screens=scrn
	property Display:
		def __get__(self):
			return self.display
		def __set__(self,value):
			self.display=value
	property Screens:
		def __get__(self):
			return self.screens
		def __set__(self,value):
			self.screens=value

cdef class Plugin:
	cdef BSPlugin * bsPlugin
	cdef Context context
	cdef object screens
	cdef object display
	cdef object groups
	
	def __new__(self, Context context, name):
		cdef BSList * setlist
		cdef BSList * glist
		cdef BSList * sglist
		cdef BSSetting * sett
		cdef BSGroup * gr
		cdef BSSubGroup * sgr
		self.bsPlugin = bsFindPlugin(context.bsContext,name)
		self.context = context
		self.screens = []
		self.display = {}
		self.groups = {}
		for n in range(0,context.NScreens):
			self.screens.append({})
		glist = self.bsPlugin.groups
		while glist != NULL:
			gr=<BSGroup *>glist.data
			self.groups[gr.name]={}
			sglist=gr.subGroups
			while sglist != NULL:
				sgr=<BSSubGroup *>sglist.data
				scr=[]
				for n in range(0,context.NScreens):
					scr.append({})
				self.groups[gr.name][sgr.name]=SSGroup({},scr)
				sglist=sglist.next
			glist=glist.next
		setlist = self.bsPlugin.settings
		while setlist != NULL:
			sett=<BSSetting *>setlist.data
			if sett.isScreen:
				self.screens[sett.screenNum][sett.name] = Setting(self,
						sett.name, True, sett.screenNum)
				self.groups[sett.group][sett.subGroup].Screens[sett.screenNum][
						sett.name]= self.screens[sett.screenNum][sett.name]
			else:
				self.display[sett.name] = Setting(self,
						sett.name, False)
				self.groups[sett.group][sett.subGroup].Display[
						sett.name]= self.display[sett.name]
			setlist=setlist.next

	property Context:
		def __get__(self):
			return self.context
	property Groups:
		def __get__(self):
			return self.groups
	property Display:
		def __get__(self):
			return self.display
	property Screens:
		def __get__(self):
			return self.screens
	property Name:
		def __get__(self):
			return self.bsPlugin.name
	property ShortDesc:
		def __get__(self):
			return self.bsPlugin.shortDesc
	property LongDesc:
		def __get__(self):
			return self.bsPlugin.longDesc
	property Category:
		def __get__(self):
			return self.bsPlugin.category
	property Enabled:
		def __get__(self):
			return self.Display['____plugin_enabled'].Value
		def __set__(self,val):
			if val:
				if len(self.EnableConflicts):
					return
				self.Display['____plugin_enabled'].Value = True
			else:
				if len(self.DisableConflicts):
					return
				self.Display['____plugin_enabled'].Value = False
	property EnableConflicts:
		def __get__(self):
			cdef BSPluginConflictList * pl, * pls
			cdef BSPluginConflict * pc
			cdef BSPluginList * ppl
			cdef BSPlugin * plg
			if self.Enabled:
				return []
			ret = []
			pl = bsCanEnablePlugin(self.context.bsContext,
					self.bsPlugin)
			pls = pl
			while pls != NULL:
				pc = <BSPluginConflict *>pls.data
				rpl = []
				ppl = pc.plugins
				while ppl != NULL:
					plg = <BSPlugin *>ppl.data
					rpl.append(self.context.Plugins[plg.name])
					ppl = ppl.next
				ret.append((ConflictTypeString[pc.type],pc.value,rpl))
				pls = pls.next
			if pl != NULL:
				bsPluginConflictListFree(pl, True)
			return ret
	property DisableConflicts:
		def __get__(self):
			cdef BSPluginConflictList * pl, * pls
			cdef BSPluginConflict * pc
			cdef BSPluginList * ppl
			cdef BSPlugin * plg
			if not self.Enabled:
				return []
			ret = []
			pl = bsCanDisablePlugin(self.context.bsContext,
					self.bsPlugin)
			pls = pl
			while pls != NULL:
				pc = <BSPluginConflict *>pls.data
				rpl = []
				ppl = pc.plugins
				while ppl != NULL:
					plg = <BSPlugin *>ppl.data
					rpl.append(self.context.Plugins[plg.name])
					ppl = ppl.next
				ret.append((ConflictTypeString[pc.type],pc.value,rpl))
				pls = pls.next
			if pl != NULL:
				bsPluginConflictListFree(pl, True)
			return ret

cdef class Context:
	cdef BSContext * bsContext
	cdef object plugins
	cdef object categories
	cdef int nScreens

	def __new__(self,nScreens=1):
		cdef BSPlugin * pl
		cdef BSList * pll
		self.nScreens=nScreens
		self.plugins={}
		self.bsContext=bsContextNew()
		bsReadSettings(self.bsContext)
		pll=self.bsContext.plugins
		self.categories={}
		while pll != NULL:
			pl = <BSPlugin *>pll.data
			self.plugins[pl.name]=Plugin(self,pl.name)
			if pl.category == NULL:
				cat=''
			else:
				cat=pl.category
			if (not self.categories.has_key(cat)):
				self.categories[cat]=[]
			self.categories[cat].append(self.plugins[pl.name])
			pll=pll.next

	def __dealloc__(self):
		bsContextDestroy(self.bsContext)

	def Write(self,onlyChanged=True):
		if onlyChanged:
			bsWriteChangedSettings(self.bsContext)
		else:
			bsWriteSettings(self.bsContext)

	def Read(self):
		bsReadSettings(self.bsContext)

	property Plugins:
		def __get__(self):
			return self.plugins
	property Categories:
		def __get__(self):
			return self.categories
	property NScreens:
		def __get__(self):
			return self.nScreens

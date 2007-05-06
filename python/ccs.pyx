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

cdef enum CCSSettingType:
	TypeBool
	TypeInt
	TypeFloat
	TypeString
	TypeAction
	TypeColor
	TypeMatch
	TypeList
	TypeNum

cdef enum CCSPluginConflictType:
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

cdef struct CCSList:
	void * data
	CCSList * next
ctypedef CCSList CCSSettingList
ctypedef CCSList CCSPluginList
ctypedef CCSList CCSStringList
ctypedef CCSList CCSGroupList
ctypedef CCSList CCSSubGroupList
ctypedef CCSList CCSPluginConflictList
ctypedef CCSList CCSSettingValueList

cdef extern struct CCSBackend

cdef struct CCSSettingActionValue:
	int button
	unsigned int buttonModMask
	int keysym
	unsigned int keyModMask
	Bool onBell
	int edgeMask
	int edgeButton

cdef struct CCSSettingColorValueColor:
	unsigned short red
	unsigned short green
	unsigned short blue
	unsigned short alpha

cdef union CCSSettingColorValue:
	CCSSettingColorValueColor color
	unsigned short array[4]

cdef union CCSSettingValueUnion:
	Bool asBool
	int asInt
	float asFloat
	char * asString
	char * asMatch
	CCSSettingActionValue asAction
	CCSSettingColorValue asColor
	CCSSettingValueList * asList

cdef struct CCSSettingIntInfo:
	int min
	int max

cdef struct CCSSettingFloatInfo:
	float min
	float max
	float precision

cdef struct CCSSettingStringInfo:
	CCSStringList * allowedValues

cdef struct CCSSettingActionInfo:
	Bool key
	Bool button
	Bool bell
	Bool edge

cdef struct CCSSettingActionArrayInfo:
	Bool array[4]

cdef struct CCSSettingListInfo:
	CCSSettingType listType
	void * listInfo				#actually CCSSettingInfo *, works around pyrex

cdef union CCSSettingInfo:
	CCSSettingIntInfo forInt
	CCSSettingFloatInfo forFloat
	CCSSettingStringInfo forString
	CCSSettingActionInfo forAction
	CCSSettingActionArrayInfo forActionAsArray
	CCSSettingListInfo forList

cdef struct CCSSettingValue:
	CCSSettingValueUnion value
	void * parent
	Bool isListChild

cdef struct CCSGroup:
	char * name
	CCSSubGroupList * subGroups

cdef struct CCSSubGroup:
	char * name
	CCSSettingList * settings

cdef struct CCSPluginCategory:
	char * name
	char * shortDesc
	char * longDesc
	CCSStringList * plugins

cdef struct CCSContext:
	CCSPluginList * plugins
	CCSPluginCategory * categories
	void * priv
	CCSBackend * backend
	char * profile
	Bool deIntegration
	CCSSettingList * changedSettings
	Bool pluginsChanged

cdef struct CCSPlugin

cdef struct CCSSetting:
	char * name
	char * shortDesc
	char * longDesc
	CCSSettingType type
	Bool isScreen
	unsigned int screenNum
	CCSSettingInfo info
	char * group
	char * subGroup
	char * hints
	CCSSettingValue defaultValue
	CCSSettingValue * value
	Bool isDefault
	CCSPlugin * parent
	void * priv

cdef struct CCSPlugin:
	char * name
	char * shortDesc
	char * longDesc
	char * hints
	char * category
	char * filename
	CCSStringList * loadAfter
	CCSStringList * loadBefore
	CCSStringList * requiresPlugin
	CCSStringList * providesFeature
	CCSStringList * requiresFeature
	CCSSettingList * settings
	CCSGroupList * groups
	void * priv
	CCSContext * context

cdef struct CCSPluginConflict:
	char * value
	CCSPluginConflictType type
	CCSPluginList * plugins


cdef extern CCSContext * ccsContextNew()
cdef extern void ccsContextDestroy(CCSContext * context)

cdef extern CCSPlugin * ccsFindPlugin(CCSContext * context, char * name)
cdef extern CCSSetting * ccsFindSetting(CCSPlugin * plugin, char * name, Bool isScreen, int screenNum)

#cdef extern char * ccsColorToString(CCSSettingColorValue * color)
cdef extern char * ccsEdgeToString(CCSSettingActionValue * action)
cdef extern char * ccsKeyBindingToString(CCSSettingActionValue * action)
cdef extern char * ccsButtonBindingToString(CCSSettingActionValue * action)

#cdef extern Bool ccsSetInt(CCSSetting * setting, int data)
#cdef extern Bool ccsSetFloat(CCSSetting * setting, float data)
#cdef extern Bool ccsSetBool(CCSSetting * setting, Bool data)
#cdef extern Bool ccsSetString(CCSSetting * setting, char * data)
#cdef extern Bool ccsSetColor(CCSSetting * setting, CCSSettingColorValue data)
#cdef extern Bool ccsSetMatch(CCSSetting * setting, char * data)
cdef extern from 'string.h':
	ctypedef int size_t
	cdef extern char * strdup(char * s)
	cdef extern void memset(void * s, int c, size_t n)
	cdef extern void free(void * f)
	cdef extern void * malloc(size_t s)


#cdef extern Bool ccsStringToColor(char * value, CCSSettingColorValue * target)
cdef extern Bool ccsStringToKeyBinding(char * value, CCSSettingActionValue * target)
cdef extern Bool ccsStringToButtonBinding(char * value, CCSSettingActionValue * target)
cdef extern Bool ccsStringToEdge(char * value, CCSSettingActionValue * target)
cdef extern Bool ccsSetValue(CCSSetting * setting, CCSSettingValue * value)
cdef extern void ccsFreeSettingValue(CCSSettingValue * value)
cdef extern CCSSettingValueList * ccsSettingValueListAppend(CCSSettingValueList * l, CCSSettingValue * v)

cdef extern void ccsReadSettings(CCSContext * c)
cdef extern void ccsWriteSettings(CCSContext * c)
cdef extern void ccsWriteChangedSettings(CCSContext * c)
cdef extern void ccsResetToDefault(CCSSetting * s)

cdef extern void ccsPluginConflictListFree(CCSPluginConflictList * l, Bool FreOBJ)
cdef extern CCSPluginConflictList * ccsCanEnablePlugin(CCSContext * c, CCSPlugin * p)
cdef extern CCSPluginConflictList * ccsCanDisablePlugin(CCSContext * c, CCSPlugin * p)

cdef class Context
cdef class Plugin

cdef object UnpackStringList(CCSList * list):
	ret=[]
	while list != NULL:
		ret.append(<char *>list.data)
		list=list.next
	return ret

cdef CCSSettingType GetType(CCSSettingValue * value):
	if (value.isListChild):
		return (<CCSSetting *>value.parent).info.forList.listType
	else:
		return (<CCSSetting *>value.parent).type

cdef CCSSettingValue * EncodeValue(object data, CCSSetting * setting, Bool isListChild):
	cdef CCSSettingValue * bv
	cdef CCSSettingType t
	cdef CCSList * l
	bv = <CCSSettingValue *>malloc(sizeof(CCSSettingValue))
	memset(bv,0,sizeof(CCSSettingValue))
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
		ccsStringToKeyBinding(data[0],&bv.value.asAction)
		ccsStringToButtonBinding(data[1],&bv.value.asAction)
		if (data[2]):
			bv.value.asAction.onBell = 1
		else:
			bv.value.asAction.onBell = 0
		ccsStringToEdge(data[3],&bv.value.asAction)
	elif t == TypeList:
		l = NULL
		for item in data:
			l=ccsSettingValueListAppend(l,
					EncodeValue(item,setting,1))
		bv.value.asList=l
	return bv

cdef object DecodeValue(CCSSettingValue * value):
	cdef CCSSettingType t
	cdef char * s
	cdef CCSList * l
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
		s=ccsKeyBindingToString(&value.value.asAction)
		if s != NULL:
			ks=s
			free(s)
		else:
			ks='None'
		s=ccsButtonBindingToString(&value.value.asAction)
		if s != NULL:
			bs=s
			free(s)
		else:
			bs='None'
		if bs == 'Button0':
			bs = 'None'
		s=ccsEdgeToString(&value.value.asAction)
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
			lret.append(DecodeValue(<CCSSettingValue *>l.data))
			l=l.next
		return lret
	return 'Unhandled'

cdef class Setting:
	cdef CCSSetting * ccsSetting
	cdef object info
	cdef Plugin plugin

	def __new__(self, Plugin plugin, name, isScreen, screenNum=0):
		cdef CCSSettingType t
		cdef CCSSettingInfo * i
		self.ccsSetting = ccsFindSetting(plugin.ccsPlugin,
				name, isScreen, screenNum)
		self.plugin = plugin
		info=()
		t=self.ccsSetting.type
		i=&self.ccsSetting.info
		if t==TypeList:
			t=self.ccsSetting.info.forList.listType
			i=<CCSSettingInfo *>self.ccsSetting.info.forList.listInfo
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
		if self.ccsSetting.type == TypeList:
			info=(SettingTypeString[t],info)
		self.info=info
	
	def Reset(self):
		ccsResetToDefault(self.ccsSetting)

	property Plugin:
		def __get__(self):
			return self.plugin
	property Name:
		def __get__(self):
			return self.ccsSetting.name
	property ShortDesc:
		def __get__(self):
			return self.ccsSetting.shortDesc
	property LongDesc:
		def __get__(self):
			return self.ccsSetting.longDesc
	property Group:
		def __get__(self):
			return self.ccsSetting.group
	property SubGroup:
		def __get__(self):
			return self.ccsSetting.subGroup
	property Type:
		def __get__(self):
			return SettingTypeString[self.ccsSetting.type]
	property Info:
		def __get__(self):
			return self.info
	property Hints:
		def __get__(self):
			if self.ccsSetting.hints == '':
				return []
			else:
				return str(self.ccsSetting.hints).split(';')[:-1]
	property IsDefault:
		def __get__(self):
			if self.ccsSetting.isDefault:
				return True
			return False
	property DefaultValue:
		def __get__(self):
			return DecodeValue(&self.ccsSetting.defaultValue)
	property Value:
		def __get__(self):
			return DecodeValue(self.ccsSetting.value)
		def __set__(self, value):
			cdef CCSSettingValue * sv
			sv = EncodeValue(value,self.ccsSetting,0)
			ccsSetValue(self.ccsSetting,sv)
			ccsFreeSettingValue(sv)
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
	cdef CCSPlugin * ccsPlugin
	cdef Context context
	cdef object screens
	cdef object display
	cdef object groups
	
	def __new__(self, Context context, name):
		cdef CCSList * setlist
		cdef CCSList * glist
		cdef CCSList * sglist
		cdef CCSSetting * sett
		cdef CCSGroup * gr
		cdef CCSSubGroup * sgr
		self.ccsPlugin = ccsFindPlugin(context.ccsContext,name)
		self.context = context
		self.screens = []
		self.display = {}
		self.groups = {}
		for n in range(0,context.NScreens):
			self.screens.append({})
		glist = self.ccsPlugin.groups
		while glist != NULL:
			gr=<CCSGroup *>glist.data
			self.groups[gr.name]={}
			sglist=gr.subGroups
			while sglist != NULL:
				sgr=<CCSSubGroup *>sglist.data
				scr=[]
				for n in range(0,context.NScreens):
					scr.append({})
				self.groups[gr.name][sgr.name]=SSGroup({},scr)
				sglist=sglist.next
			glist=glist.next
		setlist = self.ccsPlugin.settings
		while setlist != NULL:
			sett=<CCSSetting *>setlist.data
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
			return self.ccsPlugin.name
	property ShortDesc:
		def __get__(self):
			return self.ccsPlugin.shortDesc
	property LongDesc:
		def __get__(self):
			return self.ccsPlugin.longDesc
	property Category:
		def __get__(self):
			return self.ccsPlugin.category
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
			cdef CCSPluginConflictList * pl, * pls
			cdef CCSPluginConflict * pc
			cdef CCSPluginList * ppl
			cdef CCSPlugin * plg
			if self.Enabled:
				return []
			ret = []
			pl = ccsCanEnablePlugin(self.context.ccsContext,
					self.ccsPlugin)
			pls = pl
			while pls != NULL:
				pc = <CCSPluginConflict *>pls.data
				rpl = []
				ppl = pc.plugins
				while ppl != NULL:
					plg = <CCSPlugin *>ppl.data
					rpl.append(self.context.Plugins[plg.name])
					ppl = ppl.next
				ret.append((ConflictTypeString[pc.type],pc.value,rpl))
				pls = pls.next
			if pl != NULL:
				ccsPluginConflictListFree(pl, True)
			return ret
	property DisableConflicts:
		def __get__(self):
			cdef CCSPluginConflictList * pl, * pls
			cdef CCSPluginConflict * pc
			cdef CCSPluginList * ppl
			cdef CCSPlugin * plg
			if not self.Enabled:
				return []
			ret = []
			pl = ccsCanDisablePlugin(self.context.ccsContext,
					self.ccsPlugin)
			pls = pl
			while pls != NULL:
				pc = <CCSPluginConflict *>pls.data
				rpl = []
				ppl = pc.plugins
				while ppl != NULL:
					plg = <CCSPlugin *>ppl.data
					rpl.append(self.context.Plugins[plg.name])
					ppl = ppl.next
				ret.append((ConflictTypeString[pc.type],pc.value,rpl))
				pls = pls.next
			if pl != NULL:
				ccsPluginConflictListFree(pl, True)
			return ret

cdef class Context:
	cdef CCSContext * ccsContext
	cdef object plugins
	cdef object categories
	cdef int nScreens

	def __new__(self,nScreens=1):
		cdef CCSPlugin * pl
		cdef CCSList * pll
		self.nScreens=nScreens
		self.plugins={}
		self.ccsContext=ccsContextNew()
		ccsReadSettings(self.ccsContext)
		pll=self.ccsContext.plugins
		self.categories={}
		while pll != NULL:
			pl = <CCSPlugin *>pll.data
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
		ccsContextDestroy(self.ccsContext)

	def Write(self,onlyChanged=True):
		if onlyChanged:
			ccsWriteChangedSettings(self.ccsContext)
		else:
			ccsWriteSettings(self.ccsContext)

	def Read(self):
		ccsReadSettings(self.ccsContext)

	property Plugins:
		def __get__(self):
			return self.plugins
	property Categories:
		def __get__(self):
			return self.categories
	property NScreens:
		def __get__(self):
			return self.nScreens

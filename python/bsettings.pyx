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

cdef struct BSPlugin

cdef struct BSPluginList:
	BSPlugin * data

cdef extern struct BSStringList
cdef extern struct BSSettingList
cdef extern struct BSGroupList

cdef struct BSContext:
	BSPluginList * plugins

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


cdef extern BSContext * bsContextNew()
cdef extern void bsContextDestroy(BSContext * context)
cdef extern unsigned int bsPluginListLength(BSPluginList * list)
cdef extern BSPluginList * bsPluginListGetItem(BSPluginList * list, unsigned int idx)
cdef extern BSPlugin * bsFindPlugin(BSContext * context, char * name)

cdef class Context

cdef class Plugin:
	cdef BSPlugin * bsPlugin
	
	def __new__(self,Context context,name):
		self.bsPlugin = bsFindPlugin(context.bsContext,name)
	
	property Name:
		def __get__(self):
			return self.bsPlugin.name
	property ShortDesc:
		def __get__(self):
			return self.bsPlugin.shortDesc
	property LongDesc:
		def __get__(self):
			return self.bsPlugin.longDesc

cdef class Context:
	cdef BSContext * bsContext
	cdef object plugins

	def __new__(self):
		cdef BSPlugin * pl
		self.plugins={}
		self.bsContext=bsContextNew()
		for n in range(0,bsPluginListLength(self.bsContext.plugins)):
			pl = bsPluginListGetItem(self.bsContext.plugins,n).data
			self.plugins[pl.name]=Plugin(self,pl.name)

	def __dealloc__(self):
		bsContextDestroy(self.bsContext)

	property Plugins:
		def __get__(self):
			return self.plugins

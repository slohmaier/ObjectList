import os
import sys
from functools import wraps

import NVDAObjects.IAccessible
import addonHandler
import config
import globalPluginHandler
import ui
import wx
from scriptHandler import script
from gui.settingsDialogs import SettingsPanel
from logHandler import log
import api
import NVDAObjects

#make _() available
addonHandler.initTranslation()

#configuration for settings
config.conf.spec["ObjectList"] = {
	#'whitelist': 'string(default=\'\')'
}

def indexObject(parent: NVDAObjects.IAccessible.NVDAObject, indent='  '):
	output = []
	for child in parent.children:
		output.append([
			indent,
			str(child.name),
			child.role.name,
			str(child.states),
			str(child.isFocusable),
			str(child.isProtected),
		])
		output += indexObject(child, indent + '--')
	return output

def listObjects(obj: NVDAObjects.IAccessible.NVDAObject):
	while obj is not None and type(obj.parent) is not NVDAObjects.IAccessible.WindowRoot:
		obj = obj.parent

	if obj is None:
		ui.message('No WindowRoot found')
		return None
	else:
		return indexObject(obj)

class ObjectList(wx.Dialog):
	def __init__(self, focusObject: NVDAObjects.IAccessible.NVDAObject, reverse=False):
		# Translators: The title of the Specific Search dialog.
		wx.Dialog.__init__(self, None, title=_("ObjectList"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

		ui.message('ObjectList dialog created')
		self.focusObject = focusObject

		#add one big scrollable label to the dialog with
		# a button below to refresh. text in label is selectable
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.label = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
		self.sizer.Add(self.label, 1, wx.EXPAND)
		self.refreshButton = wx.Button(self, label=_("Refresh"))
		self.refreshButton.Bind(wx.EVT_BUTTON, self.refresh)
		self.sizer.Add(self.refreshButton, 0, wx.EXPAND)
		self.SetSizer(self.sizer)

		self.refresh(None)	

	def refresh(self, event):
		table = listObjects(self.focusObject)
		if table is None:
			self.label.SetValue('No WindowRoot found')
			return
		#add header
		table.insert(0, ['Name', 'Role', 'States', 'Focusable', 'Protected'])
		#convert to string
		text = ''
		for row in table:
			text += ', '.join(row) + '\n'

		self.label.SetValue(text)


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("ObjectList")

	def __init__(self, *args, **kwargs):
		global service
		super(GlobalPlugin, self).__init__(*args, **kwargs)
	
	def show_objectlist(self):
		ui.message('showing objectlist')
		#show ObjectList dialog always on top
		self.objectList = ObjectList(api.getFocusObject())
		# add minimize and maximize buttons
		self.objectList.ShowModal()

	def script_show_objectlist(self, gesture):
		ui.message('showing objectlist wrappe')
		self.show_objectlist()
	script_show_objectlist.__doc__ = _("Show Objects in current window.")

	__gestures = {
		"kb:shift+NVDA+o": "show_objectlist",
	}

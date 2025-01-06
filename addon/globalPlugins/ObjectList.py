import os
import sys
from functools import wraps

import NVDAObjects.IAccessible
import addonHandler
import config
import globalPluginHandler
import gui
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
	output = ''
	for child in parent.children:
		child.role
		name = child.name
		if not name is None:
			#output commana separated: name, role, roleText, states
			output += f'{indent}{name}, {child.role}, {child.roleText}, {child.states}\n'
		output += indexObject(child, indent + '  ')
	return output

def listObjects(obj: NVDAObjects.IAccessible.NVDAObject):
	while obj is not None and type(obj.parent) is not NVDAObjects.IAccessible.WindowRoot:
		obj = obj.parent

	if obj is None:
		return 'No WindowRoot found'
	else:
		return indexObject(obj).strip()

class ObjectList(wx.Dialog):
	def __init__(self, focusObject: NVDAObjects.IAccessible.NVDAObject, reverse=False):
		# Translators: The title of the Specific Search dialog.
		super(ObjectList, self).__init__(parent, title=_("Specific search"))

		self.focusObject = focusObject

		#add one big scrollable label to the dialog with
		# a button below to refresh. text in label is selectable
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.label = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
		self.sizer.Add(self.label, 1, wx.EXPAND)
		self.refreshButton = wx.Button(self, label=_("Refresh"))
		self.sizer.Add(self.refreshButton, 0, wx.EXPAND)
		self.SetSizer(self.sizer)

	def refresh(self):
		self.label.SetValue(listObjects(self.focusObject))


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()

		#add settings to nvda
		#gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(ObjectListSettings)
	
	def show_objectlist(self):
		#show ObjectList dialog always on top
		dlg = ObjectList(None)
		dlg.ShowModal()
		dlg.Destroy()

	def script_show_objectlist(self, gesture):
		wx.CallAfter(self.show_objectlist)
	script_show_objectlist.__doc__ = _("Show Objects in current window.")

	__gestures = {
		"kb:shift+NVDA+o": "show_objectlist",
	}

class ObjectListSettings(SettingsPanel):
	title = 'ObjectList'
	panelDescription = 'ObjectList like Mac'

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		introItem = sHelper.addItem(wx.StaticText(self, label=self.panelDescription))
	
	def _loadSettings(self):
		pass

	def onSave(self):
		pass
	
	def onPanelActivated(self):
		self._loadSettings()
		self.Show()
	
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
from gui import SettingsPanel
from logHandler import log
import api
import NVDAObjects

#make _() available
addonHandler.initTranslation()

#configuration for settings
config.conf.spec["ObjectList"] = {
	#'whitelist': 'string(default=\'\')'
}

def findsObjects(parent: NVDAObjects.IAccessible.NVDAObject, indent='  '):
	for child in parent.children:
		log.info(indent + child.name)
		findsObjects(child, indent + '  ')

def indexObjects():
	obj = api.getFocusObject()
	# If no object is found, get the
	if obj is None:
		obj = api.getTopWindow()

    # If no object is found, return
	if obj is None:
		return

	findsObjects(obj)

class ObjectList(wx.Dialog):
	def __init__(self, parent, reverse=False):
		# Translators: The title of the Specific Search dialog.
		super(ObjectList, self).__init__(parent, title=_("Specific search"))

		indexObjects()

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()

		#add settings to nvda
		#gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(ObjectListSettings)

	@script(
		description=_("Show object list from desktol with filter and option to focues an object."),
		gesture="kb:NVDA+F8"
	)
	def script_showList(self, gesture):
		def run():
			gui.mainFrame.prePopup()
			d = ObjectList(gui.mainFrame, reverse=reverse)
			d.ShowModal()
			gui.mainFrame.postPopup()
		wx.CallAfter(run)

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

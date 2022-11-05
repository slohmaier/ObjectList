import os
import sys
from functools import wraps

import addonHandler
import config
import globalPluginHandler
import gui
import wx
from gui import SettingsPanel
from logHandler import log

distdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist32')
sys.path.append(distdir)
fy, set_languages

#make _() available
addonHandler.initTranslation()

#configuration for settings
config.conf.spec["LanguageIdentification"] = {
	'whitelist': 'string(default=\'\')'
}

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()

		#add settings to nvda
		#gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(ObjectListSettings)

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

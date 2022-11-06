import os
import sys
from functools import wraps

import addonHandler
import config
import globalPluginHandler
import gui
import wx
from scriptHandler import script
from gui import SettingsPanel
from logHandler import log

distdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist32')
sys.path.append(distdir)

#make _() available
addonHandler.initTranslation()

#configuration for settings
config.conf.spec["LanguageIdentification"] = {
	#'whitelist': 'string(default=\'\')'
}

class ObjectList(wx.Dialog):
	def __init__(self, parent, reverse=False):
		# Translators: The title of the Specific Search dialog.
		super(ObjectList, self).__init__(parent, title=_("Specific search"))

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

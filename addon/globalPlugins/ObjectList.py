from typing import List
import api
import NVDAObjects
import addonHandler
import config
import controlTypes
import globalPluginHandler
import gui.guiHelper
import ui
import wx
from logHandler import log
import gui
from gui.settingsDialogs import SettingsPanel

#make _() available
addonHandler.initTranslation()

#configuration for settings
config.conf.spec['ObjectList'] = {
	'defaultaction:': 'string(default=\'click\')',	
}
DEFAULT_ACTIONS = ['click', 'focus']
HIDDEN_CONTROLTYPES = [
	controlTypes.ROLE_WINDOW
]

def indexObject(parent: NVDAObjects.IAccessible.NVDAObject, indent='  ') -> List[NVDAObjects.IAccessible.NVDAObject]:
	objects = []
	for child in parent.children:
		if child.isFocusable and child.name is not None and child.role not in HIDDEN_CONTROLTYPES:
			objects.append([f'{child.role.displayString}: {child.name}', child])
		objects += indexObject(child, indent + '--')
	return objects

def listObjects(obj: NVDAObjects.IAccessible.NVDAObject):
	# iterate to parent until role is Window
	while obj is not None and obj.role != controlTypes.ROLE_WINDOW:
		obj = obj.parent

	# if no window found output error message
	if obj is None:
		return None
	else:
		return indexObject(obj)

class ObjectList(wx.Dialog):
	def __init__(self, objects: List[NVDAObjects.IAccessible.NVDAObject]):
		# Translators: The title of the Specific Search dialog.
		wx.Dialog.__init__(self, None, title=_("ObjectList"))

		self.data = objects
		
		self.filtered_data = self.data
		self.Bind(wx.EVT_ACTIVATE, self.on_activate)
	
		panel = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)

		# Suchfeld
		self.search_field = wx.TextCtrl(panel)
		self.search_field.Bind(wx.EVT_TEXT, self.on_search)
		vbox.Add(self.search_field, 0, wx.EXPAND | wx.ALL, 5)

		# Liste
		self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.NO_BORDER)
		self.list_ctrl.SetWindowStyleFlag(wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.NO_BORDER) 
		self.list_ctrl.InsertColumn(0, _("UI Elements"), width=400)
		self.update_list(self.data)
		vbox.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)

		# Buttons
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		focus_button = wx.Button(panel, label="Focus")
		focus_button.Bind(wx.EVT_BUTTON, self.on_focus)
		hbox.Add(focus_button, 0, wx.ALL, 5)
		click_button = wx.Button(panel, label="Click")
		click_button.Bind(wx.EVT_BUTTON, self.on_click)
		hbox.Add(click_button, 0, wx.ALL, 5)
		vbox.Add(hbox, 0, wx.ALIGN_CENTER | wx.ALL, 5)

		panel.SetSizer(vbox)
		self.Centre()

		# Bind events
		self.search_field.Bind(wx.EVT_KEY_DOWN, self.on_key_press)

		# Accelerator
		accel_tbl = wx.AcceleratorTable([(wx.ACCEL_ALT, ord('F'), focus_button.GetId()),
										(wx.ACCEL_ALT, ord('C'), click_button.GetId())])
		self.SetAcceleratorTable(accel_tbl)

		# focus
		self.SetFocus()
		self.search_field.SetFocus()
		ui.message(_("ObjectList opened"))

	def on_activate(self, event):
		if not event.GetActive():  # Check if the dialog is being deactivated
			ui.message(_("ObjectList closed"))
			self.Close()

	def on_key_press(self, event):
		keycode = event.GetKeyCode()
		if keycode == wx.WXK_ESCAPE:
			ui.message(_("ObjectList closed"))
			self.Close()
		elif keycode == wx.WXK_DOWN:
			current_index = self.list_ctrl.GetFirstSelected()
			next_index = min(current_index + 1, self.list_ctrl.GetItemCount() - 1)
			self.list_ctrl.Select(current_index, False)
			self.list_ctrl.Select(next_index, True)
			self.list_ctrl.Focus(next_index)
			dataIndex = self.list_ctrl.GetItemData(next_index)
			text = self.filtered_data[dataIndex][0]
			ui.message(text)  # Speak the selected item
		elif keycode == wx.WXK_UP:
			current_index = self.list_ctrl.GetFirstSelected()
			previous_index = max(current_index - 1, 0)
			self.list_ctrl.Select(current_index, False)
			self.list_ctrl.Select(previous_index, True)
			self.list_ctrl.Focus(previous_index)
			dataIndex = self.list_ctrl.GetItemData(previous_index)
			text = self.filtered_data[dataIndex][0]
			ui.message(text)  # Speak the selected item
		else:
			event.Skip()

	def on_search(self, event):
		search_text = self.search_field.GetValue().lower()
		self.filtered_data = [row for row in self.data if search_text in row[0].lower()]
		self.update_list(self.filtered_data)
		if self.list_ctrl.GetItemCount() > 0:
			self.list_ctrl.Select(0, True)  # Select the first item
			self.list_ctrl.Focus(0)
			text = self.list_ctrl.GetItemText(0)
			ui.message(text)

	def update_list(self, data):
		self.list_ctrl.DeleteAllItems()
		rowi = 0
		for row in data:
			index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), row[0])
			self.list_ctrl.SetItemData(index, rowi)
			rowi += 1

	def on_focus(self, event):
		index = self.list_ctrl.GetFirstSelected()
		if index != -1:  # Check if an item is selected
			text = self.list_ctrl.GetItemText(index)
			obj : NVDAObjects.NVDAObject = self.filtered_data[self.list_ctrl.GetItemData(index)][1]
			ui.message(f"Focus: Text - {text}, Object - {str(obj)}")
			obj.setFocus()
			self.Close()
		else:
			ui.message(_("No Ui Element selected"))

	def on_click(self, event):
		index = self.list_ctrl.GetFirstSelected()
		if index != -1:  # Check if an item is selected
			text = self.list_ctrl.GetItemText(index)
			obj : NVDAObjects.NVDAObject = self.filtered_data[self.list_ctrl.GetItemData(index)][1]
			ui.message(f"Click: Text - {text}, Object - {str(obj)}")
			obj.setFocus()
			obj.doAction()
			self.Close()
		else:
			ui.message(_("No Ui Element selected"))

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("ObjectList")

	def __init__(self, *args, **kwargs):
		global service
		super(GlobalPlugin, self).__init__(*args, **kwargs)

		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(ObjectListSettings)
	
	def show_objectlist(self):
		# get objects
		ui.message(_('Getting ObjectList. Please wait...'))
		objects = listObjects(api.getFocusObject())
		if objects is None:
			ui.message(_('No WindowRoot found'))
		else:
			#show ObjectList dialog always on top
			self.objectList = ObjectList(objects)
			# add minimize and maximize buttons
			self.objectList.Raise()
			self.objectList.ShowModal()

	def script_show_objectlist(self, gesture):
		wx.CallAfter(self.show_objectlist)
	script_show_objectlist.__doc__ = _("Show Objects in current window.")

	__gestures = {
		"kb:shift+NVDA+o": "show_objectlist",
	}

class ObjectListSettings(SettingsPanel):
	title = 'ObjectList'

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		
		# add decsriptive text
		sHelper.addItem(wx.StaticText(self, label=_('Choose default action for hitting Enter, when searching:')))

		#add radio buttons aside each other for every DEFAULT_ACTIONS
		self._radioButtons = {}
		self.defaultActionRadio = wx.RadioBox(self, choices=DEFAULT_ACTIONS, style=wx.RA_SPECIFY_COLS)
		sHelper.addItem(self.defaultActionRadio)

		self._loadSettings()
	
	def _loadSettings(self):
		self.defaultActionRadio.SetStringSelection(config.conf['ObjectList'].get('defaultaction', 'click'))

	def onSave(self):
		config.conf['ObjectList']['defaultaction'] = self.defaultActionRadio.GetStringSelection()
	
	def onPanelActivated(self):
		self._loadSettings()
		self.Show()

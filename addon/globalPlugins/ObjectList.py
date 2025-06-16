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

import comtypes.client
import comtypes
from ctypes import windll
from comtypes.gen import _944DE083_8FB8_45CF_BCB7_C477ACB2F897_0_1_0

#make _() available
addonHandler.initTranslation()

#configuration for settings
config.conf.spec['ObjectList'] = {
	'defaultaction:': 'string(default=\'click\')',	
}
DEFAULT_ACTIONS = ['click', 'focus']

# Control type mapping
CONTROL_TYPE_NAMES = {
    50000: "Button",
    50001: "Calendar",
    50002: "CheckBox",
    50003: "ComboBox",
    50004: "Edit",
    50005: "Hyperlink",
    50006: "Image",
    50007: "ListItem",
    50008: "List",
    50009: "Menu",
    50010: "MenuBar",
    50011: "MenuItem",
    50012: "ProgressBar",
    50013: "RadioButton",
    50014: "ScrollBar",
    50015: "Slider",
    50016: "Spinner",
    50017: "StatusBar",
    50018: "Tab",
    50019: "TabItem",
    50020: "Text",
    50021: "ToolBar",
    50022: "ToolTip",
    50023: "Tree",
    50024: "TreeItem",
    50025: "Custom",
    50026: "Group",
    50027: "Thumb",
    50028: "DataGrid",
    50029: "DataItem",
    50030: "Document",
    50031: "SplitButton",
    50032: "Window",
    50033: "Pane",
    50034: "Header",
    50035: "HeaderItem",
    50036: "Table",
    50037: "TitleBar",
    50038: "Separator",
    50039: "SemanticZoom",
    50040: "AppBar"
}

# Init COM
comtypes.CoInitialize()

# Create UI Automation instance via CLSID
CLSID_CUIAutomation = '{FF48DBA4-60EF-4201-AA87-54103EEF594E}'
uia = comtypes.client.CreateObject(
	CLSID_CUIAutomation,
	interface=_944DE083_8FB8_45CF_BCB7_C477ACB2F897_0_1_0.IUIAutomation
)

def index_current_window():
	# Get foreground window
	hwnd = windll.user32.GetForegroundWindow()
	root = uia.ElementFromHandle(hwnd)
	walker = uia.ControlViewWalker

	return collect_elements(walker, root)

# Recursive UI walk function
def collect_elements(walker, element, depth=0):
    elements = []
    try:
        name = element.CurrentName
        ctrl_id = element.CurrentControlType
        ctrl_type = CONTROL_TYPE_NAMES.get(ctrl_id, f"Unknown({ctrl_id})")
        label = f"{ctrl_type}: \"{name}\"".strip()
        elements.append((label, element))
    except Exception:
        pass

    # Recurse
    child = walker.GetFirstChildElement(element)
    while child:
        elements.extend(collect_elements(walker, child))
        child = walker.GetNextSiblingElement(child)

    return elements

def click(element):
    try:
        invoke = element.GetCurrentPattern(_944DE083_8FB8_45CF_BCB7_C477ACB2F897_0_1_0.UIA_InvokePatternId)
        invoke.Invoke()
        return True
    except Exception:
        return False

class ObjectList(wx.Dialog):
	def __init__(self, objects: List[tuple]):
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
			obj = self.filtered_data[self.list_ctrl.GetItemData(index)][1]
			ui.message(f"Focus: Text - {text}, Object - {str(obj)}")
			focus(obj)
			self.Close()
		else:
			ui.message(_("No Ui Element selected"))

	def on_click(self, event):
		index = self.list_ctrl.GetFirstSelected()
		if index != -1:  # Check if an item is selected
			text = self.list_ctrl.GetItemText(index)
			obj = self.filtered_data[self.list_ctrl.GetItemData(index)][1]
			ui.message(f"Click: Text - {text}, Object - {str(obj)}")
			click(obj)
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
		objects = index_current_window()
		if objects is None or len(objects) == 0:
			# Translators: Message shown when no objects are found in the current window.
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

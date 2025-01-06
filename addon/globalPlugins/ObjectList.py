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
	objects = []
	for child in parent.children:
		if child.isFocusable and child.name is not None:
			objects.append([child.role.name, child.name, child])
		objects += indexObject(child, indent + '--')
	return objects

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

		ui.message(_('Getting ObjectList. Please wait...'))

		self.data = listObjects(focusObject)
	
		panel = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)

		# Suchfeld
		self.search_field = wx.TextCtrl(panel)
		self.search_field.Bind(wx.EVT_TEXT, self.on_search)
		vbox.Add(self.search_field, 0, wx.EXPAND | wx.ALL, 5)

		# Tabelle
		self.grid = gridlib.Grid(panel)
		self.grid.CreateGrid(len(self.data), 2)
		self.grid.SetColLabelValue(0, "Rolle")
		self.grid.SetColLabelValue(1, "Name")
		self.update_grid(self.data)
		vbox.Add(self.grid, 1, wx.EXPAND | wx.ALL, 5)

		# Buttons
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		focus_button = wx.Button(panel, label="_Focus")
		focus_button.Bind(wx.EVT_BUTTON, self.on_focus)
		hbox.Add(focus_button, 0, wx.ALL, 5)
		click_button = wx.Button(panel, label="_Click")
		click_button.Bind(wx.EVT_BUTTON, self.on_click)
		hbox.Add(click_button, 0, wx.ALL, 5)
		vbox.Add(hbox, 0, wx.ALIGN_CENTER | wx.ALL, 5)

		panel.SetSizer(vbox)
		self.Centre()
		self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)
		self.Bind(wx.EVT_CHAR_HOOK, self.on_key_press)
		self.search_field.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
		self.Show(True)

	def on_search(self, event):
		search_text = self.search_field.GetValue().lower()
		filtered_data = [row for row in self.data if search_text in row[0].lower() or search_text in row[1].lower()]
		self.update_grid(filtered_data)
		self.search_field.SetFocus()

	def update_grid(self, data):
		self.grid.ClearGrid()
		for i, row in enumerate(data):
			for j, cell in enumerate(row[:2]): # Nur "Rolle" und "Name" anzeigen
				self.grid.SetCellValue(i, j, str(cell))
		self.grid.AutoSizeColumns()

	def on_focus(self, event):
		pass  # Leerer Handler für den _Focus Button

	def on_click(self, event):
		pass  # Leerer Handler für den _Click Button

	def on_kill_focus(self, event):
		self.Close()

	def on_key_press(self, event):
		keycode = event.GetKeyCode()
		if keycode == wx.WXK_ESCAPE:
			self.Close()
		else:
			event.Skip()
	
	def on_key_down(self, event):
		keycode = event.GetKeyCode()
		if keycode == wx.WXK_DOWN:
			current_row = self.grid.GetGridCursorRow()
			next_row = min(current_row + 1, self.grid.GetNumberRows() - 1)
			self.grid.SetGridCursor(next_row, 0)
		elif keycode == wx.WXK_UP:
			current_row = self.grid.GetGridCursorRow()
			previous_row = max(current_row - 1, 0)
			self.grid.SetGridCursor(previous_row, 0)
		else:
			event.Skip()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("ObjectList")

	def __init__(self, *args, **kwargs):
		global service
		super(GlobalPlugin, self).__init__(*args, **kwargs)
	
	def show_objectlist(self):
		#show ObjectList dialog always on top
		self.objectList = ObjectList(api.getFocusObject())
		# add minimize and maximize buttons
		self.objectList.ShowModal()

	def script_show_objectlist(self, gesture):
		self.show_objectlist()
	script_show_objectlist.__doc__ = _("Show Objects in current window.")

	__gestures = {
		"kb:shift+NVDA+o": "show_objectlist",
	}

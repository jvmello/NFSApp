# coding: utf-8
import kivy
import sys
import os
import zxing

from PostgreSQL import PostgreSQL
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.config import Config
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior

db = PostgreSQL()
db.connect()
db.setCursor()

MAX_TABLE_COLS = 5
t = '-1'

class Info(Screen):
	mode = StringProperty("")
	label_rec_id = StringProperty("UserID")
	start_point = NumericProperty(0)
	col_data = ListProperty(["", "", "", "", ""])

	def __init__(self, obj, **kwargs):
		super(Info, self).__init__(**kwargs)

class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior, RecycleGridLayout):
	pass

class SelectableButton(RecycleDataViewBehavior, Button):
	index = None
	selected = BooleanProperty(False)
	selectable = BooleanProperty(True)
	rv_data = ObjectProperty(None)
	start_point = NumericProperty(0)
	mode = StringProperty("")

	def refresh_view_attrs(self, rv, index, data):
		self.index = index
		return super(SelectableButton, self).refresh_view_attrs(rv, index, data)

	def on_touch_down(self, touch):
		if super(SelectableButton, self).on_touch_down(touch):
			return True
		if self.collide_point(*touch.pos) and self.selectable:
			return self.parent.select_with_touch(self.index, touch)

	def apply_selection(self, rv, index, is_selected):
		self.selected = is_selected
		self.rv_data = rv.data

	def on_press(self):
		self.start_point = 0
		end_point = MAX_TABLE_COLS
		rows = len(self.rv_data) // MAX_TABLE_COLS
		for row in range(rows):
			if self.index in list(range(end_point)):
				break
			self.start_point += MAX_TABLE_COLS
			end_point += MAX_TABLE_COLS

class RV(BoxLayout):
	rv_data = ListProperty([])
	start_point = NumericProperty(0)
	mode = StringProperty("")

	def __init__(self, **kwargs):
		super(RV, self).__init__(**kwargs)
		self.get_users()

	def get_users(self):
		self.rv_data = []
		rows = db.buscarProdutos(t)

		for row in rows:
			print("ok")
			for col in row:
				print("col ", col)
				if(col != row[1]):
					if(col == row[5]):
						col = 'End.'

					self.rv_data.append(col)

	def add_record(self):
		self.mode = "Add"
		popup = Info(self)
		popup.open()

	def update(self, tex):
		global t
		t = tex
		self.get_users()

		print(t)

class Main(Screen):
	def build(self):
		return RV()
	pass

class CameraClick(Screen):
    def capture(self):
        camera = self.ids['camera']
        camera.export_to_png("IMG.png")

        reader = zxing.BarCodeReader()
        barcode = reader.decode("IMG.png")

        db.inserirNFE(barcode)

class KeyCode(Screen):
	def insert(self, chave):
		db.InserirNFE(chave)

class UserPage(Screen):
	def ler(self):
		self.manager.current = "cam"

	def busca(self):
		self.manager.current = "search"
	
	def key(self):
		self.manager.current = "key"

class Camera(Screen):
    pass

class ScreenManagement(ScreenManager):
	pass

class LoginApp(App):
	def build(self):
		self.title = "NFSearch"
		main_widget = Builder.load_string(open("NFS.kv", encoding="utf-8").read())
		return main_widget

if __name__ == '__main__':
	LoginApp().run()

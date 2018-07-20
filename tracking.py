import datetime as dt

from kivy.app import App

from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput


TABLES_RATIO = 0.75

TABLES = None
QUEUE = None

EARLY_STUDENT = 2.40
EARLY_ADULT =   2.40
LATE_STUDENT =  3.00
LATE_ADULT =    3.90


def calculateRate(clock_in, clock_out, type):
	assert type in ('adult','student')
	rate_threshold = clock_in.replace(hour=6, minute=0, second=0, microsecond=0)
	ER = EARLY_ADULT if type == 'adult' else EARLY_STUDENT
	LR = LATE_ADULT if type == 'adult' else LATE_STUDENT
	cost = 0
	
	if clock_in.hour >= 6 and clock_in.hour < 18:
		if clock_out < rate_threshold:
			time_delta = clock_out - clock_in
			cost += time_delta.seconds/3600*ER
		else:
			time_delta = rate_threshold - clock_in
			cost += time_delta.seconds/3600*ER
			time_delta = clock_out - rate_threshold
			cost += time_delta.seconds/3600*LR
	else:
		time_delta = clock_out - clock_in
		cost += time_delta.seconds/3600*LR
		
	return round(cost/0.05)*0.05


class Table:
	"""A table is a data structure holding the details of a table."""
	
	def __init__(self, adults=0, students=0, description="", clock_in=None):
		self.adults = adults
		self.students = students
		self.description = description
		self.clock_in = clock_in if clock_in else dt.datetime.now()
		
	def __add__(self, otherTable):
		return Table(
			self.adults + otherTable.adults,
			self.students + otherTable.students,
			self.description + ", " + otherTable.description,
			min(self.clock_in, otherTable.clock_in)
		)

class TableTrackingApp(App):
	"""TableTrackingApp inherits from App. Its build() method needs to
	return a widget containing the entirity of the program that will be
	rendered."""
	
	def build(self):
		return AppContainer()
	
class AppContainer(GridLayout):
	"""AppContainer, the main widget for the app, is a grid layout with two
	elements: a grid of tables and a scrollable list of unassigned tables
	called the queue. Tables are initially added to the queue, then can be
	assigned to a physical table on the left later."""
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		self.rows = 1
		self.cols = 2
		
		global TABLES, QUEUE
		
		TABLES = self.table_container = TableContainer(size_hint_x = TABLES_RATIO)
		self.add_widget(self.table_container)
		
		QUEUE = self.queue_container = QueueContainer(size_hint_x = 1-TABLES_RATIO)
		self.add_widget(self.queue_container)
		
class TableContainer(GridLayout):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		self.rows = 6
		self.cols = 4
		self.spacing = "10px"
		self.padding = "10px"
		
		self.add_widget(Label(text=''))
		self.add_widget(Label(text=''))
		self.add_widget(TableButton(main_text='ping pong table'))
		self.add_widget(TableButton(main_text='table 16'))
		
		self.add_widget(Label(text=''))
		self.add_widget(Label(text=''))
		self.add_widget(Label(text=''))
		self.add_widget(TableButton(main_text='table 15'))
		
		self.add_widget(TableButton(main_text='table 4'))
		self.add_widget(TableButton(main_text='table 8'))
		self.add_widget(Label(text=''))
		self.add_widget(TableButton(main_text='table 14'))
		
		self.add_widget(TableButton(main_text='table 3'))
		self.add_widget(TableButton(main_text='table 7'))
		self.add_widget(TableButton(main_text='table 10'))
		self.add_widget(TableButton(main_text='table 13'))
		
		self.add_widget(TableButton(main_text='table 2'))
		self.add_widget(TableButton(main_text='table 6'))
		self.add_widget(Label(text=''))
		self.add_widget(TableButton(main_text='table 12'))
		
		self.add_widget(TableButton(main_text='table 1'))
		self.add_widget(TableButton(main_text='table 5'))
		self.add_widget(TableButton(main_text='table 9'))
		self.add_widget(TableButton(main_text='table 11'))

# TableButtons should have two different possible behaviors when clicked:
# 1. When clicked and housing a table, it should provide most TableOptions
# 2. When clicked after clicking the Assign Table button on the QueueTableOptions,
# it should either assign or merge the table.
# Perhaps the buttons should change color when they can be assigned?
class TableButton(Button):
	def __init__(self, main_text, **kwargs):
		super().__init__(**kwargs)
		self.main_text = main_text
		self.table = None
		
		self.render()
		
	def render(self):
		if self.table:
			self.text = "\n".join([self.main_text, self.table.description, self.clock_in])
		else:
			self.text = "\n" + self.main_text + "\n"
		
class QueueContainer(ScrollView):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.inner_queue = StackLayout(padding="10px", spacing="10px")
		self.add_widget(self.inner_queue)
		
		add_table_btn = Button(text='Queue Customers', size_hint_y=.1)
		add_table_btn.bind(on_press=lambda e: ClockInPopup().open())
		self.inner_queue.add_widget(add_table_btn)
		
class ClockInPopup(Popup):
	"""A popup called from the "Queue Customers" buttons of the QueueContainer.
	It collects the information necessary to clock someone in."""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		self.title = 'Clock In Customers'
		self.size_hint = (0.67, 0.67)
		self.content = GridLayout(rows=5, cols=1)
		
		self.clock_row = ClockRow()
		self.content.add_widget(self.clock_row)
		
		self.description_row = DescriptionRow()
		self.content.add_widget(self.description_row)
		
		self.adult_row = PeopleRow('Adults')
		self.content.add_widget(self.adult_row)
		
		self.student_row = PeopleRow('Students')
		self.content.add_widget(self.student_row)
		
		self.final_row = Button(text='Add to Queue')
		self.final_row.bind(on_press=self.add_to_queue)
		self.content.add_widget(self.final_row)
		
	def add_to_queue(self, event):
		QUEUE.inner_queue.add_widget(
			QueueButton(
				Table(
					self.adult_row.value,
					self.student_row.value,
					self.description_row.input.text,
					self.clock_row.clock_in_time
				),
				size_hint_y = .1
			)
		)
		self.dismiss()
		
class ClockRow(GridLayout):
	"""A row of widgets for selecting the clock in time for a table used
	by a ClockInPopup."""
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.rows = 1
		self.cols = 3
		
		self.padding = "10px"
		self.spacing = "10px"
		
		self.clock_in_time = dt.datetime.now()
		self.time_display = Label(text=self.clock_in_time.strftime('%I:%M %p'))
		self.add_widget(self.time_display)
		
		self.sub_btn = Button(text='-5 min.')
		self.sub_btn.bind(on_press=self.subtract_time)
		self.add_widget(self.sub_btn)
		
		self.add_btn = Button(text='+5 min.')
		self.add_btn.bind(on_press=self.add_time)
		self.add_widget(self.add_btn)
		
	def subtract_time(self, event):
		minutes_mod_five = self.clock_in_time.minute % 5
		amount_to_sub = minutes_mod_five if minutes_mod_five != 0 else 5
		self.clock_in_time -= dt.timedelta(minutes=amount_to_sub)
		self.time_display.text = self.clock_in_time.strftime('%I:%M %p')
		
	def add_time(self, event):
		minutes_mod_five = self.clock_in_time.minute % 5
		amount_to_add = 5-minutes_mod_five if minutes_mod_five != 0 else 5
		self.clock_in_time += dt.timedelta(minutes=amount_to_add)
		self.time_display.text = self.clock_in_time.strftime('%I:%M %p')
		
class DescriptionRow(GridLayout):
	"""A row of widgets for entering the description for a table used by
	a ClockInPopup."""
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.rows = 1
		self.cols = 2
		
		self.add_widget(Label(text='Description'))
		self.input = TextInput()
		self.add_widget(self.input)
		
class PeopleRow(GridLayout):
	"""A row of widgets for selecting the number of "type" people for a
	table used by a ClockInPopup."""
	max_value = 6
	
	def __init__(self, type, intial_value=0, **kwargs):
		super().__init__(**kwargs)
		self.rows = 1
		self.cols = 4
		
		self.type = type
		self.value = intial_value
		
		self.add_widget(Label(text='{}:'.format(self.type)))
		
		self.number_label = Label(text=str(self.value))
		self.add_widget(self.number_label)
		
		self.sub_btn = Button(text='-')
		if self.value == 0: self.sub_btn.disabled = True
		self.sub_btn.bind(on_press=self.decrease_value)
		self.add_widget(self.sub_btn)
		
		self.add_btn = Button(text='+')
		if self.value == PeopleRow.max_value: self.add_btn.disabled = True
		self.add_btn.bind(on_press=self.increase_value)
		self.add_widget(self.add_btn)
	
	def decrease_value(self, event):
		self.value -= 1
		if self.value == 0: self.sub_btn.disabled = True
		if self.value != PeopleRow.max_value: self.add_btn.disabled = False
		self.number_label.text = str(self.value)
		
	def increase_value(self, event):
		self.value += 1
		if self.value != 0: self.sub_btn.disabled = False
		if self.value == PeopleRow.max_value: self.add_btn.disabled = True
		self.number_label.text = str(self.value)
	
class QueueButton(Button):
	def __init__(self, table, **kwargs):
		super().__init__(**kwargs)
		self.table = table
		
		self.bind(on_press=lambda e: QueueTableOptionsPopup(self).open())
		self.render()
		
	def render(self): #I made it one statement, but its soooo ugly
		people_display = ", ".join([x for x in [
			"{} adult{}".format(
				self.table.adults, ("s","")[self.table.adults==1]
			) if self.table.adults else None,
			"{} student{}".format(
				self.table.students, ("s","")[self.table.students==1]
			) if self.table.students else None,
		] if x is not None])
			
		time_display = self.table.clock_in.strftime("%I:%M %p")
			
		self.text = "\n".join([time_display, self.table.description, people_display])
		
class QueueTableOptionsPopup(Popup):
	"""A popup called from a QueueButton."""
	def __init__(self, queue_btn, **kwargs):
		super().__init__(**kwargs)
		self.queue_btn = queue_btn
		
		self.title = 'Options'
		self.size_hint = (0.67, 0.67)
		self.content = GridLayout(rows=2, cols=1)
		
		self.rate_calculation = Label(text='$5')
		self.content.add_widget(self.rate_calculation)
		
		self.button_row = GridLayout(rows=1, cols=3)
		self.content.add_widget(self.button_row)
		
		self.assign_table_btn = Button(text='Assign Table')
		self.assign_table_btn.bind(on_press=self.assign_table)
		self.button_row.add_widget(self.assign_table_btn)
		
		self.edit_customer_btn = Button(text='Edit Customer')
		self.edit_customer_btn.bind(on_press=self.edit_customer)
		self.button_row.add_widget(self.edit_customer_btn)
		
		self.clock_out_btn = Button(text='Clock Out')
		self.clock_out_btn.bind(on_press=self.clock_out)
		self.button_row.add_widget(self.clock_out_btn)
		
	def assign_table(self, event):
		pass
		
	def edit_customer(self, event):
		EditCustomerPopup(self.queue_btn).open()
		self.dismiss()
		
	def clock_out(self, event):
		QUEUE.inner_queue.remove_widget(self.queue_btn)
		self.dismiss()

class EditCustomerPopup(Popup):
		"""testing editing a customer based on clocking ina customer"""
		def __init__(self, current_customer, **kwargs):
				super(EditCustomerPopup, self).__init__(**kwargs)
				self.current_customer = current_customer

				self.title = 'Edit Customer'
				self.size_hint = (0.67, 0.67)
				self.content = GridLayout(rows=6, cols=1)
				
				self.clock_row = ClockRow()				
				self.clock_row.clock_in_time = self.current_customer.table.clock_in
				self.clock_row.time_display.text = self.current_customer.table.clock_in.strftime('%I:%M %p')
				self.content.add_widget(self.clock_row)

				self.description_row = DescriptionRow()
				self.description_row.input.text = self.current_customer.table.description
				self.content.add_widget(self.description_row)				
				
				self.adult_row = PeopleRow('Adults', current_customer.table.adults)
				self.content.add_widget(self.adult_row)
				
				self.student_row = PeopleRow('Students', current_customer.table.students)
				self.content.add_widget(self.student_row)
				
				self.final_row = Button(text='Confirm')
				self.final_row.bind(on_press=self.confirm)
				self.content.add_widget(self.final_row)

				self.cancel_row = Button(text='Cancel')
				self.cancel_row.bind(on_press=self.cancel_changes)
				self.content.add_widget(self.cancel_row)
				
		def confirm(self, event):                
				self.current_customer.table.adults = self.adult_row.value
				self.current_customer.table.students = self.student_row.value
				self.current_customer.table.description = self.description_row.input.text
				self.current_customer.table.clock_in = self.clock_row.clock_in_time
				self.current_customer.render()
				self.dismiss()

		def cancel_changes(self, event):
				self.dismiss()
	
if __name__ == "__main__":
	TableTrackingApp().run()
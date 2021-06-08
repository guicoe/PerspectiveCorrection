import ui
import io
import dialogs
from perspectivecorrection import *
from PIL import Image, ImageDraw
import numpy as np



class ImageFrame (ui.View):
	
	def __init__(self, file, work_area):
		
		self.image = Image.open(file)
		self.work_area = work_area
		self.original = ui.Image.named(file)
		w, h = self.original.size
		kh = 0.99 * (self.work_area.height - 40)/h
		kw = 0.99 * self.work_area.width/w
		self.scale = min(kh, kw)
		self.width = min(self.scale * w, w)
		self.height = min(self.scale * h, h)
		
		self.points = []
		self.lines = []
		self.horizontal_lines = []
		self.vertical_lines = []
		self.touchable = True
		
		
	def draw(self):
		if self.buttons[2].active:
			self.corrected.draw(0, 0, self.width, self.height)
		else:
			self.original.draw(0, 0, self.width, self.height)
		
		
	def touch_began(self, touch):
		if self.touchable:
			
			# Create new dot if image is touchable
			dot = Dot(2, 10)
			dot.center = touch.location
			self.points.append(dot)
			self.add_subview(dot)
			
			# Every couple of dots, create new line
			if len(self.points) % 2 == 0:
				line = Line(*self.points[-2:], self.width, self.height)
				line.touch_enabled = False
				self.lines.append(line)
				self.points[-2].line = line
				self.points[-2].start = True
				self.points[-1].line = line
				self.add_subview(line)
				if len(self.horizontal_lines) < 2:
					self.horizontal_lines.append(line)
				else:
					self.vertical_lines.append(line)
				
		
	def touch_moved(self, touch):
		
		# This allows us to drag a point around while we place it
		# If the newly added point creates a line, this should also drag the line
		if self.touchable:
			self.points[-1].center = touch.location
			if len(self.points) % 2 == 0:
				self.lines[-1].p2 = touch.location
				self.lines[-1].set_needs_display()
				
	
	def touch_ended(self, touch):
		
		# This enables the button for submitting lines only when lines are ready to be submitted
		# Also disables input for more points until lines are submitted
		if len(self.points) == 4:
			self.buttons[1].border_color = "white"
			self.buttons[1].tint_color = "white"
			self.buttons[1].active = False
			self.buttons[1].touch_enabled = True
			
		elif len(self.points) == 8:
			self.buttons[2].border_color = "white"
			self.buttons[2].tint_color = "white"
			self.buttons[2].active = False
			self.buttons[2].touch_enabled = True
			self.touchable = False
			
			
		
class Dot (ui.View):
	
	def __init__(self, line_width, radius):
		
		# Makes sure the dot's own frame is wide enough to display the dot properly
		self.lw = line_width
		self.r = radius
		self.width = self.r + self.lw
		self.height = self.r + self.lw
		
		# We'll also want to keep track of which line the dot belongs to, if any
		# And whether it's the start or end of the line
		self.line = None
		self.start = False
		
		
	def draw(self):
		circle = ui.Path.oval(self.lw/2, self.lw/2, self.r, self.r)
		circle.line_width = self.lw
		ui.set_color("#007fff")
		circle.stroke()
		
		
	def touch_moved(self, touch):
		
		# This allows us to drag a dot which has already been placed along with its line
		self.center += touch.location
		if self.line:
			if self.start:
				self.line.p1 = self.center
			else:
				self.line.p2 = self.center
			self.line.set_needs_display()
			
			
					
class Line (ui.View):
	
	def __init__(self, p1, p2, w, h):
		
		# Initializes line segment connecting the centers of p1 and p2
		self.p1 = p1.center
		self.p2 = p2.center
		self.width = w
		self.height = h
		
		
	def draw(self):
		line = ui.Path()
		line.line_width = 2
		line.move_to(*self.p1)
		line.line_to(*self.p2)
		ui.set_color("#007fff")
		line.stroke()
		
		

class ButtonHandler (object):
	
	def switcher(self, sender):
		control = sender.control
		buttons = control.buttons
		for button in buttons:
			if button.active:
				button.touch_enabled = True
				button.active = False
				button.border_color = "white"
				button.tint_color = "white"
		sender.touch_enabled = False
		sender.active = True
		sender.border_color = "#007fff"
		sender.tint_color = "#007fff"
		if sender != buttons[2]:
			def animation():
				for line in control.horizontal_lines:
					line.alpha = 1 if buttons[0].active else 0.2
				for line in control.vertical_lines:
					line.alpha = 1 if buttons[1].active else 0.2
				for i in range(4):
					control.points[i].alpha = 1 if buttons[0].active else 0.2
					control.points[i].touch_enabled = buttons[0].active
				for i in range(4, len(control.points)):
					control.points[i].alpha = 1 if buttons[1].active else 0.2
					control.points[i].touch_enabled = buttons[1].active
			ui.animate(animation, duration = 0.2)
		else:
			for point in control.points:
				point.alpha = 0
				point.line.alpha = 0
				point.touch_enabled = False
				point.line.touch_enabled = False
			scale = control.scale
			horizontal_lines = [[tuple(1/scale*l.p1), tuple(1/scale*l.p2)] for l in control.horizontal_lines]
			vertical_lines = [[tuple(1/scale*l.p1), tuple(1/scale*l.p2)] for l in control.vertical_lines]
			image = control.image
			width, height = image.size
			sensor = np.array([[width/2, height/2, 0]])
			coeffs = find_persp_coeffs_from_lines(horizontal_lines, vertical_lines, sensor)
			corrected_image = image.transform((width, height), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
			control.corrected = pil2ui(corrected_image)
		sender.control.set_needs_display()
		
		
	def cancel(self, sender):
		sender.superview.superview.close()
		
			
	def pick_pic(self, sender):
		
		canvas = sender.superview
		
		# Launches Files and stores selected image into result
		result = dialogs.pick_document(types=["public.image"])
		
		if result:
			
			top_bar = ui.View()
			top_bar.width = canvas.width
			top_bar.height = 100
			top_bar.background_color = "#111111"
			canvas.add_subview(top_bar)
			
			bottom_bar = ui.View()
			bottom_bar.width = canvas.width
			bottom_bar.height = 50
			bottom_bar.y = canvas.height - bottom_bar.height
			bottom_bar.background_color = "#111111"
			canvas.add_subview(bottom_bar)
			
			work_area = ui.View()
			work_area.flex = "LRTB"
			work_area.width, work_area.height = canvas.width, canvas.height - top_bar.height - bottom_bar.height
			work_area.y = top_bar.height
			work_area.background_color = "#090909"
			work_area.alpha = 0
			canvas.add_subview(work_area)
			
			image = ImageFrame(result, work_area)
			image.center = (work_area.width/2, work_area.height/2)
			image.flex = "LRTB"
			work_area.add_subview(image)
			
			button_names = ["Horizontal", "Vertical", "Correct"]
			mid = [ui.Button(title = name) for name in button_names]
			for i in range(3):
				mid[i].width = 100
				mid[i].height = 30
				mid[i].corner_radius = 10
				mid[i].border_color = "#007fff" if i == 0 else "#666666"
				mid[i].border_width = 2
				mid[i].tint_color = "#007fff" if i == 0 else "#666666"
				mid[i].center = (canvas.width/2 + 120 * (i - 1), 75)
				mid[i].active = True if i == 0 else False
				mid[i].touch_enabled = False
				mid[i].action = self.switcher
				mid[i].control = image
				top_bar.add_subview(mid[i])
			image.buttons = mid
			
			def animation():
				work_area.alpha = 1
			ui.animate(animation, duration = .5)
			
			cancel = ui.Button(title = "Cancel")
			cancel.width = 70
			cancel.height = 30
			cancel.corner_radius = 10
			cancel.border_width = 2
			cancel.border_color = "#da7373"
			cancel.tint_color = "#da7373"
			cancel.center = (45, 75)
			cancel.action = self.cancel
			top_bar.add_subview(cancel)
			
			canvas.remove_subview(sender)
			
			
			
def pil2ui(imgIn):
	# found this little gem here:
	# https://forum.omz-software.com/topic/1935/how-can-i-convert-a-pil-image-to-a-ui-image/7
	with io.BytesIO() as bIO:
		imgIn.save(bIO, 'PNG')
		imgOut = ui.Image.from_data(bIO.getvalue())
	del bIO
	return imgOut

	
if __name__ == "__main__":
	
	canvas = ui.View()
	canvas.width, canvas.height = ui.get_screen_size()
	if ui.get_ui_style() == "dark":
		canvas.background_color = "#111111"
	
	button_handler = ButtonHandler()
	file_button = ui.Button()
	file_button.width = 200
	file_button.height = 50
	file_button.corner_radius = 10
	file_button.flex = "LRTB"
	file_button.border_color = "white"
	file_button.border_width = 3
	file_button.font = ("<system>", 17.0)
	file_button.title = "Choose File"
	file_button.tint_color = "white"
	file_button.center = canvas.center
	file_button.action = button_handler.pick_pic
	
	canvas.add_subview(file_button)
	canvas.present('fullscreen', hide_title_bar = True)

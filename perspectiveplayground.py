# Throughout, the positive x-axis points right, positive y-axis points down, and positive z-axis points towards user

import ui
import math
import numpy as np
import dialogs
import clipboard
import console
from objc_util import ObjCInstance

class PerspectiveFrame (ui.View):
	
	def __init__(self, perspective_distance, target_distance, frame_width, frame_height, target_width, target_height):
		self.defaults = [target_distance, target_width, target_height, False]
		self.p_dist = perspective_distance
		self.width = frame_width
		self.height = frame_height
		self.sensor = np.array((self.width/2, self.height/2, 0))
		
		self.t_dist = target_distance
		self.t_width = target_width 
		self.t_height = target_height
		self.t_center = np.array((self.width/2, self.height/2, -self.t_dist))
		self.t_basis = [np.array([[0, 0, 1]]).T, np.array([[1, 0, 0]]).T, np.array([[0, 1, 0]]).T]
		
		self.t_coords = self.find_target_coords()
		self.t_points = self.find_target_points(self.t_coords)
		self.p_points = self.find_perspective_points(self.t_points)
		self.draw_grid = False

				
	def reset(self):
		self.t_dist, self.t_width, self.t_height, self.draw_grid = self.defaults
		self.t_center = np.array((self.width/2, self.height/2, -self.t_dist))
		self.t_basis = [np.array([[0, 0, 1]]).T, np.array([[1, 0, 0]]).T, np.array([[0, 1, 0]]).T]
		self.t_coords = self.find_target_coords()
		self.t_points = self.find_target_points(self.t_coords)
		self.p_points = self.find_perspective_points(self.t_points)
		self.set_needs_display()
		
		
	def find_target_coords(self):
		return [np.array((sgn_x * self.t_width/2, sgn_y * self.t_height/2)) for sgn_x, sgn_y in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
		
		
	def find_target_points(self, t_coords):
		A = np.hstack(self.t_basis[1:])
		return [np.dot(A, coords) + self.t_center for coords in t_coords]
		
	
	def find_perspective_points(self, t_points):
		return [project_to_plane(t_point, self.p_dist, self.sensor) for t_point in t_points]
		
	
	def draw(self):
		cell_size = 50
		tw_numpoints = int(self.t_width / cell_size)
		th_numpoints = int(self.t_height / cell_size)
		p0, p1, p2, p3 = [p[:2] for p in self.p_points]
		quad = ui.Path()
		quad.line_width = 2
		ui.set_color("black")
		quad.move_to(*p3)
		for p in [p0, p1, p2, p3]:
			quad.line_to(*p)
			quad.move_to(*p)
		if self.draw_grid:
			t0, t1, t2, t3 = self.t_coords
			for i in range(1, tw_numpoints):
				start_coords = t0 + 50 * i * np.array((1, 0))
				end_coords = t3 + 50 * i * np.array((1, 0))
				start_t_point, end_t_point = self.find_target_points([start_coords, end_coords])
				start, end = self.find_perspective_points([start_t_point, end_t_point])
				quad.move_to(*start[:2])
				quad.line_to(*end[:2])
			for i in range(1, th_numpoints):
				start_coords = t0 + 50 * i * np.array((0, 1))
				end_coords = t1 + 50 * i * np.array((0, 1))
				start_t_point, end_t_point = self.find_target_points([start_coords, end_coords])
				start, end = self.find_perspective_points([start_t_point, end_t_point])
				quad.move_to(*start[:2])
				quad.line_to(*end[:2])
		quad.stroke()
		
		
	def touch_began(self, touch):
		ui_touch = ObjCInstance(touch)
		if ui_touch.type() == 2: # touch type 2 corresponds to Apple Pencil
			azimuth_angle = ui_touch.azimuthAngleInView_(self) # Angle in radians from positive x-axis towards positive y-axis
			altitude_angle = ui_touch.altitudeAngle()          # Angle in radians from screen surface towards user
			nx = math.cos(altitude_angle) * math.cos(azimuth_angle)
			ny = math.cos(altitude_angle) * math.sin(azimuth_angle)
			nz = math.sin(altitude_angle)
			tilt = np.dot(np.array([[0, ny, nz]]), np.array([[0, -1, 0]]).T)
			labeled_sliders[3].slider.value = 0.5 * (tilt + 1)
			labeled_sliders[3].value_label.text = "{:.1f}".format(float(tilt))
			self.t_basis = GSBasis([np.array([[nx, ny, nz]]).T, np.array([[1, 0, 0]]).T, np.array([[0, 1, 0]]).T])
			self.t_center = project_to_plane(np.array((*touch.location, -self.p_dist)), self.t_dist, self.sensor)
			self.t_points = self.find_target_points(self.t_coords)
			self.p_points = self.find_perspective_points(self.t_points)
			self.set_needs_display()
		
		
	def touch_moved(self, touch):
		ui_touch = ObjCInstance(touch)
		if ui_touch.type() == 2: # touch type 2 corresponds to Apple Pencil
			azimuth_angle = ui_touch.azimuthAngleInView_(self) # Angle in radians from positive x-axis towards positive y-axis
			altitude_angle = ui_touch.altitudeAngle()          # Angle in radians from screen surface towards user
			nx = math.cos(altitude_angle) * math.cos(azimuth_angle)
			ny = math.cos(altitude_angle) * math.sin(azimuth_angle)
			nz = math.sin(altitude_angle)
			tilt = np.dot(np.array([[0, ny, nz]]), np.array([[0, -1, 0]]).T)
			labeled_sliders[3].slider.value = 0.5 * (tilt + 1)
			labeled_sliders[3].value_label.text = "{:.1f}".format(float(tilt))
			self.t_basis = GSBasis([np.array([[nx, ny, nz]]).T, np.array([[1, 0, 0]]).T, np.array([[0, 1, 0]]).T])
			self.t_center = project_to_plane(np.array((*touch.location, -self.p_dist)), self.t_dist, self.sensor)
			self.t_points = self.find_target_points(self.t_coords)
			self.p_points = self.find_perspective_points(self.t_points)
			self.set_needs_display()
			
			
			
class NormalPad (ui.View):
	
	def __init__(self, width, height, frame):
		self.width = width
		self.height = height
		self.corner_radius = self.width / 4
		self.control_frame = frame
		
		
	def touch_began(self, touch):
		ui_touch = ObjCInstance(touch)
		if ui_touch.type() == 2: # touch type 2 corresponds to Apple Pencil
			azimuth_angle = ui_touch.azimuthAngleInView_(self) # Angle in radians from positive x-axis towards positive y-axis
			altitude_angle = ui_touch.altitudeAngle()          # Angle in radians from screen surface towards user
			nx = math.cos(altitude_angle) * math.cos(azimuth_angle)
			ny = math.cos(altitude_angle) * math.sin(azimuth_angle)
			nz = math.sin(altitude_angle)
			tilt = np.dot(np.array([[0, ny, nz]]), np.array([[0, -1, 0]]).T)
			labeled_sliders[3].slider.value = 0.5 * (tilt + 1)
			labeled_sliders[3].value_label.text = "{:.1f}".format(float(tilt))
			self.control_frame.t_basis = GSBasis([np.array([[nx, ny, nz]]).T, np.array([[1, 0, 0]]).T, np.array([[0, 1, 0]]).T])
			self.control_frame.t_points = self.control_frame.find_target_points(self.control_frame.t_coords)
			self.control_frame.p_points = self.control_frame.find_perspective_points(self.control_frame.t_points)
			self.control_frame.set_needs_display()
			
		
	def touch_moved(self, touch):
		ui_touch = ObjCInstance(touch)
		if ui_touch.type() == 2: # touch type 2 corresponds to Apple Pencil
			azimuth_angle = ui_touch.azimuthAngleInView_(self) # Angle in radians from positive x-axis towards positive y-axis
			altitude_angle = ui_touch.altitudeAngle()          # Angle in radians from screen surface towards user
			nx = math.cos(altitude_angle) * math.cos(azimuth_angle)
			ny = math.cos(altitude_angle) * math.sin(azimuth_angle)
			nz = math.sin(altitude_angle)
			tilt = np.dot(np.array([[0, ny, nz]]), np.array([[0, -1, 0]]).T)
			labeled_sliders[3].slider.value = 0.5 * (tilt + 1)
			labeled_sliders[3].value_label.text = "{:.1f}".format(float(tilt))
			self.control_frame.t_basis = GSBasis([np.array([[nx, ny, nz]]).T, np.array([[1, 0, 0]]).T, np.array([[0, 1, 0]]).T])
			self.control_frame.t_points = self.control_frame.find_target_points(self.control_frame.t_coords)
			self.control_frame.p_points = self.control_frame.find_perspective_points(self.control_frame.t_points)
			self.control_frame.set_needs_display()
			
			
			
class LabeledSlider (ui.View):
	
	def __init__(self, width, height, min, max, default, label, action, doubool):
		self.default = default
		self.width = width
		self.height = height
		self.min = min
		self.max = max
		self.label = label
		self.doubool = doubool
		
		slider_label = ui.Label()
		slider_label.width = self.width
		slider_label.height = 30
		slider_label.text = self.label
		slider_label.text_color = "white"
		self.add_subview(slider_label)
		
		self.value_label = ui.Label()
		self.value_label.width = self.width
		self.value_label.height = 30
		self.value_label.alignment = ui.ALIGN_RIGHT
		self.value_label.text = "{:.1f}".format(2 ** self.doubool * (self.default * (self.max - self.min) + self.min))
		self.value_label.text_color = "white"
		self.add_subview(self.value_label)
		
		self.slider = ui.Slider()
		self.slider.width = self.width
		self.slider.y = slider_label.height
		self.slider.value = self.default
		self.slider.continuous = True
		self.slider.action = action
		self.add_subview(self.slider)
		
	
	def reset(self):
		self.value_label.text = "{:.1f}".format(2 ** self.doubool * (self.default * (self.max - self.min) + self.min))
		self.slider.value = self.default
		self.set_needs_display()
		

		
class SliderHandler (object):
	
	def __init__(self, frame):
		self.frame = frame
		
	
	def td(self, sender):
		context = sender.superview
		value = sender.value
		d = context.doubool
		m, M = context.min, context.max
		self.frame.t_dist = (M - m) * value + m
		self.frame.t_center[2] = -self.frame.t_dist
		self.frame.t_points = self.frame.find_target_points(self.frame.t_coords)
		self.frame.p_points = self.frame.find_perspective_points(self.frame.t_points)
		self.frame.set_needs_display()
		context.value_label.text = "{:.1f}".format(2 ** d * self.frame.t_dist)
		
		
	def tw(self, sender):
		context = sender.superview
		value = sender.value
		d = context.doubool
		m, M = context.min, context.max
		self.frame.t_width = (M - m) * value + m
		self.frame.t_coords = self.frame.find_target_coords()
		self.frame.t_points = self.frame.find_target_points(self.frame.t_coords)
		self.frame.p_points = self.frame.find_perspective_points(self.frame.t_points)
		self.frame.set_needs_display()
		context.value_label.text = "{:.1f}".format(2 ** d * self.frame.t_width)
		
		
	def th(self, sender):
		context = sender.superview
		value = sender.value
		d = context.doubool
		m, M = context.min, context.max
		self.frame.t_height = (M - m) * value + m
		self.frame.t_coords = self.frame.find_target_coords()
		self.frame.t_points = self.frame.find_target_points(self.frame.t_coords)
		self.frame.p_points = self.frame.find_perspective_points(self.frame.t_points)
		self.frame.set_needs_display()
		context.value_label.text = "{:.1f}".format(2 ** d * self.frame.t_height)
		
		
	def v_tilt(self, sender):
		context = sender.superview
		value = sender.value
		d = context.doubool
		m, M = context.min, context.max
		n = np.vstack((self.frame.t_basis[0][:2], np.array([[0]])))
		prev_tilt = math.acos(np.dot(n.T, np.array([[0, -1, 0]]).T))
		new_tilt = math.acos((M - m) * value + m)
		theta = new_tilt - prev_tilt
		R = np.array([[1, 0, 0], [0, math.cos(theta), math.sin(theta)], [0, -math.sin(theta), math.cos(theta)]])
		self.frame.t_basis = [np.dot(R, c) for c in self.frame.t_basis]
		self.frame.t_points = self.frame.find_target_points(self.frame.t_coords)
		self.frame.p_points = self.frame.find_perspective_points(self.frame.t_points)
		self.frame.set_needs_display()
		context.value_label.text = "{:.1f}".format((M - m) * value + m)
		
		
		
class ButtonHandler (object):
	
	def __init__(self, frame):
		self.frame = frame
		
		
	def close(self, sender):
		if console.alert("Closing", "Would you like to export this image before closing?", "Yes", "No") == 1:
			self.export(None)
		self.frame.superview.superview.close()
		
		
	def export(self, sender):
		with ui.ImageContext(self.frame.width, self.frame.height) as ctx:
			bounds = ui.Path.rect(0, 0, self.frame.width, self.frame.height)
			ui.set_color(self.frame.background_color)
			bounds.fill()
			cell_size = 50
			tw_numpoints = int(self.frame.t_width / cell_size)
			th_numpoints = int(self.frame.t_height / cell_size)
			p0, p1, p2, p3 = [p[:2] for p in self.frame.p_points]
			quad = ui.Path()
			quad.line_width = 2
			ui.set_color("black")
			quad.move_to(*p3)
			for p in [p0, p1, p2, p3]:
				quad.line_to(*p)
				quad.move_to(*p)
			if self.frame.draw_grid:
				t0, t1, t2, t3 = self.frame.t_coords
				for i in range(1, tw_numpoints):
					start_coords = t0 + 50 * i * np.array((1, 0))
					end_coords = t3 + 50 * i * np.array((1, 0))
					start_t_point, end_t_point = self.frame.find_target_points([start_coords, end_coords])
					start, end = self.frame.find_perspective_points([start_t_point, end_t_point])
					quad.move_to(*start[:2])
					quad.line_to(*end[:2])
				for i in range(1, th_numpoints):
					start_coords = t0 + 50 * i * np.array((0, 1))
					end_coords = t1 + 50 * i * np.array((0, 1))
					start_t_point, end_t_point = self.frame.find_target_points([start_coords, end_coords])
					start, end = self.frame.find_perspective_points([start_t_point, end_t_point])
					quad.move_to(*start[:2])
					quad.line_to(*end[:2])
			quad.stroke()
			img = ctx.get_image()
		img.show()
		message = "Image dimensions:\n    {} by {}\n\nObject dimensions:\n    {} by {}\n\nPoints:\n    [{}, {}, {}, {}]"
		clipboard.set(message.format(math.ceil(2*frame.width), math.ceil(2*frame.height), math.ceil(2*frame.t_width), 		math.ceil(2*frame.t_height), *[[int(round(2*p[0])), int(round(2*p[1]))] for p in frame.p_points]))
		dialogs.share_image(img)
		frame.superview.superview.close()
		
		with open('test.png', 'wb') as out_file:
			out_file.write(img.to_png())
		
		print("\n\nImage dimensions:\n    {} by {}\n".format(math.ceil(2*frame.width), math.ceil(2*frame.height)))
		print("Object dimensions:\n    {} by {}\n".format(math.ceil(2*frame.t_width), math.ceil(2*frame.t_height)))
		print("Points:\n    [{}, {}, {}, {}]".format(*[[int(round(2*p[0])), int(round(2*p[1]))] for p in frame.p_points]))
		
		
	def reset(self, sender):
		frame.reset()
		grid_toggle.value = False
		for i in range(len(labeled_sliders)):
			labeled_sliders[i].reset()
			
			
			
class SwitchHandler (object):
	
	def __init__(self, frame):
		self.frame = frame
		
		
	def toggle(self, sender):
		self.frame.draw_grid = sender.value
		self.frame.set_needs_display()
		
		

def project_to_plane(pt, z_dist, sensor):
	
	'''
	Project point onto a plane which is orthogonal to line of sight.
	
	Input: 
		pt (1x3 numpy array), coordinates of point to be projected.
		z_dist (float), position of new plane relative to sensor.
		sensor (1x3 numpy array), xyz-coordinates of sensor.
	Output:
		(1x3 numpy array) xyz-coordinates of pt projected onto new plane.
	'''
	
	# Force sensor to be (0, 0, 0), project, then translate back
	x, y, z = pt - sensor
	return np.array((-z_dist*x/z, -z_dist*y/z, -z_dist)) + sensor
	
	
def GSBasis(basis: list) -> list:
	
	'''
	Applies the Gram-Schmidt orthogonalization process to the basis b1, b2, and b3, in place.
	
	Input:
		basis (list of 1-by-n numpy arrays), the original basis.
	Output:
		basis (list of 1-by-n numpy arrays), the resulting orthonormal basis.
	'''
	
	n = len(basis)
	for i in range(1, n):
		for j in range(i):
			basis[i] = basis[i] - np.dot(basis[i].T, basis[j]) * basis[j]
		basis[i] /= np.linalg.norm(basis[i])
	
	return basis
	

	
if __name__ == "__main__":
	
	screen_width, screen_height = ui.get_screen_size()
	canvas = ui.View(frame = (0, 0, screen_width, screen_height))
	canvas.background_color = "#222222"
	
	left_column = ui.View(name = "left")
	left_column.width = screen_width/3
	left_column.height = screen_height
	left_column.background_color = "#333333"
	
	right_column = ui.View(name = "right")
	right_column.width = screen_width - left_column.width
	right_column.height = screen_height
	right_column.x = left_column.width
		
	canvas.add_subview(left_column)
	canvas.add_subview(right_column)
	
	max_distance = 30000
	frame = PerspectiveFrame(870, 870, 0.9 * right_column.width, 0.9 * right_column.height, 600, 400)
	frame.name = "frame"
	frame.background_color = "white"
	frame.center = (right_column.width/2, right_column.height/2)
	
	right_column.add_subview(frame)
	
	container = ui.View()
	container.width = 0.7 * left_column.width
	container.height = frame.height
	container.center = left_column.center
	
	left_column.add_subview(container)
	
	slider_handler = SliderHandler(frame)
	actions = [slider_handler.td, slider_handler.tw, slider_handler.th, slider_handler.v_tilt]
	labels = ["Target Distance", "Object Width", "Object Height", "Vertical Tilt"]
	ranges = [(1, max_distance), (0, frame.width), (0, frame.height), (-0.999, 0.999)]
	defaults = [(frame.defaults[0] - 1)/(max_distance - 1), 600/frame.width, 400/frame.height, 0.5] # Make this better
	double_display = [1, 1, 1, 0]
	labeled_sliders = []
	for i in range(4):
		labeled_slider = LabeledSlider(container.width, 70, *ranges[i], defaults[i], labels[i], actions[i], double_display[i])
		labeled_slider.y = 100 * (i + 1)
		container.add_subview(labeled_slider)
		labeled_sliders.append(labeled_slider)
		
	npad = NormalPad(100, 100, frame)
	npad.center = (container.width/2, labeled_sliders[-1].y + labeled_sliders[-1].height + 120)
	npad.background_color = "#555555"
	npad.border_color = "#666666"
	npad.border_width = 2
	
	container.add_subview(npad)
	
	grid_handler = SwitchHandler(frame)
	grid_toggle = ui.Switch()
	grid_toggle.y = npad.y + npad.height + 80
	grid_toggle.action = grid_handler.toggle
	grid_label = ui.Label(frame = (grid_toggle.width + 20, grid_toggle.y, 80, 30))
	grid_label.text_color = "white"
	grid_label.text = "Grid"
	container.add_subview(grid_toggle)
	container.add_subview(grid_label)
	
	button_handler = ButtonHandler(frame)
	close_button = ui.Button(title = "Close")
	close_button.font = ("<system-bold>", 17.0)
	close_button.width = 55
	close_button.action = button_handler.close
	container.add_subview(close_button)
	
	export_button = ui.Button(title = "Export")
	export_button.font = ("<system-bold>", 17.0)
	export_button.x = 80
	export_button.width = 55
	export_button.action = button_handler.export
	container.add_subview(export_button)
	
	reset_button = ui.Button(title = "Reset")
	reset_button.font = ("<system-bold>", 17.0)
	reset_button.width = 50
	reset_button.x = 160
	reset_button.action = button_handler.reset
	container.add_subview(reset_button)
			
	canvas.present('fullscreen', hide_title_bar = True)

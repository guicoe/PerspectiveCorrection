from PIL import Image, ImageDraw
import numpy as np


# User identifies a pair of horizontal line segments and a pair of vertical line segments.

# Extend line segments until they form a quadrilateral.

# Find intersection for each pair of lines in projective space.

# Detect position of focal plane.

# Find vector normal to target plane.

# Project vertices of quadrilateral in focal plane onto target plane.

# Rotate target plane so that it's orthogonal to the line of sight.

# Project vertices of quadrilateral (should be a rectangle) in target plane to focal plane.

# Use old points along with new points to warp the perspective of the image accordingly.

# Allow user to constrain crop the output and export the corrected image.


def intersect(l1, l2):
	
	'''
	
	Finds the intersection of the two lines l1 and l2.
	
	Input:
		
		l1 = [(x11, y11), (x12, y12)], list of two points on l1.
		l2 = [(x21, y21), (x22, y22)], list of two points on l2.
		
	Output:
		
		(x, y), point of intersection.
		
	'''
	
	p1, q1 = [np.array([*p, 1]) for p in l1]
	p2, q2 = [np.array([*p, 1]) for p in l2]
	
	n1, n2 = np.cross(p1, q1), np.cross(p2, q2)
	x, y, z = np.cross(n1, n2)
	
	## Assume for now that z cannot equal 0
	
	return (x/z, y/z)
	
	
def get_focal_distance(p1, p2, sensor):
	
	'''
	
	Given two points p1 and p2 on a focal plane at an unknown distance corresponding to
	vanishing points of perpendicular lines, this function finds the correct focal distance.
	
	Input:
		
		p1 = (x1, y1), point on focal plane.
		p2 = (x2, y2), point on focal plane.
		sensor = (x, y), xy-coordinates of sensor.
		
	Output:
		
		d, focal distance
		
	'''
	
	x1, y1 = p1 - sensor
	x2, y2 = p2 - sensor
	
	return np.sqrt(- x1 * x2 - y1 * y2)
	
	
def project_to_plane(points, sensor, n, t):
	
	'''
	
	Project list of points onto plane normal to n passing through t.
	
	Input:
		
		points = [p1, p2, ...], list of points to be projected.
		sensor = (x, y, z), coordinates of sensor.
		n = np.array([[nx, ny, nz]]), normal vector defining plane.
		t = np.array([[tx, ty, tz]]), point on plane.
		
	Output:
		
		p_points = [new_p1, new_p2, ...], list of projected points.
		
	'''
	
	p_points = []
	
	for point in points:
		p = point - sensor
		c = np.dot(n, t.T) / np.dot(n, p.T)
		p_points.append(c * p + sensor)
		
	return p_points
	
	
def find_perspective_coeffs(pa, pb):
	# taken from here:
	# https://stackoverflow.com/questions/14177744/how-does-perspective-transformation-work-in-pil
	matrix = []
	for p1, p2 in zip(pa, pb):
		matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
		matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

	A = np.matrix(matrix, dtype=np.float)
	B = np.array(pb).reshape(8)

	res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
	return np.array(res).reshape(8)
	
	
def find_persp_coeffs_from_lines(horizontal_lines, vertical_lines, sensor):
	
	'''
	
	Given lines which should be horizontal and lines which should be vertical
	in an image, along with the position of a sensor in 3-space, this function
	finds the perspective coefficients needed to warp the perspective so that
	the lines become truly horizontal and vertical.
	
	Input:
		
		horizontal_lines = [[(xh11, yh11), (xh12, yh12)], [(xh21, yh21), (xh22, yh22)]],
			a pair of user-identified horizontal lines, each given by a list of two points.
		vertical_lines = [[(xv11, yv11), (xv12, yv12)], [(xv21, yv21), (xv22, yv22)]],
			a pair of user-identified vertical lines, each given by a list of two points.
		sensor = np.array([[x, y, z]]), the location of the sensor.
		
	Output:
		
		coeffs = np.array([c0, ..., c7]), the required perspective coefficients.
		
	'''
	
	# Get quadrilateral vertices by intersecting horizontal lines with vertical lines
	quad = [intersect(hl, vl) for hl in horizontal_lines for vl in vertical_lines]
	
	# Find intersection of "horizontal" lines and intersection of "vertical" lines
	h_int, v_int = intersect(quad[:2], quad[2:4]), intersect(quad[0:4:2], quad[1:5:2])
	
	## Assume for now that these intersections both exist.
	## If they both don't exist, we just need to rotate the image.
	## If one exists but the other doesn't, focal distance might not be computable.
	
	# Detect focal distance using intersections
	focal_distance = get_focal_distance(np.array(h_int), np.array(v_int), sensor[0][:2])
	
	# Find vector normal to target plane
	h_direction = np.array([[*h_int, focal_distance]]) - sensor
	v_direction = np.array([[*v_int, focal_distance]]) - sensor
	target_normal = np.cross(h_direction, v_direction)
	sgn = target_normal[0][2]/abs(target_normal[0][2])
	target_normal /= np.linalg.norm(target_normal) * sgn
	
	# Project quad onto target plane (which should result in a rectangle on target)
	target_shift = np.array([[0, 0, focal_distance]])
	quad = [np.array([[*v, focal_distance]]) for v in quad]
	target_rect = project_to_plane(quad, sensor, target_normal, target_shift)
	
	# Rotate target plane so normal points forward and rectangle aligns with axes
	h_axis = (target_rect[1] - target_rect[0]) / np.linalg.norm(target_rect[1] - target_rect[0])
	R = np.vstack((h_axis, np.cross(target_normal, h_axis), target_normal))
	rotate_rect = [(np.dot(R, point.T - target_shift.T) + target_shift.T).T for point in target_rect]
	
	# Project rotate_rect back to focal plane to get corrected quad
	rect = project_to_plane(rotate_rect, sensor, np.array([[0, 0, 1]]), target_shift)
	
	# Center rect at sensor for now (we probably don't want this in the end)
	rect = [v[0][:2] for v in rect]
	rect_center = rect[0] + np.array(((rect[1][0] - rect[0][0])/2, (rect[2][1] - rect[0][1])/2))
	centered_rect = [v - rect_center + sensor[0][:2] for v in rect]
	
	# Find perspective coefficients mapping quad to rect
	quad = [v[0][:2] for v in quad]
	coeffs = find_perspective_coeffs(centered_rect, quad)
	
	return coeffs


if __name__ == "__main__":
	
	file = "/test_images/test_bad.png"
	image = Image.open(file)
	width, height = image.size
	sensor = np.array([[width/2, height/2, 0]])
	
	# Express a line as a list containing two points on the line
	horizontal_lines = [[(552, 310), (1120, 1090)], [(386, 431), (1258, 1537)]]
	vertical_lines = [[(552, 310), (386, 431)], [(1120, 1090), (1258, 1537)]]
	
	# Run main function on extracted lines
	coeffs = find_persp_coeffs_from_lines(horizontal_lines, vertical_lines, sensor)
	
	# Warp original image to correct perspective
	corrected_image = image.transform((width, height), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
	
	image.show()
	corrected_image.show()
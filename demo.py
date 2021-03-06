import csv
from perspectivecorrection import *

sample = []
path = "./test_images/"
n = 0

## We need to handle the case when we don't find a file with the given name

with open(path + "samples.csv") as csvfile:
	reader = csv.reader(csvfile)
	header = next(reader)
	for row in reader:
		n += 1
		filename = row[0]
		lines = [[tuple(map(int, row[4*i+1:4*i+3])), tuple(map(int, row[4*i+3:4*i+5]))] for i in range(4)]
		sample.append([filename, lines])
		
for index in range(n):
	filename, lines = sample[index]
	image = Image.open(path + filename)
	width, height = image.size
	sensor = np.array([[width/2, height/2, 0]])
	
	# Express a line as a list containing two points on the line
	horizontal_lines = lines[:2]
	vertical_lines = lines[2:]
	
	# Run main function on extracted lines
	coeffs = find_persp_coeffs_from_lines(horizontal_lines, vertical_lines, sensor)
	
	# Warp original image to correct perspective
	corrected_image = image.transform((width, height), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
	
	print("horizontal_lines = " + str(horizontal_lines))
	print("vertical_lines = " + str(vertical_lines))
	draw_lines(image, lines, r = int(max(width, height)/300))
	image.show()
	corrected_image.show()

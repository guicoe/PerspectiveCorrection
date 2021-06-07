# PerspectiveCorrection

This is a projective geometry project aiming to correct perspective distortions in images after a user identifies pairs of horizontal and vertical lines.

## perspectiveplayground.py

Used for generating images with rectangles viewed from different perspectives. Some of the resulting test images can be found in test_images.

This is written using Pythonista 3 on a 2019 iPad Pro. It uses some of Pythonista's built-in modules, so you'll probably need to run it using Pythonista 3. You'll also need an Apple Pencil to tilt the plane. Future update will include sliders to tilt the plane horizontally and vertically without an Apple Pencil.

## perspectivecorrection.py

This is the main part of the project containing the functions needed to correct the perspective in an image. It still needs a UI where a user can choose the image to be corrected and identify pairs of "horizontal" and "vertical" lines.

## Process for Perspective Correction

* User identifies a pair of horizontal line segments and a pair of vertical line segments.
* Extend line segments until they form a quadrilateral.
* Find intersection for each pair of lines in projective space.
* Detect position of focal plane.
* Find vector normal to target plane.
* Project vertices of quadrilateral in focal plane onto target plane.
* Rotate target plane so that it's orthogonal to the line of sight.
* Project vertices of quadrilateral (should be a rectangle) in target plane to focal plane.
* Rotate if necessary so that the rectangle's sides are horizontal and vertical.
* Use old points along with new points to warp the perspective of the image accordingly.
* Allow user to constrain crop the output and export the corrected image.
#!/usr/bin/env ruby

$:.unshift __dir__ + "/.."
require 'numo/narray'
require 'cv2'

# Create 3 channels color (BGR) image buffer (width: 600, height: 400)
img = Numo::UInt8.zeros(400, 600, 3)
# draw a circle of radius: 100 at position (200, 200) with blue color
# (BGR: 255, 0, 0), thickness: 3 and antialiased
CV2::circle(img, [200, 200], 50, [255, 0, 0], thickness: 3, lineType: CV2::LINE_AA)
# Save the image to out.jpg
CV2::imwrite("out.jpg", img)

#!/usr/bin/env ruby

$:.unshift ".."

require 'cv2'

img = CV2::imread("input.jpg")
# draw a circle of radius: 100 at position (200, 200) with blue color
# (BGR: 255, 0, 0), thickness: 3 and antialiased
CV2::circle(img, [200, 200], 50, [255, 0, 0], thickness: 3, lineType: CV2::LINE_AA)
CV2::imwrite("out.jpg", img)

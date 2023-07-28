#!/usr/bin/env ruby

$unsupported_headers = [
  "opencv2/core/cuda.hpp",
  "opencv2/core/cuda.inl.hpp",
  "opencv2/core/cuda_types.hpp",
  #"opencv2/core/types.hpp",  # wrap_cv_Moments_init
  "opencv2/dnn/dnn.hpp",     # wrap_XXX_init
  "opencv2/dnn/dnn.inl.hpp",
  "opencv2/dnn/layer.hpp",
  "opencv2/dnn/utils/inference_engine.hpp",
  "opencv2/dnn/version.hpp",
  "opencv2/features2d.hpp",  # Compilable with note about "Class Feature2D has more than 1 base class"
  #"opencv2/ml.hpp",          # wrap_cv_ml_ParamGrid_init
  #"opencv2/ml/ml.inl.hpp",
  #"opencv2/stitching.hpp",   # wrap_cv_Stitcher_init
  "opencv2/stitching/detail/blenders.hpp",
  "opencv2/stitching/detail/camera.hpp",
  "opencv2/stitching/detail/exposure_compensate.hpp",
  "opencv2/stitching/detail/matchers.hpp",
  "opencv2/stitching/detail/motion_estimators.hpp",
  "opencv2/stitching/detail/seam_finders.hpp",
  "opencv2/stitching/detail/util.hpp",
  "opencv2/stitching/detail/util_inl.hpp",
  "opencv2/stitching/detail/warpers.hpp",
  "opencv2/stitching/detail/warpers_inl.hpp",
  "opencv2/stitching/warpers.hpp",
  "opencv2/video/tracking.hpp",  # wrap_cv_TrackerGOTURN_init wrap_cv_TrackerMIL_init
]

# Additional ignore list for Mac
unsupported_headers_mac = [
  "opencv2/objdetect/aruco_board.hpp", # wrap_cv_aruco_Board_init
  "opencv2/objdetect/charuco_detector.hpp", # wrap_cv_aruco_CharucoParameters_init
  "opencv2/objdetect.hpp", # crash
  "opencv2/objdetect/aruco_detector.hpp",
  "opencv2/objdetect/aruco_dictionary.hpp",
  "opencv2/objdetect/detection_based_tracker.hpp",
  "opencv2/objdetect/face.hpp",
]
if RUBY_PLATFORM.include?("darwin")
  $unsupported_headers += unsupported_headers_mac
end

def is_unsupported_header(header)
  $unsupported_headers.each{|us_hdr|
    return true if header.end_with?(us_hdr)
  }
  return false
end

# List all header files included from <opencv2/opencv.hpp>
lines = `echo "#include <opencv2/opencv.hpp>" | g++ -std=c++14 -xc++ -M \`pkg-config --cflags opencv4\` -`.split("\n")
tmp_headers = lines[0][3..-1].chomp(" \\").split() # [3..-1].chomp(" \\") is to strip "-: " and " \\"
lines[1..-1].each{|line|
  cols = line[1..-1].chomp(" \\").split()
  cols.each{|col| tmp_headers << col}
}

# Extract required headers
headers = ["./dummycv/dummycv.hpp"] # Classes/methods for test
tmp_headers.each{|header|
  next if !header.include?("opencv2") # remove non-opencv headers
  next if header.include?("/cuda.")
  header = File.expand_path(header) # convert paths with "." and ".."
  #next if is_unsupported_header(header)
  headers << header
}
headers.uniq! # remove duplicated headers
headers.sort!

headers.each{|header|
  puts header
}

require 'find'
require 'mkmf'
require 'numo/narray'

def find_opencv_include_dir(opencv4_cppflags)
  flags = opencv4_cppflags.split()
  flags.each{|flag|
    include_dir = flag.gsub(/^-I/, '')
    opencv_hpp_path = include_dir + "/opencv2/opencv.hpp"
    if FileTest.exist?(opencv_hpp_path)
      return include_dir
    end
  }
  raise "cannot find opencv.hpp in cflags"
end

def gen_headers_txt(opencv_include_dir)
  header_paths = []
  Find.find(opencv_include_dir){|path|
    next unless FileTest.file? path
    next unless path.end_with?(".hpp")
    next if path =~ /\/cuda\//
    next if path =~ /\/opencl\//
    next if path =~ /\/hal\// # Skip due to duplated definition error
    next if path =~ /tracking_legacy.hpp$/
    header_paths << path
  }
  File.open(__dir__ + "/headers.txt", "w"){|fout|
    header_paths.each{|path|
      if FileTest.exist?(path)
        fout.puts path
      end
    }
  }
end

$LOAD_PATH.each{|lp|
  if File.exists?(File.join(lp, 'numo/numo/narray.h'))
    $INCFLAGS = "-I#{lp}/numo #{$INCFLAGS}"
    break
  end
}

opencv4_libs = `pkg-config --libs-only-l opencv4`.chomp
opencv4_cppflags = `pkg-config --cflags-only-I opencv4`.chomp
found_opencv4 = $?.success?

if found_opencv4
  opencv_include_dir = find_opencv_include_dir(opencv4_cppflags)
  gen_headers_txt(opencv_include_dir)
  $libs = opencv4_libs
  $CPPFLAGS = opencv4_cppflags
  create_makefile('cv2')
end

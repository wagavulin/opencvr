require 'mkmf'

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
  header_relpaths = []
  File.open(__dir__ + "/headers-tmpl.txt"){|fin|
    while line = fin.gets
      line.chomp!
      next if line.start_with?('#')
      header_relpaths << line
    end
  }
  header_paths = header_relpaths.map{|relpath|
    opencv_include_dir + "/" + relpath
  }
  File.open(__dir__ + "/headers.txt", "w"){|fout|
    header_paths.each{|path|
      if FileTest.exist?(path)
        fout.puts path
      end
    }
  }
end

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

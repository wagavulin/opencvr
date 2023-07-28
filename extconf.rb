require 'mkmf'
require 'numo/narray'

$LOAD_PATH.each{|lp|
  if File.exists?(File.join(lp, 'numo/numo/narray.h'))
    $INCFLAGS = "-I#{lp}/numo #{$INCFLAGS}"
    break
  end
}

$CXXFLAGS += " -std=c++14 -Wno-deprecated-declarations "
opencv4_include_dir = `pkg-config --cflags-only-I opencv4`.chomp
opencv4_ldflags = `pkg-config --libs-only-L opencv4`.chomp # -L/path/to/opencv4/lib
$CPPFLAGS = opencv4_include_dir + " -I./dummycv"
$LDFLAGS = opencv4_ldflags
if !opencv4_ldflags.empty?
  opencv4_libdir = opencv4_ldflags[2..-1] # remove "-L"
  $LDFLAGS += " -Wl,-rpath,'#{opencv4_libdir}'"
end
$LDFLAGS += " -L./dummycv -Wl,-rpath,'$$ORIGIN/dummycv'"
opencv4_libs = `pkg-config --libs-only-l opencv4`.chomp
$libs = opencv4_libs + " -ldummycv"
create_makefile('cv2')

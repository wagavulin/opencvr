require 'mkmf'
require 'numo/narray'

$LOAD_PATH.each{|lp|
  if File.exists?(File.join(lp, 'numo/numo/narray.h'))
    $INCFLAGS = "-I#{lp}/numo #{$INCFLAGS}"
    break
  end
}

opencv4_include_dir = `pkg-config --cflags-only-I opencv4`.chomp
$CPPFLAGS = opencv4_include_dir + " -I./dummycv"
$LDFLAGS = "-L./dummycv -Wl,-rpath,'$$ORIGIN/dummycv'"
opencv4_libs = `pkg-config --libs-only-l opencv4`.chomp
$libs = opencv4_libs + " -ldummycv"
create_makefile('cv2')

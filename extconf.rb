require 'mkmf'
$CPPFLAGS = "-I./dummycv"
$LDFLAGS = "-L./dummycv -Wl,-rpath,'$$ORIGIN/dummycv'"
$libs = "-ldummycv"
create_makefile('cv2')

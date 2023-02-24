require 'mkmf'
$CPPFLAGS = "-I./dummycv"
$LDFLAGS = "-L./dummycv"
$libs = "-ldummycv"
create_makefile('cv2')

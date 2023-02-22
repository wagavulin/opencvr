require 'mkmf'
$CPPFLAGS = "-I./dummycv"
create_makefile('cv2')

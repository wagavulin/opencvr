require 'mkmf'

opencv4_libs = `pkg-config --libs-only-l opencv4`.chomp
found_opencv4 = $?.success?

if found_opencv4
    $libs = opencv4_libs
    create_makefile('cv2')
end

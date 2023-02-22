#include <ruby.h>

#define PRINT_FUNC() fprintf(stderr, "[%s]\n", __func__)
#define PRINT_CXXFUNC() fprintf(stderr, "[CXX %s]\n", __func__)

#include "autogen/rbopencv_include.hpp"
using namespace cv;
static VALUE mCV2;
#include "autogen/rbopencv_wrapclass.hpp"

extern "C" {
void Init_cv2(){
    PRINT_FUNC();
    mCV2 = rb_define_module("CV2");

    #include "autogen/rbopencv_classregistration.hpp"
}
}

#include "dummycv.hpp"

namespace cv {
int bindTest1(int a){
    PRINT_CXXFUNC();
    return a + 10;
}
}

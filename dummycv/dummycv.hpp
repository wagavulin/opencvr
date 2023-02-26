#ifndef DUMMYCV_HPP
#define DUMMYCV_HPP

#include <opencv2/core/types.hpp>
#include <cstdio>

#define PRINT_FUNC() fprintf(stderr, "[%s]\n", __func__)
#define PRINT_CXXFUNC() fprintf(stderr, "[CXX %s]\n", __func__)

// Copied from opencv/modules/core/include/opencv2/core/cvdef.h
#ifndef CV_EXPORTS
# if (defined _WIN32 || defined WINCE || defined __CYGWIN__) && defined(CVAPI_EXPORTS)
#   define CV_EXPORTS __declspec(dllexport)
# elif defined __GNUC__ && __GNUC__ >= 4 && (defined(CVAPI_EXPORTS) || defined(__APPLE__))
#   define CV_EXPORTS __attribute__ ((visibility ("default")))
# endif
#endif

#ifndef CV_EXPORTS
# define CV_EXPORTS
#endif

#define CV_EXPORTS_W CV_EXPORTS
#define CV_EXPORTS_W_SIMPLE CV_EXPORTS
#define CV_EXPORTS_AS(synonym) CV_EXPORTS
#define CV_EXPORTS_W_MAP CV_EXPORTS
#define CV_IN_OUT
#define CV_OUT
#define CV_PROP
#define CV_PROP_RW
#define CV_WRAP
#define CV_WRAP_AS(synonym)
#define CV_WRAP_MAPPABLE(mappable)
#define CV_WRAP_PHANTOM(phantom_header)
#define CV_WRAP_DEFAULT(val)
// End copied

namespace cv {

// global functions for test arguments and retval
CV_EXPORTS_W int bindTest1(int a) { return a+a; } // Simple function
// CV_EXPORTS_W double bindTest1(int a, CV_IN_OUT Point& b, CV_OUT int* c, int d=10, RNG* rng=0, double e=1.2);
CV_EXPORTS_W void bindTest2(int a) { int tmp = a + 10; if (tmp) {} } // retval: void
CV_EXPORTS_W int bindTest3(int a) { return a + a; }
CV_EXPORTS_W void bindTest4(int a, CV_IN_OUT Point& pt) { pt.x += a; pt.y -= a; }
// CV_EXPORTS_W void bindTest5(int a, CV_IN_OUT Point& pt, CV_OUT int* x);
// CV_EXPORTS_W bool bindTest6(int a, CV_IN_OUT Point& pt, CV_OUT int* x);

// CV_EXPORTS_W double bindTest_overload(Point a, Point b, double c);
// CV_EXPORTS_W double bindTest_overload(RotatedRect a);

CV_EXPORTS_W void bindTest_Out_Point(int a, CV_OUT Point& pt) { pt.x=a+10; pt.y=a-10; }
// CV_EXPORTS_W void bindTest_InOut_Mat(CV_IN_OUT Mat& a);
// CV_EXPORTS_W void bindTest_InOut_bool(CV_IN_OUT bool& a);
// CV_EXPORTS_W void bindTest_InOut_uchar(CV_IN_OUT uchar& a);
// CV_EXPORTS_W void bindTest_InOut_int(CV_IN_OUT int& a);
// CV_EXPORTS_W void bindTest_Out_intp(CV_OUT int* a);
// CV_EXPORTS_W void bindTest_InOut_size_t(CV_IN_OUT size_t& a);
// CV_EXPORTS_W void bindTest_InOut_float(CV_IN_OUT float& a);
// CV_EXPORTS_W void bindTest_InOut_double(CV_IN_OUT double& a);
// CV_EXPORTS_W void bindTest_InOut_Size(CV_IN_OUT Size& a);
// CV_EXPORTS_W void bindTest_InOut_Size2f(CV_IN_OUT Size2f& a);
// CV_EXPORTS_W void bindTest_InOut_Point(CV_IN_OUT Point& a);
// CV_EXPORTS_W void bindTest_InOut_Point2f(CV_IN_OUT Point2f& a);
// CV_EXPORTS_W void bindTest_InOut_RotatedRect(CV_IN_OUT RotatedRect& a);
// CV_EXPORTS_W void bindTest_InOut_vector_Point(CV_IN_OUT std::vector<Point>& a);

// enum
enum MyEnum1 {
    MYENUM1_UNCHANGED = -1,
    MYENUM1_GRAYSACLE =  0,
    MYENUM1_COLOR     =  1,
    MYENUM1_IGNORE_ORIENTATION = 128,
};

class CV_EXPORTS_W Foo {
public:
    CV_WRAP static int smethod1(int a) { return a + 10; }
    CV_WRAP Foo() { PRINT_CXXFUNC(); }
    CV_WRAP Foo(int value1) : m_value1(value1) { PRINT_CXXFUNC(); }
    ~Foo() { PRINT_CXXFUNC(); }
    CV_WRAP int method1(int a) {
        int ret = m_value1 + a;
        printf("[CXX %s] %d\n", __func__, ret);
        return ret;
    }
    CV_WRAP int method2(int a) { return m_value1 + a + 1; }
    CV_WRAP int method2(int a, int b) { return m_value1 + a + b; }
    int m_value1{123};
};

// class CV_EXPORTS_W Algorithm {
// public:
//     Algorithm();
//     virtual ~Algorithm();
//     CV_WRAP virtual void clear() {}
// };

// class CV_EXPORTS_W BackgroundSubtractor : public Algorithm {
// public:
//     CV_WRAP virtual void apply() = 0;
// };
namespace Ns1 {
enum MyEnum2 { // old style enum
    MYENUM2_VALUE_A = -1,
    MYENUM2_VALUE_B =  0,
    MYENUM2_VALUE_C = 10,
};
enum class MyEnum3 { // enum class
    MYENUM3_VALUE_P = 100,
    MYENUM3_VALUE_Q = 110,
    MYENUM3_VALUE_R = 120,
};
class CV_EXPORTS_W Bar {
public:
    CV_WRAP Bar() {}
    CV_WRAP int method1(int a) { return a+10; }
};
namespace Ns11 { // sub-sub-namespace
CV_EXPORTS_W int bindTest_Ns11(int a) { return a + 11; } // global function in sub-sub-namespace
enum MyEnum4 {
    MYENUM4_VALUE_1 = 1000,
    MYENUM4_VALUE_2 = 1100,
};
class CV_EXPORTS_W SubSubC1 {
public:
    CV_WRAP SubSubC1() {}
    CV_WRAP SubSubC1(int v1) : m_value1(v1) {}
    CV_WRAP int method1(int a) { return a + m_value1; }
    int m_value1{111};
};
} // namespace Ns11
} // namespace Ns1
} // namespace cv

#endif

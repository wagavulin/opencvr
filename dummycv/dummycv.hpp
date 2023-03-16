#ifndef DUMMYCV_HPP
#define DUMMYCV_HPP

#include <opencv2/core/types.hpp>
#include <cstdio>

#if TRACE
#define PRINT_FUNC() fprintf(stderr, "[%s]\n", __func__)
#define PRINT_CXXFUNC() fprintf(stderr, "[CXX %s]\n", __func__)
#else
#define PRINT_FUNC()
#define PRINT_CXXFUNC()
#endif

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

CV_EXPORTS_W double bindTest_double(double a) { return a + 0.5; }

CV_EXPORTS_W double bindTest_overload(double a) { return a * 2.0; }
CV_EXPORTS_W double bindTest_overload(Point pt) { return pt.x * 2.0 + pt.y * 2.0; }
CV_EXPORTS_W double bindTest_overload(double a, double b) { return a * b; }
// CV_EXPORTS_W double bindTest_overload(Point a, Point b, double c);
// CV_EXPORTS_W double bindTest_overload(RotatedRect a);

// Overloaded functions with CV_EXPORTS and CV_EXPORTS_W (cv::clipLine uses this style).
// Only the last one is supported even in python-binding
// CV_EXPORTS   int bindTest_overload2(int a) { return a + 1; }
// CV_EXPORTS_W int bindTest_overload2(int a, int b) { return a + b; }

CV_EXPORTS_W void bindTest_Out_Point(int a, CV_OUT Point& pt) { pt.x=a+10; pt.y=a-10; }
CV_EXPORTS_W void bindTest_Out_Pointp(int a, CV_OUT Point* pt) { pt->x=a+11; pt->y=a-11; }
// CV_EXPORTS_W void bindTest_InOut_Mat(CV_IN_OUT Mat& a);
CV_EXPORTS_W void bindTest_InOut_bool(CV_IN_OUT bool& a) { a = !a; }
// CV_EXPORTS_W void bindTest_InOut_uchar(CV_IN_OUT uchar& a);
// CV_EXPORTS_W void bindTest_InOut_int(CV_IN_OUT int& a);
CV_EXPORTS_W void bindTest_Out_intp(CV_OUT int* a) { *a = 10; }
CV_EXPORTS_W void bindTest_InOut_size_t(CV_IN_OUT size_t& a) { a += 10; }
CV_EXPORTS_W void bindTest_InOut_float(CV_IN_OUT float& a) { a += 0.5; }
CV_EXPORTS_W void bindTest_InOut_double(CV_IN_OUT double& a) { a += 1.5; }
CV_EXPORTS_W void bindTest_Out_doublep(CV_OUT double* a) { *a = 2.5; }
CV_EXPORTS_W int bindTest_In_String(const cv::String& s) { return s.length(); }
CV_EXPORTS_W void bindTest_InOut_Scalar(CV_IN_OUT Scalar& a) { a[0] += 1; a[1] += 2; a[2] += 3; a[3] += 4; }
CV_EXPORTS_W void bindTest_InOut_Size(CV_IN_OUT Size& a) { a.width += 10; a.height += 10; }
CV_EXPORTS_W void bindTest_InOut_Size2i(CV_IN_OUT Size2i& a) { a.width += 20; a.height += 20; }
// CV_EXPORTS_W void bindTest_InOut_Size2l(CV_IN_OUT Size2i& a) { a.width += 30; a.height += 30; }
CV_EXPORTS_W void bindTest_InOut_Size2f(CV_IN_OUT Size2f& a) { a.width += 0.5; a.height += 0.5; }
CV_EXPORTS_W void bindTest_InOut_Point(CV_IN_OUT Point& a) { a.x+=10; a.y+=10; }
CV_EXPORTS_W void bindTest_InOut_Pointpdv(CV_OUT Point* pt = 0) { if (pt) { pt->x = 10; pt->y = 20; }} // Point pointer with default value
CV_EXPORTS_W void bindTest_InOut_Point2f(CV_IN_OUT Point2f& a) { a.x += 0.5; a.y += 0.5; }
CV_EXPORTS_W void bindTest_InOut_Rect(CV_IN_OUT Rect& r) { r.x += 10; r.y += 20; r.width += 30; r.height += 40; }
CV_EXPORTS_W void bindTest_Out_Rectp(CV_OUT Rect* r = 0) { r->x = 10; r->y = 20; r->width = 30; r->height = 40; }
CV_EXPORTS_W void bindTest_InOut_RotatedRect(CV_IN_OUT RotatedRect& a) {
    a.center.x += 0.5;
    a.center.y += 0.5;
    a.size.width += 0.5;
    a.size.height += 0.5;
    a.angle += 0.5;
}
CV_EXPORTS_W void bindTest_InOut_vector_int(CV_IN_OUT std::vector<int>& xs) { for (auto& x : xs) { x += 3; } }
CV_EXPORTS_W void bindTest_InOut_vector_Point(CV_IN_OUT std::vector<Point>& a) {
    Point p1{10, 11}, p2{20, 21};
    for (Point& p : a) { p.x += 1; p.y += 1; }
    a.push_back(p1); a.push_back(p2);
}
CV_EXPORTS_W void bindTest_InOut_vector_Rect(CV_IN_OUT std::vector<Rect>& rects) {
    for (auto& rect : rects) { rect.x += 1; rect.y += 2; rect.width += 3; rect.height += 4; }
}

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
    CV_WRAP int method1(int a) { return m_value1 + a; }
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
    CV_WRAP static int smethod1(int a) { return a + 20; }
    CV_WRAP SubSubC1() {}
    CV_WRAP SubSubC1(int v1) : m_value1(v1) {}
    CV_WRAP int method1(int a) { return a + m_value1; }
    CV_WRAP int method1(int a, int b) { return a + b + m_value1; }
    int m_value1{111};
};
} // namespace Ns11
} // namespace Ns1
} // namespace cv

#endif

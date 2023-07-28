#ifndef DUMMYCV_HPP
#define DUMMYCV_HPP

#include <opencv2/core/types.hpp>
#include <cstdio>
#include <cstdlib>
#include <cstdarg>

static int dcv_trace_printf(const char *filename, int line, const char *fmt, ...){
    const char *s_env = getenv("RBOPENCV_TRACE");
    if (s_env && atoi(s_env)) {
        va_list ap;
        va_start(ap, fmt);
        int ret = 0;
        ret += printf("[%s %d] ", filename, line);
        ret += vprintf(fmt, ap);
        va_end(ap);
        return ret;
    }
    return 0;
}

#define DCV_TRACE_PRINTF(fmt, ...) dcv_trace_printf(__FILE__, __LINE__, fmt, ##__VA_ARGS__)

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

namespace enumtest1 {
    enum E1 { AAA };       // CV2::Enumtest1::AAA
    enum { BBB };          // CV2::Enumtest1::BBB
    class CV_EXPORTS_W C1 {
    public:
        enum E2 { CCC };   // CV2::Enumtest1::C1_CCC
    };
    enum class E3 { DDD }; // CV2::Enumtest1::E3_DDD
}

namespace classtest1 {
class CV_EXPORTS_W C1 {
public:
    CV_WRAP C1() {}
    CV_WRAP C1(int value1) : m_value1(value1) {}
    CV_WRAP int method1(int a) { return m_value1 + a; }
    int m_value1{1};
};
CV_EXPORTS_W C1 bindTestClassInstance1(C1 c){ c.m_value1 = 1000; return c; }
} // classtest1

// global functions for test arguments and retval
CV_EXPORTS_W int bindTest1(int a) { return a+a; } // Simple function
// CV_EXPORTS_W double bindTest1(int a, CV_IN_OUT Point& b, CV_OUT int* c, int d=10, RNG* rng=0, double e=1.2);
CV_EXPORTS_W void bindTest2(int a) { int tmp = a + 10; if (tmp) {} } // retval: void
CV_EXPORTS_W int bindTest3(int a) { return a + a; }
CV_EXPORTS_W void bindTest4(int a, CV_IN_OUT Point& pt) { pt.x += a; pt.y -= a; }
// CV_EXPORTS_W void bindTest5(int a, CV_IN_OUT Point& pt, CV_OUT int* x);
// CV_EXPORTS_W bool bindTest6(int a, CV_IN_OUT Point& pt, CV_OUT int* x);
CV_EXPORTS_W int bindTest7(int a, int b=2, int c=3) { return (a + b) * c; }

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
CV_EXPORTS_W void bindTest_InOut_Mat(CV_IN_OUT Mat&) {}
CV_EXPORTS_W void bindTest_InOut_cvMat(CV_IN_OUT cv::Mat&) {}
CV_EXPORTS_W void bindTest_InOut_bool(CV_IN_OUT bool& a) { a = !a; }
CV_EXPORTS_W void bindTest_InOut_int(CV_IN_OUT int& a) { a += 10; }
CV_EXPORTS_W void bindTest_InOut_char(CV_IN_OUT char& a) { a += 20; };
CV_EXPORTS_W void bindTest_InOut_uchar(CV_IN_OUT uchar& a) { a += 30; };
CV_EXPORTS_W void bindTest_Out_intp(CV_OUT int* a) { *a = 10; }
CV_EXPORTS_W void bindTest_InOut_size_t(CV_IN_OUT size_t& a) { a += 10; }
CV_EXPORTS_W void bindTest_InOut_float(CV_IN_OUT float& a) { a += 0.5; }
CV_EXPORTS_W void bindTest_InOut_double(CV_IN_OUT double& a) { a += 1.5; }
CV_EXPORTS_W void bindTest_Out_doublep(CV_OUT double* a) { *a = 2.5; }
CV_EXPORTS_W int bindTest_In_String(const String& s) { return s.length(); }
CV_EXPORTS_W int bindTest_In_cvString(const cv::String& s) { return s.length(); }
CV_EXPORTS_W int bindTest_In_stdstring(const std::string& s) { return s.length(); }
CV_EXPORTS_W String bindTest_Out_String() { return "aa"; }
CV_EXPORTS_W cv::String bindTest_Out_cvString() { return "bb"; }
CV_EXPORTS_W std::string bindTest_Out_stdstring() { return "cc"; }
CV_EXPORTS_W String bindTest_InOut_String(const String& s) { return s + "x"; }
CV_EXPORTS_W int bindTest_In_cstring(const char* s) { return static_cast<int>(strlen(s)); }
CV_EXPORTS_W void bindTest_InOut_Scalar(CV_IN_OUT Scalar& a) { a[0] += 1; a[1] += 2; a[2] += 3; a[3] += 4; }
CV_EXPORTS_W void bindTest_InOut_Size(CV_IN_OUT Size& a) { a.width += 10; a.height += 10; }
CV_EXPORTS_W void bindTest_InOut_Size2i(CV_IN_OUT Size2i& a) { a.width += 20; a.height += 20; }
// CV_EXPORTS_W void bindTest_InOut_Size2l(CV_IN_OUT Size2i& a) { a.width += 30; a.height += 30; }
CV_EXPORTS_W void bindTest_InOut_Size2f(CV_IN_OUT Size2f& a) { a.width += 0.5; a.height += 0.5; }
CV_EXPORTS_W void bindTest_InOut_Point(CV_IN_OUT Point& a) { a.x+=10; a.y+=10; }
CV_EXPORTS_W void bindTest_InOut_Pointpdv(CV_OUT Point* pt = 0) { if (pt) { pt->x = 10; pt->y = 20; }} // Point pointer with default value
CV_EXPORTS_W void bindTest_InOut_Point2f(CV_IN_OUT Point2f& a) { a.x += 0.5; a.y += 0.5; }
CV_EXPORTS_W void bindTest_Out_Point2fp(CV_OUT Point2f* p) { p->x = 0.5; p->y = 1.5; }
CV_EXPORTS_W void bindTest_InOut_Point2d(CV_IN_OUT Point2d& a) { a.x += 1.5; a.y += 1.5; }
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
CV_EXPORTS_W void bindTest_InOut_vector_char(CV_IN_OUT std::vector<char>& xs) { for (auto& x : xs) { x += 4; } }
CV_EXPORTS_W void bindTest_InOut_vector_uchar(CV_IN_OUT std::vector<uchar>& xs) { for (auto& x : xs) { x += 5; } }
CV_EXPORTS_W void bindTest_InOut_vector_float(CV_IN_OUT std::vector<float>& xs) { for (auto& x : xs) { x += 0.5; } }
CV_EXPORTS_W void bindTest_InOut_vector_double(CV_IN_OUT std::vector<double>& xs) { for (auto& x : xs) { x += 1.5; } }
CV_EXPORTS_W void bindTest_InOut_vector_String(CV_IN_OUT std::vector<String>& ss) { for (auto& s : ss) { s += "x"; } }
CV_EXPORTS_W void bindTest_InOut_vector_cvString(CV_IN_OUT std::vector<cv::String>& ss) { for (auto& s : ss) { s += "y"; } }
CV_EXPORTS_W void bindTest_InOut_vector_stdstring(CV_IN_OUT std::vector<std::string>& ss) { for (auto& s : ss) { s += "z"; } }
CV_EXPORTS_W void bindTest_InOut_vector_Point(CV_IN_OUT std::vector<Point>& a) {
    Point p1{10, 11}, p2{20, 21};
    for (Point& p : a) { p.x += 1; p.y += 1; }
    a.push_back(p1); a.push_back(p2);
}
CV_EXPORTS_W void bindTest_InOut_vector_Point2f(CV_IN_OUT std::vector<Point2f>& a) {
    Point2f p1{10.5, 11.5}, p2{20.5, 21.5};
    for (Point2f& p : a) { p.x += 0.5; p.y += 0.5; }
    a.push_back(p1); a.push_back(p2);
}
CV_EXPORTS_W void bindTest_InOut_vector_Rect(CV_IN_OUT std::vector<Rect>& rects) {
    for (auto& rect : rects) { rect.x += 1; rect.y += 2; rect.width += 3; rect.height += 4; }
}
CV_EXPORTS_W void bindTest_InOut_vector_RotatedRect(CV_IN_OUT std::vector<RotatedRect>& rrects) {
    for (auto& rrect : rrects) {
        rrect.angle += 10;
        rrect.center.x += 1; rrect.center.y -= 1;
        rrect.size.width += 100; rrect.size.height -= 100;
    }
}
CV_EXPORTS_W void bindTest_InOut_vector_Size(CV_IN_OUT std::vector<Size>& sizes) {
    for (auto& size : sizes) { size.width += 100; size.height -= 100; }
}
CV_EXPORTS_W std::vector<Size> bindTest_InOut_vector_Size2(std::vector<Size>& sizes) {
    std::vector<Size> ret_sizes;
    for (const auto& size : sizes) {
        ret_sizes.push_back(Size{size.width + 100, size.height - 100});
    }
    return ret_sizes;
}
CV_EXPORTS_W void bindTest_InOut_vector_vector_int(CV_IN_OUT std::vector<std::vector<int>>& xss) {
    for (auto& xs : xss) { for (auto& x : xs) { x += 1; } }
}
CV_EXPORTS_W void bindTest_InOut_vector_vector_Point(CV_IN_OUT std::vector<std::vector<Point>>& pss) {
    for (auto& ps : pss) { for (auto& p : ps) { p.x += 1; p.y += 2; } }
}
CV_EXPORTS_W void bindTest_InOut_vector_vector_Point2f(CV_IN_OUT std::vector<std::vector<Point2f>>& pss) {
    for (auto& ps : pss) { for (auto& p : ps) { p.x += 1.5; p.y += 2.5; } }
}
CV_EXPORTS CV_WRAP_AS(wrapAsFunc1) int bindTest_WrapAsFunc(int a) { return a + 10; }
CV_EXPORTS CV_WRAP_AS(wrapAsFunc2) int bindTest_WrapAsFunc(std::string s) { return static_cast<int>(s.length()); }
CV_EXPORTS_AS(exportsAsFunc1) int bindTest_ExportsAsFunc(int a) { return a + 10; }
CV_EXPORTS_AS(exportsAsFunc2) int bindTest_ExportsAsFunc(std::string s) { return static_cast<int>(s.length()); }

// enum
enum MyEnum1 {
    MYENUM1_UNCHANGED = -1,
    MYENUM1_GRAYSCALE =  0,
    MYENUM1_COLOR     =  1,
    MYENUM1_IGNORE_ORIENTATION = 128,
};
CV_EXPORTS_W cv::MyEnum1 bindTest_OldEnum(MyEnum1 e) {
    if (e == MYENUM1_GRAYSCALE) { return MYENUM1_COLOR; }
    return MYENUM1_IGNORE_ORIENTATION;
}

class CV_EXPORTS_W Foo {
public:
    enum EnumInClass1 { EIC1_AA=0, EIC1_BB=1, EIC1_CC=2 };

    CV_WRAP static int smethod1(int a) { return a + 10; }
    CV_WRAP Foo() { DCV_TRACE_PRINTF("[%s]\n", __func__); }
    CV_WRAP Foo(int value1) : m_value1(value1) { DCV_TRACE_PRINTF("[%s]\n", __func__); }
    ~Foo() { DCV_TRACE_PRINTF("[%s]\n", __func__); }
    CV_WRAP int method1(int a) { return m_value1 + a; }
    CV_WRAP int method2(int a) { return m_value1 + a + 1; }
    CV_WRAP int method2(int a, int b) { return m_value1 + a + b; }
    CV_WRAP Foo::EnumInClass1 method3(Foo::EnumInClass1 e) {
        if (e == EnumInClass1::EIC1_AA) { return EnumInClass1::EIC1_BB; }
        return EnumInClass1::EIC1_CC;
    }
    CV_WRAP EnumInClass1 method4(EnumInClass1 e) {
        if (e == EnumInClass1::EIC1_AA) { return EnumInClass1::EIC1_BB; }
        return EnumInClass1::EIC1_CC;
    }
    CV_WRAP_AS(at) int operator[](int x) const { return x + m_value1; }
    CV_WRAP_AS(getNode) int operator[](const char* name) const { return static_cast<int>(strlen(name)) + m_value1; }
    CV_WRAP_AS(wrapAsSMethod1) static int wrapAsSMethod(int a) { return a + 10; }
    CV_WRAP_AS(wrapAsSMethod2) static int wrapAsSMethod(std::string s) { return static_cast<int>(s.length()); }
    int m_value1{123};
};
class CV_EXPORTS_W Fizz {
public:
    CV_WRAP Fizz(int value1) : m_value1(value1) { DCV_TRACE_PRINTF("[%s]\n", __func__); }
    ~Fizz() { DCV_TRACE_PRINTF("[%s]\n", __func__); }
    CV_WRAP int method1() { return m_value1; }
    int m_value1{333};
};
CV_EXPORTS_W Ptr<Fizz> createFizz() { auto p = std::make_shared<Fizz>(444); return p; }

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
    CV_WRAP ~SubSubC1() { DCV_TRACE_PRINTF("[%s]\n", __func__); }
    CV_WRAP int method1(int a) { return a + m_value1; }
    CV_WRAP int method1(int a, int b) { return a + b + m_value1; }
    CV_WRAP_AS(at) int operator[](int x) const { return x + m_value1; }
    CV_WRAP_AS(getNode) int operator[](const char* name) const { return static_cast<int>(strlen(name)) + m_value1; }
    CV_WRAP_AS(ssc1wrapAsSMethod1) static int wrapAsSMethod(int a) { return a + 10; }
    CV_WRAP_AS(ssc1wrapAsSMethod2) static int wrapAsSMethod(std::string s) { return static_cast<int>(s.length()); }
    int m_value1{111};
};
class CV_EXPORTS_W SubSubI2 {
public:
    CV_WRAP virtual int method1() = 0;
};
class SubSubC2 : public SubSubI2 {
public:
    SubSubC2(int value1) : m_value1(value1) { DCV_TRACE_PRINTF("[%s]\n", __func__); }
    virtual ~SubSubC2() { DCV_TRACE_PRINTF("[%s]\n", __func__); }
    int method1() override { return m_value1; }
    int m_value1{1000};
};
CV_EXPORTS_W Ptr<SubSubI2> createSubSubI2() {
    Ptr<SubSubI2> p{new SubSubC2(2000)};
    return p;
}
// Class without constructor, but not interface class (like cv::Stitcher)
class CV_EXPORTS_W SubSubC3 {
public:
    CV_WRAP static Ptr<SubSubC3> create(int value1) {
        auto p = std::make_shared<SubSubC3>();
        p->m_value1 = value1;
        return p;
    }
    CV_WRAP int method1() { return m_value1; }
private:
    int m_value1{300};
};
CV_EXPORTS CV_WRAP_AS(ns11wrapAsFunc1) int bindTest_WrapAsFunc(int a) { return a + 10; }
CV_EXPORTS CV_WRAP_AS(ns11wrapAsFunc2) int bindTest_WrapAsFunc(std::string s) { return static_cast<int>(s.length()); }

} // namespace Ns11
} // namespace Ns1
} // namespace cv

#endif

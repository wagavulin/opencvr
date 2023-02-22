#ifndef DUMMYCV_HPP
#define DUMMYCV_HPP

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
class CV_EXPORTS_W Foo {
public:
    //CV_WRAP static int smethod1(int a) { return a + 10; }
    CV_WRAP Foo() { PRINT_CXXFUNC(); }
    CV_WRAP Foo(int value1) : m_value1(value1) { PRINT_CXXFUNC(); }
    ~Foo() { PRINT_CXXFUNC(); }
    CV_WRAP void method1(int a) {
        printf("[%s] %d\n", __func__, m_value1 + a);
    }
    CV_WRAP int method2(int a) { return a * 2; }
    CV_WRAP int method2(int a, int b) { return a * b; }
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
// namespace Ns1 {
// class CV_EXPORTS_W Bar {
// public:
//     CV_WRAP Bar() {}
// };
// }
}

#endif

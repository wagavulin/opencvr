#include <ruby.h>
#include <string>
#include <vector>

#define PRINT_FUNC() fprintf(stderr, "[%s]\n", __func__)
#define PRINT_CXXFUNC() fprintf(stderr, "[CXX %s]\n", __func__)
#if TRACE
#define TRACE_PRINTF printf
#else
#define TRACE_PRINTF
#endif

//TODO Below variable is originally defined as TLSData<...> and TLSData is defined in opencv2/core/utils/tls.hpp
thread_local std::vector<std::string> conversionErrorsTLS;

void rbRaiseCVOverloadException(const std::string& functionName)
{
    std::string msg(functionName);
    const std::vector<std::string>& conversionErrors = conversionErrorsTLS;
    //const std::size_t conversionErrorsCount = conversionErrors.size();
    for (const auto& convErr : conversionErrors) {
        msg += convErr;
    }
    rb_raise(rb_eTypeError, "%s", msg.c_str());
}

void rbPopulateArgumentConversionErrors(const std::string& msg)
{
    conversionErrorsTLS.push_back(msg);
}

template<typename T>
static bool rbopencv_to(VALUE obj, T& p){
    TRACE_PRINTF("[rbopencv_to primary] should not be used\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, int& value){
    TRACE_PRINTF("[rbopencv_to int]\n");
    if (!FIXNUM_P(obj))
        return false;
    value = FIX2INT(obj);
    return true;
}

template<typename T>
static VALUE rbopencv_from(const T& src) {
    TRACE_PRINTF("[rbopencv_from primary] should not be used\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const int& value){
    TRACE_PRINTF("[rbopencv_from int]\n");
    return INT2NUM(value);
}

struct MethodDef {
    using func_ptr_for_ruby_method = VALUE (*)(int, VALUE*, VALUE);
    const char *name;
    func_ptr_for_ruby_method wrapper_func;
};

struct ConstDef {
    const char *name;
    long long val;
};

#include "autogen/rbopencv_include.hpp"
using namespace cv;
static VALUE mCV2;
#include "autogen/rbopencv_wrapclass.hpp"

#include "autogen/rbopencv_funcs.hpp"
#include "autogen/rbopencv_modules_content.hpp"

static void init_submodule_cv(VALUE module, MethodDef method_defs[], ConstDef const_defs[]){
    MethodDef *method_def = method_defs;
    while (method_def->name) {
        rb_define_module_function(module, method_def->name, method_def->wrapper_func, -1);
        method_def++;
    }
}

extern "C" {
void Init_cv2(){
    PRINT_FUNC();
    mCV2 = rb_define_module("CV2");

    init_submodule_cv(mCV2, methods_cv, consts_cv);
    #include "autogen/rbopencv_classregistration.hpp"
}
}

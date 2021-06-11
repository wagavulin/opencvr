#include <ruby.h>
#include <opencv2/opencv.hpp>
#include "opencv2/core/utils/tls.hpp"
#include <string>

#include "generated/rbopencv_generated_include.h"
//#include "rbcompat.hpp"

#if TRACE
#define TRACE_PRINTF printf
#else
#define TRACE_PRINTF
#endif

using namespace cv;

static VALUE mCV2;
static VALUE cMat;

using vector_int = std::vector<int>;

TLSData<std::vector<std::string> > conversionErrorsTLS;

inline void rbPrepareArgumentConversionErrorsStorage(std::size_t size)
{
    std::vector<std::string>& conversionErrors = conversionErrorsTLS.getRef();
    conversionErrors.clear();
    conversionErrors.reserve(size);
}

void rbRaiseCVOverloadException(const std::string& functionName)
{
    std::string msg(functionName);
    const std::vector<std::string>& conversionErrors = conversionErrorsTLS.getRef();
    //const std::size_t conversionErrorsCount = conversionErrors.size();
    for (const auto& convErr : conversionErrors) {
        msg += convErr;
    }
    rb_raise(rb_eTypeError, "%s", msg.c_str());
}

void rbPopulateArgumentConversionErrors(const std::string& msg)
{
    conversionErrorsTLS.getRef().push_back(msg);
}

struct WrapMat {
    cv::Mat* mat;
};

static const rb_data_type_t mat_type {
    "Mat",
    {NULL, NULL, NULL},
    NULL, NULL,
    RUBY_TYPED_FREE_IMMEDIATELY
};

static cv::Mat* get_mat(VALUE self){
    WrapMat* ptr;
    TypedData_Get_Struct(self, struct WrapMat, &mat_type, ptr);
    return ptr->mat;
}

static void wrap_mat_free(WrapMat* ptr){
    delete ptr->mat;
    ruby_xfree(ptr);
}

static VALUE wrap_mat_alloc(VALUE klass){
    struct WrapMat* ptr = nullptr;
    VALUE ret = TypedData_Make_Struct(klass, struct WrapMat, &mat_type, ptr);
    ptr->mat = new cv::Mat();
    return ret;
}

static VALUE wrap_mat_init(VALUE self){
    return Qnil;
}

static VALUE wrap_mat_channels(VALUE self){
    int ret = get_mat(self)->channels();
    return INT2FIX(ret);
}

static VALUE wrap_mat_cols(VALUE self){
    int ret = get_mat(self)->cols;
    return INT2FIX(ret);
}

static VALUE wrap_mat_rows(VALUE self){
    int ret = get_mat(self)->rows;
    return INT2FIX(ret);
}

template<typename T>
static bool rbopencv_to(VALUE obj, T& p){
    TRACE_PRINTF("[rbopencv_to primary] should not be used\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Mat& m){
    TRACE_PRINTF("[rbopencv_to Mat]\n");
    if (TYPE(obj) != T_DATA)
        return false;
    RTypedData *typed_data_p = (RTypedData*)obj;
    if (typed_data_p->type != &mat_type)
        return false;
    cv::Mat* raw_img = get_mat(obj);
    m = *raw_img;
    return true;
}

template<typename _Tp, int m, int n>
bool rbopencv_to(VALUE obj, Matx<_Tp, m, n>& mx){
    TRACE_PRINTF("[rbopencv_to Matx] not implemented\n");
    return false;
}

template<typename _Tp, int cn>
bool rbopencv_to(VALUE obj, Vec<_Tp, cn>& vec){
    TRACE_PRINTF("[rbopencv_to Vec] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, void*& ptr){
    TRACE_PRINTF("[rbopencv_to void*] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Scalar& s){
    TRACE_PRINTF("[rbopencv_to Scalar]\n");
    if (TYPE(obj) != T_ARRAY)
        return false;
    long len = rb_array_len(obj);
    if (len > 4) {
        fprintf(stderr, "  too many elements: %ld\n", len);
        return false;
    }
    long copy_num = len < 4 ? len : 4;
    for (long i = 0; i < copy_num; i++) {
        VALUE value_elem = rb_ary_entry(obj, i);
        int value_type = TYPE(value_elem);
        if (value_type == T_FLOAT) {
            s[i] = NUM2DBL(value_elem);
        } else if (value_type == T_FIXNUM) {
            s[i] = FIX2INT(value_elem);
        }
        TRACE_PRINTF("  %ld: %f\n", i, s[i]);
    }
    return true;
}

template<>
bool rbopencv_to(VALUE obj, bool& value){
    TRACE_PRINTF("[rbopencv_to bool]\n");
    value = obj == Qtrue ? true : false;
    return true;
}

template<>
bool rbopencv_to(VALUE obj, size_t& value){
    TRACE_PRINTF("[rbopencv_to size_t] not implemented\n");
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

template<>
bool rbopencv_to(VALUE obj, uchar& value){
    TRACE_PRINTF("[rbopencv_to uchar] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, double& value){
    TRACE_PRINTF("[rbopencv_to double]\n");
    value = NUM2DBL(obj);
    return true;
}

template<>
bool rbopencv_to(VALUE obj, float& value){
    TRACE_PRINTF("[rbopencv_to float]\n");
    value = NUM2DBL(obj);
    return true;
}

template<>
bool rbopencv_to(VALUE obj, String& value){
    TRACE_PRINTF("[rbopencv_to String]\n");
    if (TYPE(obj) != RUBY_T_STRING)
        return false;
    value = RSTRING_PTR(obj);
    return true;
}

template<>
bool rbopencv_to(VALUE obj, Size& sz){
    TRACE_PRINTF("[rbopencv_to Size]\n");
    if (TYPE(obj) != T_ARRAY)
        return false;
    long len = rb_array_len(obj);
    if (len != 2) {
        fprintf(stderr, "  # elements is not 2: %ld\n", len);
        return false;
    }
    double tmp[2];
    for (long i = 0; i < 2; i++) {
        VALUE value_elem = rb_ary_entry(obj, i);
        int value_type = TYPE(value_elem);
        if (value_type == T_FLOAT) {
            tmp[i] = NUM2DBL(value_elem);
        } else if (value_type == T_FIXNUM) {
            tmp[i] = FIX2INT(value_elem);
        }
    }
    sz.width = tmp[0];
    sz.height = tmp[1];
    TRACE_PRINTF("  %f %f\n", sz.width, sz.height);
    return true;
}

template<>
bool rbopencv_to(VALUE obj, Size_<float>& sz){
    TRACE_PRINTF("[rbopencv_to Size_<float>] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Rect& r){
    TRACE_PRINTF("[rbopencv_to Rect]\n");
    if (TYPE(obj) != T_ARRAY)
        return false;
    long len = rb_array_len(obj);
    if (len != 4) {
        fprintf(stderr, "  # elements is not 4: %ld\n", len);
        return false;
    }
    double tmp[4];
    for (long i = 0; i < 4; i++) {
        VALUE value_elem = rb_ary_entry(obj, i);
        int value_type = TYPE(value_elem);
        if (value_type == T_FLOAT) {
            tmp[i] = NUM2DBL(value_elem);
        } else if (value_type == T_FIXNUM) {
            tmp[i] = FIX2INT(value_elem);
        }
    }
    r.x = tmp[0];
    r.y = tmp[1];
    r.width = tmp[2];
    r.height = tmp[3];
    TRACE_PRINTF("  %f %f %f %f\n", r.x, r.y, r.width, r.height);
    return true;
}

template<>
bool rbopencv_to(VALUE obj, Rect2d& r){
    TRACE_PRINTF("[rbopencv_to Rect2d] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Range& r){
    TRACE_PRINTF("[rbopencv_to Range] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Point& p){
    TRACE_PRINTF("[rbopencv_to Point]\n");
    if (TYPE(obj) != T_ARRAY)
        return false;
    p.x = FIX2INT(rb_ary_entry(obj, 0));
    p.y = FIX2INT(rb_ary_entry(obj, 1));
    return true;
}

template<>
bool rbopencv_to(VALUE obj, Point2f& p){
    TRACE_PRINTF("[rbopencv_to Point2f] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Point2d& p){
    TRACE_PRINTF("[rbopencv_to Point2d] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Point3f& p){
    TRACE_PRINTF("[rbopencv_to Point3f] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Point3d& p){
    TRACE_PRINTF("[rbopencv_to Point3d] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Vec4d& v){
    TRACE_PRINTF("[rbopencv_to Vec4d] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Vec4f& v){
    TRACE_PRINTF("[rbopencv_to Vec4f] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Vec4i& v){
    TRACE_PRINTF("[rbopencv_to Vec4i] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Vec3d& v){
    TRACE_PRINTF("[rbopencv_to Vec3d] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Vec3f& v){
    TRACE_PRINTF("[rbopencv_to Vec3f] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Vec3i& v){
    TRACE_PRINTF("[rbopencv_to Vec3i] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Vec2d& v){
    TRACE_PRINTF("[rbopencv_to Vec2d] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Vec2f& v){
    TRACE_PRINTF("[rbopencv_to Vec2f] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, Vec2i& v){
    TRACE_PRINTF("[rbopencv_to Vec2i] not implemented\n");
    return false;
}

template<typename _Tp>
bool rbopencv_to(VALUE obj, std::vector<_Tp>& value){
    TRACE_PRINTF("[rbopencv_to std::vector<_Tp>\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, TermCriteria& dst){
    TRACE_PRINTF("[rbopencv_to TermCriteria] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, RotatedRect& dst){
    TRACE_PRINTF("[rbopencv_to RotatedRect] not implemented\n");
    return false;
}

template<>
bool rbopencv_to(VALUE obj, vector_int& value){
    TRACE_PRINTF("[rbopencv_to vector_int]\n");
    if (TYPE(obj) != T_ARRAY)
        return false;
    long len = rb_array_len(obj);
    for (long i = 0; i < len; i++) {
        VALUE value_elem = rb_ary_entry(obj, i);
        value.push_back(FIX2INT(value_elem));
    }
    return true;
}

template<typename T>
static VALUE rbopencv_from(const T& src) {
    TRACE_PRINTF("[rbopencv_from primary] should not be used\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Mat& m){
    TRACE_PRINTF("[rbopencv_from Mat]\n");
    struct WrapMat* ptr = nullptr;
    VALUE ret = TypedData_Make_Struct(cMat, struct WrapMat, &mat_type, ptr);
    ptr->mat = new cv::Mat();
    *ptr->mat = m;
    return ret;
}

template<typename _Tp, int m, int n>
VALUE rbopencv_from(const Matx<_Tp, m, n>& matx){
    TRACE_PRINTF("[rbopencv_from Matx] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Scalar& src){
    TRACE_PRINTF("[rbopencv_from Scalar] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const bool& value){
    TRACE_PRINTF("[rbopencv_from bool]\n");
    return value ? Qtrue : Qfalse;
}

template<>
VALUE rbopencv_from(const size_t& value){
    TRACE_PRINTF("[rbopencv_from size_t] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const int& value){
    TRACE_PRINTF("[rbopencv_from int]\n");
    return INT2NUM(value);
}

template<>
VALUE rbopencv_from(const uchar& value){
    TRACE_PRINTF("[rbopencv_from uchar] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const double& value){
    TRACE_PRINTF("[rbopencv_from double]\n");
    return DBL2NUM(value);
}

template<>
VALUE rbopencv_from(const float& value){
    TRACE_PRINTF("[rbopencv_from float] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const int64& value){
    TRACE_PRINTF("[rbopencv_from int64] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const String& value){
    TRACE_PRINTF("[rbopencv_from String] not implemented\n");
    return Qnil;
}

#if 0 // Is this same as String?
template<>
VALUE rbopencv_from(const std::string& value){
    TRACE_PRINTF("[rbopencv_from ] not implemented\n");
    return Qnil;
}
#endif

template<>
VALUE rbopencv_from(const Size& sz){
    TRACE_PRINTF("[rbopencv_from Size]\n");
    VALUE value_width = INT2NUM(sz.width);
    VALUE value_height = INT2NUM(sz.height);
    VALUE ret = rb_ary_new3(2, value_width, value_height);
    return ret;
}

template<>
VALUE rbopencv_from(const Size_<float>& sz){
    TRACE_PRINTF("[rbopencv_from Size_<float>] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Rect& r){
    TRACE_PRINTF("[rbopencv_from Rect] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Rect2d& r){
    TRACE_PRINTF("[rbopencv_from Rect2d] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Range& r){
    TRACE_PRINTF("[rbopencv_from Range] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Point& p){
    TRACE_PRINTF("[rbopencv_from Point]\n");
    VALUE value_x = INT2NUM(p.x);
    VALUE value_y = INT2NUM(p.y);
    VALUE ret = rb_ary_new3(2, value_x, value_y);
    return ret;
}

template<>
VALUE rbopencv_from(const Point2f& p){
    TRACE_PRINTF("[rbopencv_from Point2f] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Point3f& p){
    TRACE_PRINTF("[rbopencv_from Poin3f] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Vec4d& v){
    TRACE_PRINTF("[rbopencv_from Vec4d] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Vec4f& v){
    TRACE_PRINTF("[rbopencv_from Vec4f] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Vec4i& v){
    TRACE_PRINTF("[rbopencv_from Vec4i] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Vec3d& v){
    TRACE_PRINTF("[rbopencv_from Vec3d] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Vec3f& v){
    TRACE_PRINTF("[rbopencv_from Vec3f] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Vec3i& v){
    TRACE_PRINTF("[rbopencv_from Vec3i] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Vec2d& v){
    TRACE_PRINTF("[rbopencv_from Vec2d] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Vec2f& v){
    TRACE_PRINTF("[rbopencv_from Vec2f] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Vec2i& v){
    TRACE_PRINTF("[rbopencv_from Vec2i] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Point2d& p){
    TRACE_PRINTF("[rbopencv_from Point2d] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Point3d& p){
    TRACE_PRINTF("[rbopencv_from Point3d] not implemented\n");
    return Qnil;
}

template<typename _Tp>
VALUE rbopencv_from(const std::vector<_Tp>& value){
    TRACE_PRINTF("[rbopencv_from std::vector<_Tp>] not implemented\n");
    return Qnil;
}

template<typename... Ts>
VALUE rbopencv_from(const std::tuple<Ts...>& cpp_tuple){
    TRACE_PRINTF("[rbopencv_from std::tuple<Ts...>] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const std::pair<int, double>& src){
    TRACE_PRINTF("[rbopencv_from std::pair<int, double>] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const TermCriteria& src){
    TRACE_PRINTF("[rbopencv_from TermCriteria] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const RotatedRect& src){
    TRACE_PRINTF("[rbopencv_from RotatedRect] not implemented\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const Moments& m){
    TRACE_PRINTF("[rbopencv_from Moment] not implemented\n");
    return Qnil;
}

struct ConstDef
{
    const char * name;
    long long val;
};

struct MethodDef
{
    using func_ptr_for_ruby_method = VALUE (*)(int, VALUE*, VALUE);
    const char *name;
    func_ptr_for_ruby_method wrapper_func;
};

#include "generated/rbopencv_generated_funcs.h"
#include "generated/rbopencv_generated_modules_content.h"

static void init_submodule_cv(VALUE module, MethodDef method_defs[], ConstDef const_defs[]){
    MethodDef *method_def = method_defs;
    while (method_def->name) {
        rb_define_module_function(module, method_def->name, method_def->wrapper_func, -1);
        method_def++;
    }
    ConstDef *const_def = const_defs;
    while (const_def->name) {
        if (const_def->name[0] != '_')
            rb_define_const(module, const_def->name, INT2FIX(const_def->val));
        const_def++;
    }
}

extern "C" {
void Init_cv2(){
    mCV2 = rb_define_module("CV2");

    init_submodule_cv(mCV2, methods_cv, consts_cv);

    cMat = rb_define_class_under(mCV2, "Mat", rb_cObject);
    rb_define_alloc_func(cMat, wrap_mat_alloc);
    rb_define_private_method(cMat, "initialize", RUBY_METHOD_FUNC(wrap_mat_init), 0);
    rb_define_method(cMat, "cols", RUBY_METHOD_FUNC(wrap_mat_cols), 0);
    rb_define_method(cMat, "rows", RUBY_METHOD_FUNC(wrap_mat_rows), 0);
    rb_define_method(cMat, "channels", RUBY_METHOD_FUNC(wrap_mat_channels), 0);

}
}

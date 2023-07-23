#include <ruby.h>
#include <opencv2/opencv.hpp>
#include <opencv2/core/types.hpp>
#include <opencv2/core/types_c.h>
#include <numo/narray.h>
#include <sstream>
#include <string>
#include <type_traits>
#include <vector>
#include <cstdio>
#include <cstdlib>
#include <cstdarg>

static int trace_printf(const char *filename, int line, const char *fmt, ...){
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

#define TRACE_PRINTF(fmt, ...) trace_printf(__FILE__, __LINE__, fmt, ##__VA_ARGS__)

using namespace cv;
using namespace std;

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

using vector_int = std::vector<int>;
using vector_char = std::vector<char>;
using vector_uchar = std::vector<uchar>;
using vector_float = std::vector<float>;
using vector_double = std::vector<double>;
using vector_String = std::vector<std::string>;
using vector_string = std::vector<std::string>;
using vector_Mat = std::vector<Mat>;
using vector_Point = std::vector<Point>;
using vector_Point2f = std::vector<Point2f>;
using vector_Rect = std::vector<Rect>;
using vector_vector_int = std::vector<std::vector<int>>;
using vector_vector_Point2f = std::vector<std::vector<Point2f>>;

const char* db_get_class_name(VALUE o){
    VALUE vtmp1 = rb_funcall(o, rb_intern("class"), 0, 0);
    VALUE vtmp2 = rb_funcall(vtmp1, rb_intern("to_s"), 0, 0);
    return StringValuePtr(vtmp2);
}

void db_dump_narray(int level, const narray_t* na){
    printf("%*sndim: %d, type: %d, flag: [%d,%d], elmsz: %d, size: %ld\n", level*2, "", na->ndim, na->type, na->flag[0], na->flag[1], na->elmsz, na->size);
    for (unsigned char i = 0; i < na->ndim; i++) {
        printf("%*sshape[%d]: %ld\n", (level+1)*2, "", i, na->shape[i]);
    }
    printf("%*sreduce: %s: %d\n", level*2, "", db_get_class_name(na->reduce), NUM2INT(na->reduce));
}

void db_dump_narray_data(int level, const narray_data_t* nad){
    db_dump_narray(level, &nad->base);
    printf("%*sowned: %d\n", level*2, "", nad->owned);
}

void db_dump_narray_view(int level, const narray_view_t* nav){
    int i;
    size_t *idx;
    size_t j;

    printf("  offset = %ld\n", (size_t)nav->offset);
    printf("  stridx = %ld\n", (size_t)nav->stridx);

    if (nav->stridx) {
        printf("  stridx = [");
        for (i=0; i<nav->base.ndim; i++) {
            if (SDX_IS_INDEX(nav->stridx[i])) {

                idx = SDX_GET_INDEX(nav->stridx[i]);
                printf("  index[%d]=[", i);
                for (j=0; j<nav->base.shape[i]; j++) {
                    printf(" %ld", idx[j]);
                }
                printf(" ] ");

            } else {
                printf(" %ld", SDX_GET_STRIDE(nav->stridx[i]));
            }
        }
        printf(" ]\n");
    }
}

class NumpyAllocator : public cv::MatAllocator {
public:
    NumpyAllocator() { stdAllocator = cv::Mat::getStdAllocator(); }
    ~NumpyAllocator() {}

    UMatData* allocate(VALUE o, int dims, const int* sizes, int type, size_t* step) const {
        narray_data_t* nad = na_get_narray_data_t(o);
        VALUE view = rb_funcall(o, rb_intern("view"), 0, 0);
        narray_view_t* nav = na_get_narray_view_t(view);

        UMatData* u = new UMatData(this);
        //TRACE_PRINTF("  u: %p\n", u);
        u->data = u->origdata = (uchar*)nad->ptr;
        if (!nav->stridx) {
            throw std::runtime_error("[NumpyAllocator::allocate] nav->stridx is NULL");
        }
        for (unsigned char i = 0; i < nad->base.ndim; i++) {
            if (SDX_IS_INDEX(nav->stridx[i])) {
                //TRACE_PRINTF("nav->stridx[%d] is not stride\n", i);
                throw std::runtime_error("[NumpyAllocator::allocate] nav->stridx[i] is not stride");
            } else {
                ssize_t stride = SDX_GET_STRIDE(nav->stridx[i]);
                step[i] = (size_t)stride;
                //printf("step[%d]: %ld\n", i, step[i]);
            }
        }
        step[dims-1] = CV_ELEM_SIZE(type);
        //printf("step[dims-1=%d]: %ld\n", dims-1, step[dims-1]);
        u->size = sizes[0] * step[0];
        //printf("u->size: %ld\n", u->size);
        u->userdata = (void*)o;
        return u;
    }

    UMatData* allocate(int dims0, const int* sizes, int type, void* data, size_t* step, AccessFlag flags, UMatUsageFlags usageFlags) const override {
        TRACE_PRINTF("[allocate] dims0: %d, type: %d, depth: %d, cn: %d\n", dims0, type, CV_MAT_DEPTH(type), CV_MAT_CN(type));
        for (int i = 0; i < dims0; i++) {
            //TRACE_PRINTF("  sizes[%d]: %d\n", i, sizes[i]);
        }
        if (data) {
            return stdAllocator->allocate(dims0, sizes, type, data, step, flags, usageFlags);
        }
        int depth = CV_MAT_DEPTH(type);
        int cn = CV_MAT_CN(type);
        const int f = (int)(sizeof(size_t)/8);
        VALUE numo_type = depth == CV_8U ? numo_cUInt8 : depth == CV_8S ? numo_cInt8 :
        depth == CV_16U ? numo_cUInt16 : depth == CV_16S ? numo_cInt16 :
        depth == CV_32S ? numo_cInt32 : depth == CV_32F ? numo_cSFloat :
        depth == CV_64F ? numo_cDFloat : 0xffff;
        if (numo_type == 0xffff) {
            throw std::runtime_error("[NumpyAllocator::allocate] Unsupported type\n");
        }

        int i, dims = dims0;
        cv::AutoBuffer<size_t> _sizes(dims + 1);
        for (i = 0; i < dims; i++) {
            _sizes[i] = sizes[i];
        }
        if (cn > 1) {
            _sizes[dims++] = cn;
        }
        VALUE o = rb_narray_new(numo_type, dims, _sizes.data());
        rb_funcall(o, rb_intern("fill"), 1, INT2FIX(3));

        cv::UMatData* ret = allocate(o, dims0, sizes, type, step);
        //TRACE_PRINTF("ret: %p\n", ret);
        return ret;
    }

    bool allocate(UMatData* u, AccessFlag accessFlags, UMatUsageFlags usageFlags) const override {
        TRACE_PRINTF("[allocate]\n");
        return false;
    }

    void deallocate(UMatData* u) const override {
        TRACE_PRINTF("[deallocate] %p\n", u);
        if (!u)
            return;
        CV_Assert(u->urefcount >= 0);
        CV_Assert(u->refcount >= 0);
        if (u->refcount == 0) {
            //TRACE_PRINTF("  refcount == 0; delete %p\n", u);
            delete u;
        } else {
            //TRACE_PRINTF("  refcount >= 1\n");
        }
    }

    const cv::MatAllocator* stdAllocator;
};

NumpyAllocator g_numpyAllocator;

template<typename T>
static bool rbopencv_to(VALUE obj, T& p){
    TRACE_PRINTF("[rbopencv_to primary] should not be used\n");
    return false;
}

template<>
bool rbopencv_to(VALUE o, Mat& m){
    TRACE_PRINTF("[rbopencv_to Mat] o: %s\n", db_get_class_name(o));
    bool allowND = true;
    if (NIL_P(o)) {
        //TRACE_PRINTF("  o is NIL\n");
        if (!m.data)
            m.allocator = &g_numpyAllocator;
        return true;
    }

    if (TYPE(o) == T_FIXNUM) {
        //TRACE_PRINTF("  o is FIXNUM\n");
        return false;
    }
    if (TYPE(o) == T_FLOAT) {
        //TRACE_PRINTF("  o is \n");
        return false;
    }

    bool needcopy = false, needcast = false;
    narray_data_t* nad = na_get_narray_data_t(o);
    VALUE rclass = rb_obj_class(o), new_rclass = rclass;
    int type = rclass == numo_cUInt8 ? CV_8U :
        rclass == numo_cInt8 ? CV_8S :
        rclass == numo_cUInt16 ? CV_16U :
        rclass == numo_cInt16 ? CV_16S :
        rclass == numo_cInt32 ? CV_32S :
        rclass == numo_cSFloat ? CV_32F :
        rclass == numo_cDFloat ? CV_64F : -1;
    if (type < 0) {
        if (rclass == numo_cInt64 || rclass == numo_cUInt64) {
            needcopy = needcast = true;
            new_rclass = numo_cInt32;
            type = CV_32S;
        } else {
            fprintf(stderr, "type: %s is not supported\n", db_get_class_name(o));
            return false;
        }
    }

    int ndims = (int)nad->base.ndim;
    if (ndims >= CV_MAX_DIM) {
        //TRACE_PRINTF("dimensionality (=%d) is too high\n", ndims);
        return false;
    }

    int size[CV_MAX_DIM + 1];
    size_t step[CV_MAX_DIM + 1];
    size_t elemsize = CV_ELEM_SIZE1(type);
    bool ismultichannel = ndims == 3 && nad->base.shape[2] <= CV_CN_MAX;
    VALUE view = rb_funcall(o, rb_intern("view"), 0, 0);
    narray_view_t* nav = na_get_narray_view_t(view);
    //TRACE_PRINTF("  ismultichannel: %d\n", ismultichannel);
    for (int i = 0; i < ndims; i++) {
        if (SDX_IS_STRIDE(nav->stridx[i])) {
            //TRACE_PRINTF("  shape[%d]: %ld, stride[%d]: %ld\n", i, nad->base.shape[i], i, SDX_GET_STRIDE(nav->stridx[i]));
        } else {
            //TRACE_PRINTF("  shape[%d]: %ld, is not stride -> not supported\n", i, nad->base.shape[i]);
            return false;
        }
    }

    for( int i = ndims-1; i >= 0 && !needcopy; i-- ) {
        // [original cv2.cpp comment]
        // these checks handle cases of
        //  a) multi-dimensional (ndims > 2) arrays, as well as simpler 1- and 2-dimensional cases
        //  b) transposed arrays, where _strides[] elements go in non-descending order
        //  c) flipped arrays, where some of _strides[] elements are negative
        // the _sizes[i] > 1 is needed to avoid spurious copies when NPY_RELAXED_STRIDES is set
        // [original cv2.cpp comment end]
        // _sizes[i] can be replaced with nad->base.shape[i]
        // _strides[i] can be replaced with SDX_GET_STRIDE(nav->stridx[i])
        if ((i == ndims - 1 && nad->base.shape[i] > 1 && (size_t)SDX_GET_STRIDE(nav->stridx[i]) != elemsize) ||
            (i < ndims - 1 && nad->base.shape[i] > 1 && SDX_GET_STRIDE(nav->stridx[i]) < SDX_GET_STRIDE(nav->stridx[i+1])))
            needcopy = true;
    }

    if( ismultichannel && SDX_GET_STRIDE(nav->stridx[1]) != elemsize * nad->base.shape[2] )
        needcopy = true;

    if (needcopy) {
        //TRACE_PRINTF("needcopy case is not supported\n");
        return false;
    }

    // Normalize strides in case NPY_RELAXED_STRIDES is set
    size_t default_step = elemsize;
    for ( int i = ndims - 1; i >= 0; --i )
    {
        size[i] = (int)nad->base.shape[i];
        if ( size[i] > 1 )
        {
            step[i] = (size_t)SDX_GET_STRIDE(nav->stridx[i]);
            default_step = step[i] * size[i];
        }
        else
        {
            step[i] = default_step;
            default_step *= size[i];
        }
    }

    // handle degenerate case
    if( ndims == 0) {
        size[ndims] = 1;
        step[ndims] = elemsize;
        ndims++;
    }

    if( ismultichannel )
    {
        ndims--;
        type |= CV_MAKETYPE(0, size[2]);
    }

    if( ndims > 2 && !allowND )
    {
        //TRACE_PRINTF("has more than 2 dimensions\n");
        return false;
    }

    //TRACE_PRINTF("  ndims: %d, type: %d\n", ndims, type);
    for (int i = 0; i < ndims; i++) {
        //TRACE_PRINTF("  size[%d]: %d, step[%d] %ld\n", i, size[i], i, step[i]);
    }
    m = Mat(ndims, size, type, nad->ptr, step);
    m.u = g_numpyAllocator.allocate(o, ndims, size, type, step);
    m.addref();
    m.allocator = &g_numpyAllocator;

    return true;
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
bool rbopencv_to(VALUE obj, char& value){
    TRACE_PRINTF("[rbopencv_to char]\n");
    if (!FIXNUM_P(obj))
        return false;
    value = FIX2INT(obj);
    return true;
}

template<>
bool rbopencv_to(VALUE obj, uchar& value){
    TRACE_PRINTF("[rbopencv_to uchar]\n");
    if (!FIXNUM_P(obj))
        return false;
    value = FIX2INT(obj);
    return true;
}

template<>
bool rbopencv_to(VALUE obj, size_t& value){
    TRACE_PRINTF("[rbopencv_to size_t]\n");
    if (!FIXNUM_P(obj))
        return false;
    value = FIX2ULONG(obj);
    return true;
}

template<>
bool rbopencv_to(VALUE obj, bool& value){
    TRACE_PRINTF("[rbopencv_to bool]\n");
    value = obj == Qtrue ? true : false;
    return true;
}

template<>
bool rbopencv_to(VALUE obj, double& value){
    TRACE_PRINTF("[rbopencv_to double]\n");
    ruby_value_type t = rb_type(obj);
    bool ret = false;
    if (rb_integer_type_p(obj)) {
        value = FIX2INT(obj);
        ret = true;
    } else if (RB_TYPE_P(obj, RUBY_T_FLOAT)) {
        value = NUM2DBL(obj);
        ret = true;
    }
    return ret;
}

template<>
bool rbopencv_to(VALUE obj, float& value){
    TRACE_PRINTF("[rbopencv_to float]\n");
    double tmp;
    bool ret = rbopencv_to(obj, tmp);
    if (ret)
        value = static_cast<float>(tmp);
    return ret;
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
    TRACE_PRINTF("[rbopencv_to Point2f]\n");
    if (TYPE(obj) != T_ARRAY)
        return false;
    bool ret = true;
    ret &= rbopencv_to(rb_ary_entry(obj, 0), p.x);
    ret &= rbopencv_to(rb_ary_entry(obj, 1), p.y);
    return ret;
}

template<>
bool rbopencv_to(VALUE obj, Point2d& p){
    TRACE_PRINTF("[rbopencv_to Point2d]\n");
    if (TYPE(obj) != T_ARRAY)
        return false;
    bool ret = true;
    ret &= rbopencv_to(rb_ary_entry(obj, 0), p.x);
    ret &= rbopencv_to(rb_ary_entry(obj, 1), p.y);
    return ret;
}

template<>
bool rbopencv_to(VALUE obj, Rect& r){
    TRACE_PRINTF("[rbopencv_to Rect]\n");
    if (TYPE(obj) != T_ARRAY) {
        fprintf(stderr, "  # elements is not array: 0x%02x\n", TYPE(obj));
        return false;
    }
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
    //TRACE_PRINTF("  %f %f %f %f\n", r.x, r.y, r.width, r.height);
    return true;
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
        //TRACE_PRINTF("  %ld: %f\n", i, s[i]);
    }
    return true;
}

template<>
bool rbopencv_to(VALUE obj, Size_<float>& sz){
    TRACE_PRINTF("[rbopencv_to Size_<float>]\n");
    if (TYPE(obj) != T_ARRAY)
        return false;
    bool ret = true;
    ret &= rbopencv_to(rb_ary_entry(obj, 0), sz.width);
    ret &= rbopencv_to(rb_ary_entry(obj, 1), sz.height);
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
    int tmp_i[2];
    for (long i = 0; i < 2; i++) {
        VALUE value_elem = rb_ary_entry(obj, i);
        int value_type = TYPE(value_elem);
        if (value_type == T_FLOAT) {
            double tmp_d = NUM2DBL(value_elem);
            tmp_i[i] = static_cast<int>(tmp_d);
        } else if (value_type == T_FIXNUM) {
            tmp_i[i] = FIX2INT(value_elem);
        }
    }
    sz.width = tmp_i[0];
    sz.height = tmp_i[1];
    //TRACE_PRINTF("  %f %f\n", sz.width, sz.height);
    return true;
}

template<>
bool rbopencv_to(VALUE obj, RotatedRect& dst){
    TRACE_PRINTF("[rbopencv_to RotatedRect]\n");
    if (TYPE(obj) != T_ARRAY)
        return false;
    bool ret = true;
    ret &= rbopencv_to(rb_ary_entry(obj, 0), dst.center);
    ret &= rbopencv_to(rb_ary_entry(obj, 1), dst.size);
    ret &= rbopencv_to(rb_ary_entry(obj, 2), dst.angle);
    return true;
}

template<typename T>
bool rbopencv_to(VALUE obj, std::vector<T>& value){
    TRACE_PRINTF("[rbopencv_to vector_T %s]\n", typeid(T).name());
    if (TYPE(obj) != T_ARRAY)
        return false;
    long len = rb_array_len(obj);
    for (long i = 0; i < len; i++) {
        VALUE value_elem = rb_ary_entry(obj, i);
        T raw_elem;
        bool ret = rbopencv_to(value_elem, raw_elem);
        if (!ret)
            return false;
        value.push_back(raw_elem);
    }
    return true;
}

template<typename T>
static VALUE rbopencv_from(const T& src) {
    TRACE_PRINTF("[rbopencv_from primary] should not be used\n");
    return Qnil;
}

template<>
VALUE rbopencv_from(const cv::Mat& m){
    if (!m.data) {
        TRACE_PRINTF("m.data is null\n");
        return Qnil;
    }
    //TRACE_PRINTF("m.u: %p\n", m.u);
    cv::Mat temp, *p = (cv::Mat*)&m;
    if (!p->u || p->allocator != &g_numpyAllocator) {
        temp.allocator = &g_numpyAllocator;
        m.copyTo(temp);
        p = &temp;
    }
    VALUE o = (VALUE)p->u->userdata;
    return o;
}

template<>
VALUE rbopencv_from(const int& value){
    TRACE_PRINTF("[rbopencv_from int]\n");
    return INT2NUM(value);
}

template<>
VALUE rbopencv_from(const char& value){
    TRACE_PRINTF("[rbopencv_from char]\n");
    return INT2NUM(value);
}

template<>
VALUE rbopencv_from(const uchar& value){
    TRACE_PRINTF("[rbopencv_from uchar]\n");
    return INT2NUM(value);
}

template<>
VALUE rbopencv_from(const size_t& value){
    TRACE_PRINTF("[rbopencv_from size_t]\n");
    return ULONG2NUM(value);
}

template<>
VALUE rbopencv_from(const bool& value){
    TRACE_PRINTF("[rbopencv_from bool]\n");
    return value ? Qtrue : Qfalse;
}

template<>
VALUE rbopencv_from(const double& value){
    TRACE_PRINTF("[rbopencv_from double]\n");
    return DBL2NUM(value);
}

template<>
VALUE rbopencv_from(const float& value){
    TRACE_PRINTF("[rbopencv_from float]\n");
    return DBL2NUM(value);
}

template<>
VALUE rbopencv_from(const String& value){
    TRACE_PRINTF("[rbopencv_from String]\n");
    VALUE ret = rb_str_new_cstr(value.c_str());
    return ret;
}

template<>
VALUE rbopencv_from(const Rect& rect){
    TRACE_PRINTF("[rbopencv_from Rect]\n");
    VALUE value_x = INT2NUM(rect.x);
    VALUE value_y = INT2NUM(rect.y);
    VALUE value_width = INT2NUM(rect.width);
    VALUE value_height = INT2NUM(rect.height);
    VALUE ret = rb_ary_new3(4, value_x, value_y, value_width, value_height);
    return ret;
}

template<>
VALUE rbopencv_from(const Scalar& s){
    TRACE_PRINTF("[rbopencv_from Scalar]\n");
    VALUE v0 = DBL2NUM(s[0]);
    VALUE v1 = DBL2NUM(s[1]);
    VALUE v2 = DBL2NUM(s[2]);
    VALUE v3 = DBL2NUM(s[3]);
    VALUE ret = rb_ary_new3(4, v0, v1, v2, v3);
    return ret;
}

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
    TRACE_PRINTF("[rbopencv_from Size_<float>]\n");
    VALUE value_width = rbopencv_from(sz.width);
    VALUE value_height = rbopencv_from(sz.height);
    VALUE ret = rb_ary_new3(2, value_width, value_height);
    return ret;
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
    TRACE_PRINTF("[rbopencv_from Point2f]\n");
    VALUE value_x = rbopencv_from(p.x);
    VALUE value_y = rbopencv_from(p.y);
    VALUE ret = rb_ary_new3(2, value_x, value_y);
    return ret;
}

template<>
VALUE rbopencv_from(const Point2d& p){
    TRACE_PRINTF("[rbopencv_from Point2d]\n");
    VALUE value_x = rbopencv_from(p.x);
    VALUE value_y = rbopencv_from(p.y);
    VALUE ret = rb_ary_new3(2, value_x, value_y);
    return ret;
}

template<>
VALUE rbopencv_from(const RotatedRect& src){
    TRACE_PRINTF("[rbopencv_from RotatedRect]\n");
    VALUE value_center = rbopencv_from(src.center);
    VALUE value_size = rbopencv_from(src.size);
    VALUE value_angle = rbopencv_from(src.angle);
    VALUE ret = rb_ary_new3(3, value_center, value_size, value_angle);
    return ret;
}

template<typename T>
VALUE rbopencv_from(const std::vector<T>& value){
    TRACE_PRINTF("[rbopencv_from vector_T %s]\n", typeid(T).name());
    size_t size = value.size();
    VALUE ret = rb_ary_new2(size);
    for (const auto& x : value) {
        VALUE item = rbopencv_from(x);
        rb_ary_push(ret, item);
    }
    return ret;
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
static VALUE mCV2;
#include "autogen/rbopencv_wrapclass.hpp"

#include "autogen/rbopencv_enum_converter.hpp"
#include "autogen/rbopencv_funcs.hpp"
#include "autogen/rbopencv_modules_content.hpp"

static std::vector<std::string> split_string(const std::string& str, char delim){
    std::vector<std::string> substrs;
    std::stringstream sstream{str};
    std::string substr;
    while (getline(sstream, substr, delim))
        if (!substr.empty())
            substrs.push_back(substr);
    return substrs;
}

std::string to_submod_name(const std::string subname){
    if (subname == "cv")
        return std::string{"CV2"};
    std::string submod_name{subname};
    submod_name[0] = toupper(submod_name[0]);
    return submod_name;
}

static void init_submodule(const std::string& name, MethodDef method_defs[], ConstDef const_defs[]){
    //printf("[%s]\n", __func__);
    auto subnames = split_string(name, '.');
    VALUE parent_mod = mCV2;
    for (const auto& subname : subnames) {
        const std::string submod_name = to_submod_name(subname);
        int sym = rb_intern(submod_name.c_str());
        int is_defined = rb_const_defined(parent_mod, sym);
        //printf("  %s %d %d\n", submod_name.c_str(), sym, is_defined);
        if (is_defined) {
            parent_mod = rb_const_get(parent_mod, sym);
        } else {
            parent_mod = rb_define_module_under(parent_mod, submod_name.c_str());
        }
    }

    MethodDef *method_def = method_defs;
    while (method_def->name) {
        rb_define_module_function(parent_mod, method_def->name, method_def->wrapper_func, -1);
        method_def++;
    }
    ConstDef *const_def = const_defs;
    while (const_def->name) {
        // Need to check whether the 1st character is upper case.
        // cv::datasets defines both uppercase and lowercase constants (e.g. "CIRCLE" and "circle")
        if (const_def->name[0] != '_' && isupper(const_def->name[0]))
            rb_define_const(parent_mod, const_def->name, INT2FIX(const_def->val));
        const_def++;
    }
}

// 1st arg (top_module) must be mCV2
static void init_submodule_bak(VALUE top_module, const char* name, MethodDef method_defs[], ConstDef const_defs[]){
    // traverse and create nested submodules
    std::string s = name;
    size_t i = s.find('.');
    VALUE parent_mod = top_module;
    while (i < s.length() && i != std::string::npos)
    {
        size_t j = s.find('.', i);
        if (j == std::string::npos)
            j = s.length();
        std::string short_name = s.substr(i, j-i);
        std::string full_name = s.substr(0, j);
        i = j+1;
        std::string module_short_name{short_name};
        // Ruby module name must begins with uppercase
        module_short_name[0] = toupper(module_short_name[0]);

        if (module_short_name == "")
            parent_mod = top_module;
        else {
            int name_sym = rb_intern(module_short_name.c_str());
            int is_defined = rb_const_defined(parent_mod, name_sym);
            VALUE submod;
            if (is_defined)
                submod = rb_const_get(parent_mod, name_sym);
            else
                submod = rb_define_module_under(parent_mod, module_short_name.c_str());
            parent_mod = submod;
        }
    }

    MethodDef *method_def = method_defs;
    while (method_def->name) {
        rb_define_module_function(parent_mod, method_def->name, method_def->wrapper_func, -1);
        method_def++;
    }
    ConstDef *const_def = const_defs;
    while (const_def->name) {
        // Need to check whether the 1st character is upper case.
        // cv::datasets defines both uppercase and lowercase constants (e.g. "CIRCLE" and "circle")
        if (const_def->name[0] != '_' && isupper(const_def->name[0]))
            rb_define_const(parent_mod, const_def->name, INT2FIX(const_def->val));
        const_def++;
    }
}

static VALUE get_parent_module_by_wname(VALUE top_module, const std::string wname){
    // wname: Ns1_Ns11_SubSubC1
    // printf("[%s] %s\n", __func__, wname.c_str());
    auto modnames = split_string(wname, '_'); // ["Ns1", "Ns11", "SubSubC1"]
    modnames.pop_back(); // remove the last element (class name) => ["Ns1", "Ns11"]
    // Special handling. In wname, module names are split by "_", but some classes
    // have "_".
    if (wname == "Ml_Ann_MLP") {
        modnames = {"Ml"};
    } else if (wname == "Simpleblobdetector_Params") {
        modnames = {"SimpleBlobDetector"};
    }
    VALUE parent_mod = top_module;
    VALUE submod;
    for (const auto &modname : modnames) {
        //printf("[%s] modname: %s\n", __func__, modname.c_str());
        int name_sym = rb_intern(modname.c_str());
        int is_defined = rb_const_defined(parent_mod, name_sym);
        VALUE submod;
        if (is_defined)
            submod = rb_const_get(parent_mod, name_sym);
        else {
            fprintf(stderr, "[ruby cv2.cpp %s] Error: parent_mod is not defined\n", __func__);
            parent_mod = Qnil;
            break;
        }
        parent_mod = submod;
    }
    return parent_mod;
}

extern "C" {
void Init_cv2(){
    mCV2 = rb_define_module("CV2");

    #include "autogen/rbopencv_namespaceregistration.hpp"
    //#include "autogen/rbopencv_classregistration.hpp"
}
}

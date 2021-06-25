#include <opencv2/opencv.hpp>


namespace cv { // cv for bind test
double bindTest1(int a, Point& b, int* c, int d, RNG* rng, double e){
    //printf("[C++ bindTest1] a: %d, b: [%d, %d], c: %d, d: %d, e: %f\n", a, b.x, b.y, *c, d, e);
    b.x += 10;
    b.y -= 10;
    *c = 23;
    double ret = (double)a + (double)(b.x) + (double)(b.y) + (double)(*c) + (double)d + e;
    //printf("ret: %f\n", ret);
    return ret;
}

CV_EXPORTS_W void bindTest2(int a){
    int tmp = a + 10;
    if (tmp) {}
}

CV_EXPORTS_W int bindTest3(int a){
    return a + a;
}

CV_EXPORTS_W void bindTest4(int a, CV_IN_OUT Point& pt){
    pt.x += a;
    pt.y -= a;
}

CV_EXPORTS_W void bindTest5(int a, CV_IN_OUT Point& pt, CV_OUT int* x){
    pt.x += a;
    pt.y -= a;
    *x = 23;
}

CV_EXPORTS_W bool bindTest6(int a, CV_IN_OUT Point& pt, CV_OUT int* x){
    pt.x += a;
    pt.y -= a;
    *x = 23;
    return true;
}

CV_EXPORTS_W void bindTest_InOut_bool(CV_IN_OUT bool& a){
    a = !a;
}

CV_EXPORTS_W void bindTest_InOut_uchar(CV_IN_OUT uchar& a){
    a += 10;
}

CV_EXPORTS_W void bindTest_InOut_int(CV_IN_OUT int& a){
    a += 10;
}

CV_EXPORTS_W void bindTest_Out_intp(CV_OUT int* a){
    *a = 10;
}

CV_EXPORTS_W void bindTest_InOut_size_t(CV_IN_OUT size_t& a){
    a += 10;
}

CV_EXPORTS_W void bindTest_InOut_float(CV_IN_OUT float& a){
    a += 0.5;
}

CV_EXPORTS_W void bindTest_InOut_double(CV_IN_OUT double& a){
    a += 0.5;
}

CV_EXPORTS_W void bindTest_InOut_Size(CV_IN_OUT Size& a){
    a.width += 10;
    a.height += 10;
}

CV_EXPORTS_W void bindTest_InOut_Point(CV_IN_OUT Point& a){
    a.x += 10;
    a.y += 10;
}

}

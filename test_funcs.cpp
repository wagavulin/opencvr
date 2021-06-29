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

CV_EXPORTS_W double bindTest_overload(Point a, Point b, double c){
    return a.x + a.y + b.x + b.y + c;
}

CV_EXPORTS_W double bindTest_overload(RotatedRect a){
    return a.center.x + a.center.y + a.size.width + a.size.height + a.angle;
}

CV_EXPORTS_W void bindTest_InOut_Mat(CV_IN_OUT Mat& a){
    a.at<Vec3b>(0, 0)[0] = 100;
    a.at<Vec3b>(0, 0)[1] = 110;
    a.at<Vec3b>(0, 0)[2] = 120;
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

CV_EXPORTS_W void bindTest_InOut_Size2f(CV_IN_OUT Size2f& a){
    a.width += 0.5;
    a.height += 0.5;
}

CV_EXPORTS_W void bindTest_InOut_Point(CV_IN_OUT Point& a){
    a.x += 10;
    a.y += 10;
}

CV_EXPORTS_W void bindTest_InOut_Point2f(CV_IN_OUT Point2f& a){
    a.x += 0.5;
    a.y += 0.5;
}

CV_EXPORTS_W void bindTest_InOut_RotatedRect(CV_IN_OUT RotatedRect& a){
    a.center.x += 0.5;
    a.center.y += 0.5;
    a.size.width += 0.5;
    a.size.height += 0.5;
    a.angle += 0.5;
}

}

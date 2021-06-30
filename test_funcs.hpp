#include "opencv2/core.hpp"

namespace cv
{

CV_EXPORTS_W double bindTest1(int a, CV_IN_OUT Point& b, CV_OUT int* c, int d=10, RNG* rng=0, double e=1.2);
CV_EXPORTS_W void bindTest2(int a);
CV_EXPORTS_W int bindTest3(int a);
CV_EXPORTS_W void bindTest4(int a, CV_IN_OUT Point& pt);
CV_EXPORTS_W void bindTest5(int a, CV_IN_OUT Point& pt, CV_OUT int* x);
CV_EXPORTS_W bool bindTest6(int a, CV_IN_OUT Point& pt, CV_OUT int* x);

CV_EXPORTS_W double bindTest_overload(Point a, Point b, double c);
CV_EXPORTS_W double bindTest_overload(RotatedRect a);

CV_EXPORTS_W void bindTest_InOut_Mat(CV_IN_OUT Mat& a);
CV_EXPORTS_W void bindTest_InOut_bool(CV_IN_OUT bool& a);
CV_EXPORTS_W void bindTest_InOut_uchar(CV_IN_OUT uchar& a);
CV_EXPORTS_W void bindTest_InOut_int(CV_IN_OUT int& a);
CV_EXPORTS_W void bindTest_Out_intp(CV_OUT int* a);
CV_EXPORTS_W void bindTest_InOut_size_t(CV_IN_OUT size_t& a);
CV_EXPORTS_W void bindTest_InOut_float(CV_IN_OUT float& a);
CV_EXPORTS_W void bindTest_InOut_double(CV_IN_OUT double& a);
CV_EXPORTS_W void bindTest_InOut_Size(CV_IN_OUT Size& a);
CV_EXPORTS_W void bindTest_InOut_Size2f(CV_IN_OUT Size2f& a);
CV_EXPORTS_W void bindTest_InOut_Point(CV_IN_OUT Point& a);
CV_EXPORTS_W void bindTest_InOut_Point2f(CV_IN_OUT Point2f& a);
CV_EXPORTS_W void bindTest_InOut_RotatedRect(CV_IN_OUT RotatedRect& a);
CV_EXPORTS_W void bindTest_InOut_vector_Point(CV_IN_OUT std::vector<Point>& a);

} // cv

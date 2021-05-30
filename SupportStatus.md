# ROpenCV2: Support Status

Complete list of supported functions is on [Github Wiki page](https://github.com/wagavulin/ropencv2/wiki/Supported-functions).

## Functions

Support functions which satisfy all the conditions below:

* Global function (=not class member function)
* Directly under `cv` namespace
* Number of mandatory arguments < 10
* Number of optional arguments < 10
* All input arguments' types are supported (see the list below)
* All output arguments' and retval types are supported (see the list below)

## Classes

`cv::Mat` class is supported with manual binding, but only a new functions and public members are supported.

* `cv::Mat::cols`
* `cv::Mat::rows`
* `cv::Mat::channels`

All other classes are not supported.

## enums and constants

All enums and constants directly under `cv` namespace are supported.

## Supported types

### Input argument

* `cv::Mat`
* `cv::Scalar`
* `bool`
* `int`
* `double`
* `cv::String`
* `cv::Size`
* `cv::Rect`
* `Point`

### Output argument and return value

* `void`
* `cv::Mat`
* `bool`
* `int`
* `Point`

#!/usr/bin/env python

import os
import sys
import typing

import hdr_parser_wrapper
from hdr_parser_wrapper import (CvApi, CvArg, CvEnum, CvEnumerator, CvProp, CvFunc,
                                CvKlass, CvNamespace, CvVariant)

g_out_dir = "./autogen"

g_supported_rettypes = [
    "", # constructor
    "void",
    "bool",
    "char",
    "uchar",
    "int",
    "size_t",
    "float",
    "double",
    "std.string",
    "cv.String",
    "cv.Mat",
    "cv.Point",
    "cv.Point2d",
    "cv.Rect",
    "cv.RotatedRect",
    "cv.Scalar",
    "cv.Size",
    "std.vector<uchar>",
    "std.vector<int>",
    "std.vector<float>",
    "std.vector<std.string>",
    "std.vector<cv.String>",
    "std.vector<cv.Mat>",
    "std.vector<cv.Point2f>",
    "std.vector<cv.Size>",
]
g_supported_argtypes = [
    "bool",
    "char",
    "uchar",
    "int",
    "int*",
    "size_t",
    "float",
    "double",
    "double*",
    "c_string",
    "std.string",
    "cv.String",
    "cv.Mat",
    "cv.Point",
    "cv.Point*",
    "cv.Point2d",
    "cv.Point2f",
    "cv.Point2f*",
    "cv.Rect",
    "cv.Rect*",
    "cv.RotatedRect",
    "cv.Scalar",
    "cv.Size",
    "cv.Size2f",
    "cv.Size2i",
    "std.vector<char>",
    "std.vector<uchar>",
    "std.vector<int>",
    "std.vector<float>",
    "std.vector<double>",
    "std.vector<std.string>",
    "std.vector<cv.String>",
    "std.vector<cv.Mat>",
    "std.vector<cv.Point>",
    "std.vector<cv.Point2f>",
    "std.vector<cv.Rect>",
    "std.vector<cv.RotatedRect>",
    "std.vector<cv.Size>",
    #"std.vector<cv.>",
    "std.vector<std.vector<int>>",
    "std.vector<std.vector<cv.Point>>",
    "std.vector<std.vector<cv.Point2f>>",
    #"std.vector<std.vector<>>",
]

g_unsupported_argtypes = [
    "cv.flann.SearchParams",
]

g_supported_enum_types = []
g_supported_class_types = []

def check_rettype_supported(rettype_qname:str):
    if rettype_qname in g_supported_rettypes:
        return True
    if rettype_qname in g_supported_enum_types:
        return True
    if rettype_qname in g_supported_class_types:
        return True
    if rettype_qname.startswith("Ptr<"):
        return True
    return False

def check_argtype_supported(argtype_qname:str):
    if argtype_qname in g_unsupported_argtypes:
        return False
    if argtype_qname in g_supported_argtypes:
        return True
    if argtype_qname in g_supported_enum_types:
        return True
    if argtype_qname in g_supported_class_types:
        return True
    return False

def check_func_variants_support_status(func:CvFunc) -> list[tuple[bool,str]]:
    global g_supported_rettypes, g_supported_argtypes
    ret = []
    for v in func.variants:
        supported = True
        msg = ""
        if not check_rettype_supported(v.rettype_qname):
            supported = False
            msg = f"rettype ({v.rettype_qname}) is not supported"
        for i, arg in enumerate(v.args):
            if check_argtype_supported(arg.tp_qname):
                pass # supported
            else:
                supported = False
                msg = f"arg[{i}] ({arg.tp_qname}) is not supported"
                break
        stat = (supported, msg)
        ret.append(stat)
    return ret

g_instance_used_as_retval_types = []

def check_is_constructor(cvfunc:CvFunc) -> bool:
    is_constructor = cvfunc.klass and cvfunc.klass.name.split(".")[-1] == cvfunc.name.split(".")[-1]
    return is_constructor

def gen_wrapper_func_name(func:CvFunc):
    if check_is_constructor(func):
        wrapper_func_name = "wrap_" + func.klass.name.replace(".", "_") + "_init" # "rbopencv_cv_Ns1_Ns11_Foo_init"
    else:
        wrapper_func_name = "rbopencv_" + func.name.replace(".", "_")                 # "rbopencv_cv_Ns1_Ns11_Foo_method1"
    if func.isstatic:
        wrapper_func_name += "_static"
    return wrapper_func_name

def get_namespace_of_func(func:CvFunc):
    ret = None
    if func.ns:
        ret = func.ns
    elif func.klass:
        if func.klass.ns:
            ret = func.klass.ns
        elif func.klass.klass:
            if func.klass.klass.ns:
                ret = func.klass.klass.ns
    if ret is None:
        print(f"[Error] Could not find namespace of {func.name}")
        exit(1)
    return ret

_g_abstract_classes = [
    "cv.Ns1.Ns11.SubSubI2",
    "cv.Algorithm",
    "cv.ml.ANN_MLP",
    "cv.ml.Boost",
    "cv.ml.DTrees",
    "cv.ml.EM",
    "cv.ml.KNearest",
    "cv.ml.LogisticRegression",
    "cv.ml.NormalBayesClassifier",
    "cv.ml.RTrees",
    "cv.ml.SVM",
    "cv.ml.SVMSGD",
    "cv.ml.StatModel",
    "cv.ml.TrainData",
    "cv.detail.Estimator",
    "cv.detail.ExposureCompensator",
    "cv.detail.BlocksCompensator",
    "cv.detail.BundleAdjusterBase",
    "cv.detail.FeaturesMatcher",
    "cv.detail.PairwiseSeamFinder",
    "cv.detail.SeamFinder",
    "cv.AKAZE",
    "cv.AffineFeature",
    "cv.AgastFeatureDetector",
    "cv.AlignExposures",
    "cv.AlignMTB",
    "cv.BOWTrainer",
    "cv.BRISK",
    "cv.BackgroundSubtractor",
    "cv.BackgroundSubtractorKNN",
    "cv.BackgroundSubtractorMOG2",
    "cv.BaseCascadeClassifier",
    "cv.CLAHE",
    "cv.CalibrateCRF",
    "cv.CalibrateDebevec",
    "cv.CalibrateRobertson",
    "cv.DISOpticalFlow",
    "cv.DenseOpticalFlow",
    "cv.DescriptorMatcher",
    "cv.FaceDetectorYN",
    "cv.FaceRecognizerSF",
    "cv.FarnebackOpticalFlow",
    "cv.FastFeatureDetector",
    "cv.Formatter",
    "cv.GFTTDetector",
    "cv.GeneralizedHough",
    "cv.GeneralizedHoughBallard",
    "cv.GeneralizedHoughGuil",
    "cv.KAZE",
    "cv.LineSegmentDetector",
    "cv.MSER",
    "cv.MergeDebevec",
    "cv.MergeExposures",
    "cv.MergeMertens",
    "cv.MergeRobertson",
    "cv.ORB",
    "cv.QRCodeEncoder",
    "cv.SIFT",
    "cv.SimpleBlobDetector",
    "cv.SparseOpticalFlow",
    "cv.SparsePyrLKOpticalFlow",
    "cv.StereoBM",
    "cv.StereoMatcher",
    "cv.StereoSGBM",
    "cv.Tonemap",
    "cv.TonemapDrago",
    "cv.TonemapMantiuk",
    "cv.TonemapReinhard",
    "cv.Tracker",
    "cv.TrackerDaSiamRPN",
    "cv.TrackerGOTURN",
    "cv.TrackerMIL",
    "cv.TrackerNano",
    "cv.VariationalRefinement",
    "cv.WarperCreator",
    # Not abstarct, but cannot be instantiated
    "cv.dnn.TextDetectionModel",
    "cv.UMatData",
    "cv.Mat",
    # Not abstract, but cannot be instantiated because no default ctor
    "cv.DetectionBasedTracker",
]

def check_is_abstract_class(cvklass:CvKlass):
    return cvklass.name in _g_abstract_classes

def generate_accessor_wrapper_impl(f:typing.TextIO, klass:CvKlass, prop:CvProp, log_f):
    us_klass_name = klass.name.replace(".", "_")     # underscored class name: cv_Ns1_Ns11_Foo
    c_klass = f'c{us_klass_name}'                    # ccv_Ns1_Ns11_Foo (for VALUE name)
    getter_wrapper_func_name = f"wrap_{us_klass_name}_{prop.name}_getter"
    setter_wrapper_func_name = f"wrap_{us_klass_name}_{prop.name}_setter"
    tp_cpp_qname = prop.tp_qname.replace(".", "::")
    f.write(f'static VALUE {getter_wrapper_func_name}(VALUE self){{\n')
    #f.write(f'    printf("[%s]\\n", __func__);\n')
    f.write(f'    const {tp_cpp_qname}& raw_retval = get_{us_klass_name}(self)->{prop.name};\n')
    f.write(f'    VALUE value_retval = rbopencv_from(raw_retval);\n')
    f.write(f'    return value_retval;\n')
    f.write(f'}}\n')
    f.write(f'\n')
    f.write(f'static VALUE {setter_wrapper_func_name}(VALUE self, VALUE value_{prop.name}){{\n')
    #f.write(f'    printf("[%s]\\n", __func__);\n')
    f.write(f'    {tp_cpp_qname} raw_{prop.name};\n')
    f.write(f'    bool conv_arg_ok = rbopencv_to(value_{prop.name}, raw_{prop.name});\n')
    f.write(f'    if (!conv_arg_ok) {{\n')
    f.write(f"        std::string err_msg{{\" can't parse '{prop.name}'\"}};\n")
    f.write(f'        rbPopulateArgumentConversionErrors(err_msg);\n')
    f.write(f'        rbRaiseCVOverloadException("{klass.name}.{prop.name}");\n')
    f.write(f'        return Qnil;\n')
    f.write(f'    }}\n')
    f.write(f'    get_{us_klass_name}(self)->{prop.name} = raw_{prop.name};\n')
    f.write(f'    return Qnil;\n')
    f.write(f'}}\n')
    f.write(f'\n')

def generate_wrapper_function_impl(f:typing.TextIO, cvfunc:CvFunc, log_f):
    support_stats = check_func_variants_support_status(cvfunc)
    num_supported_variants = 0
    supported_vars:list[CvVariant] = []
    for i in range(len(cvfunc.variants)):
        stat = support_stats[i]
        if stat[0]:
            num_supported_variants += 1
            supported_vars.append(cvfunc.variants[i])
    if num_supported_variants == 0:
        return
    func_cpp_basename = cvfunc.name_cpp.split(".")[-1]
    supported_vars = sorted(supported_vars, reverse=True, key=lambda var: len(var.args))
    wrapper_func_name = gen_wrapper_func_name(cvfunc)
    is_constructor = check_is_constructor(cvfunc)
    is_instance_method = cvfunc.klass and cvfunc.isstatic == False
    if is_constructor:
        print(f'static VALUE {wrapper_func_name}(int argc, VALUE *argv, VALUE self)', file=f)
    else:
        print(f'static VALUE {wrapper_func_name}(int argc, VALUE *argv, VALUE klass)', file=f)
    print(f'{{', file=f)
    ### gen-func-wrapper-start ###
    ns = get_namespace_of_func(cvfunc)
    f.write(f"    using namespace {ns.name.replace('.', '::')};\n\n")
    f.write( "    VALUE h = rb_check_hash_type(argv[argc-1]);\n")
    f.write( "    if (!NIL_P(h)) {\n        --argc;\n    }\n")
    f.write( "    int arity = rb_check_arity(argc, 0, UNLIMITED_ARGUMENTS);\n")
    f.write( "\n")
    f.write( "    std::string err_msg;\n")
    for var_idx, v in enumerate(supported_vars):
        # variables for raw variable definitions (rvd)
        rvd_raw_types:list[str] = []
        rvd_raw_var_names:list[str] = []
        rvd_raw_default_values:list[str] = []
        # variables for value variable definitions (vvd)
        vvd_names:list[str] = []
        vvd_value_var_names:list[str] = []
        vvd_corr_raw_var_names:list[str] = []
        # variables for rb_scan_args() (rsa)
        rsa_num_mandatory_args = 0
        rsa_num_optional_args = 0
        # variables for C++ API calling (cac)
        cac_args:list[str] = []
        cac_raw_out_var_names:list[str] = []
        # variables for return values handling (rh)
        rh_raw_var_names:list[str] = []

        ordered_args:list[CvArg] = []
        tmp_mandatory_args:list[CvArg] = []
        tmp_out_pyin_args:list[CvArg] = []
        tmp_optional_args:list[CvArg] = []
        for a in v.args:
            if a.inputarg == False and a.outputarg == True and a.defval == "":
                tmp_out_pyin_args.append(a)
            else:
                if a.defval:
                    tmp_optional_args.append(a)
                else:
                    tmp_mandatory_args.append(a)
        ordered_args.extend(tmp_mandatory_args)
        ordered_args.extend(tmp_out_pyin_args)
        ordered_args.extend(tmp_optional_args)

        # Collect values
        if v.rettype and not v.rettype == "void":
            rh_raw_var_names.append("raw_retval")
        # C++ API calling is based on original arguments order
        for a in v.args:
            if a.inputarg == False and a.outputarg == True and a.tp[-1] == "*":
                # "&raw_x" is used when calling C++ API.
                cac_args.append(f"&raw_{a.name}")
            else:
                if a.tp == "c_string":
                    cac_args.append(f"raw_{a.name}.c_str()")
                else:
                    cac_args.append(f"raw_{a.name}")
        # Other process is based on ordered arguments
        for a in ordered_args:
            if a.inputarg == False and a.outputarg == True and a.tp[-1] == "*":
                # If the arg is pointer and for OUT arg (e.g. int* x),
                # it's declared as non-pointer (int raw_x).
                rvd_raw_types.append(a.tp[:-1])
            else:
                if a.tp == "c_string":
                    rvd_raw_types.append("std::string")
                else:
                    rvd_raw_types.append(a.tp_qname.replace(".", "::"))
            rvd_raw_var_names.append(f"raw_{a.name}")
            if not a.tp[-1] == "*":
                # If pointer arg has default value, it's always 0 or nullptr (Is this correct?)
                #   => No. cv.Cuda.GpuMat.GpuMat takes GpuAllocator*=GpuMat::defaultAllocator() [TBD]
                # It should not be used as default value to avoid error (For example, Point raw_point = 0;)
                rvd_raw_default_values.append(a.defval)
            else:
                rvd_raw_default_values.append("")
            if a.inputarg:
                vvd_names.append(a.name)
                vvd_value_var_names.append(f"value_{a.name}")
                vvd_corr_raw_var_names.append(f"raw_{a.name}")
                if a.defval:
                    rsa_num_optional_args += 1
                else:
                    rsa_num_mandatory_args += 1
            else:
                if a.outputarg == True:
                    vvd_names.append(a.name)
            if a.outputarg:
                cac_raw_out_var_names.append(f"raw_{a.name}")
                rh_raw_var_names.append(f"raw_{a.name}")

        # Generate raw variable definitions (rvd)
        f.write(f"    if (arity >= {rsa_num_mandatory_args}) {{\n")
        for i in range(len(rvd_raw_types)):
            if rvd_raw_default_values[i]:
                f.write(f"        {rvd_raw_types[i]} {rvd_raw_var_names[i]} = {rvd_raw_default_values[i]};\n")
            else:
                f.write(f"        {rvd_raw_types[i]} {rvd_raw_var_names[i]}; // {v.args[i].tp_qname}\n")
        f.write("\n")

        # Generate value variable definitions (vvd)
        for i in range(len(vvd_value_var_names)):
            f.write(f"        VALUE {vvd_value_var_names[i]};\n")
        f.write("\n")

        # Call rb_scan_args() (rsa)
        rsa_scan_args_fmt = f"{rsa_num_mandatory_args}{rsa_num_optional_args}"
        f.write(f"        int scan_ret = rb_scan_args(argc, argv, \"{rsa_scan_args_fmt}\"")
        for i in range(len(vvd_value_var_names)):
            f.write(f", &{vvd_value_var_names[i]}")
        f.write(");\n")

        # Check the result of rb_scan_args()
        f.write("        bool conv_args_ok = true;\n")
        for i in range(rsa_num_mandatory_args):
            f.write(f"        conv_args_ok &= rbopencv_to({vvd_value_var_names[i]}, {vvd_corr_raw_var_names[i]});\n")
            f.write(f"        if (!conv_args_ok) {{\n")
            f.write(f"            err_msg = \" can't parse '{vvd_names[i]}'\";\n")
            f.write(f"        }}\n")
        rsa_idx_optional_start = rsa_num_mandatory_args
        rsa_idx_optional_end = rsa_num_mandatory_args + rsa_num_optional_args - 1
        if rsa_num_optional_args >= 1:
            for i in range(rsa_idx_optional_start, rsa_idx_optional_end+1):
                f.write(f"        if (scan_ret >= {i+1}) {{\n")
                f.write(f"            conv_args_ok &= rbopencv_to({vvd_value_var_names[i]}, {vvd_corr_raw_var_names[i]});\n")
                f.write(f"            if (!conv_args_ok) {{\n")
                f.write(f"                err_msg = \" can't parse '{vvd_names[i]}'\";\n")
                f.write(f"            }}\n")
                f.write(f"        }}\n")
        f.write("\n")

        # Call rb_get_kwargs() for keyword arguments
        if rsa_num_optional_args >= 1:
            f.write(f"        if (!NIL_P(h)) {{\n")
            f.write(f"            ID table[{rsa_num_optional_args}];\n")
            f.write(f"            VALUE values[{rsa_num_optional_args}];\n")
            for i in range(rsa_idx_optional_start, rsa_idx_optional_end+1):
                j = i - rsa_idx_optional_start
                f.write(f"            table[{j}] = rb_intern(\"{vvd_names[i]}\");\n")
            f.write(f"            rb_get_kwargs(h, table, 0, {rsa_num_optional_args}, values);\n")

            # Check the result of rb_get_kwargs()
            for i in range(rsa_idx_optional_start, rsa_idx_optional_end+1):
                j = i - rsa_idx_optional_start
                f.write(f"            if (values[{j}] == Qundef) {{\n")
                f.write(f"                // Do nothing. Already set by arg w/o keyword, or use {vvd_corr_raw_var_names[i]} default value\n")
                f.write(f"            }} else {{\n")
                f.write(f"                conv_args_ok &= rbopencv_to(values[{j}], {vvd_corr_raw_var_names[i]});\n")
                f.write(f"                if (!conv_args_ok) {{\n")
                f.write(f"                    err_msg = \"Can't parse '{vvd_names[i]}'\";\n")
                f.write(f"                }}\n")
                f.write(f"            }}\n")
            f.write(f"        }}\n")

        # Call C++ API if arguments are ready
        f.write("        if (conv_args_ok) {\n")
        is_ret_class_instance = False
        if is_constructor:
            klassname_us = cvfunc.klass.name.replace(".", "_")
            wrap_struct = f"Wrap_{klassname_us}"
            data_type_instance = f"{klassname_us}_type"
            ctor_cname = cvfunc.klass.name.replace(".", '::')
            f.write(f"            struct {wrap_struct} *ptr;\n")
            f.write(f"            TypedData_Get_Struct(self, struct {wrap_struct}, &{data_type_instance}, ptr);\n")
            args_str = ", ".join(cac_args)
            f.write(f"            ptr->v = new {ctor_cname}({args_str});\n")
        else:
            func_cpp_qname = cvfunc.name_cpp.replace(".", "::")
            rettype_cpp_qname = v.rettype_qname.replace(".", "::")
            if v.rettype_qname in api.cvklasses.keys() and not v.rettype_qname == "cv.Mat":
                is_ret_class_instance = True
                if is_instance_method:
                    klassname_us = cvfunc.klass.name.replace(".", "_")
                    f.write(f"            cv::Ptr<{rettype_cpp_qname}> p = new {rettype_cpp_qname}{{get_{klassname_us}(klass)->{func_cpp_basename}")
                    pass
                else:
                    f.write(f"            cv::Ptr<{rettype_cpp_qname}> p = new {rettype_cpp_qname}{{{func_cpp_qname}")
                f.write(f"({', '.join(cac_args)})}};\n")
                f.write(f"            VALUE value_retval = rbopencv_from(p);\n")
            else:
                if v.rettype == "void":
                    f.write(f"            ")
                else:
                    f.write(f"            {rettype_cpp_qname} raw_retval;\n")
                    f.write(f"            raw_retval = ")
                if is_instance_method:
                    klassname_us = cvfunc.klass.name.replace(".", "_")
                    f.write(f"get_{klassname_us}(klass)->{func_cpp_basename}")
                else:              # call global function
                    f.write(f"{func_cpp_qname}")
                f.write(f"({', '.join(cac_args)});\n")
        # Convert the return value(s)
        num_ruby_retvals = len(rh_raw_var_names)
        if is_ret_class_instance:
            f.write(f"            return value_retval;\n")
        elif num_ruby_retvals == 0:
            # If no retvals for ruby, return Qnil
            f.write(f"            return Qnil;\n")
        elif num_ruby_retvals == 1:
            # If 1 ruby retval, return it as VALUE
            retval_raw_var_name = rh_raw_var_names[0]
            f.write(f"            VALUE value_retval = rbopencv_from({retval_raw_var_name});\n")
            f.write(f"            return value_retval;\n")
        else:
            # If 2 or more ruby retvals, return as array
            f.write(f"            VALUE value_retval_array = rb_ary_new3({num_ruby_retvals}")
            for raw_var_name in rh_raw_var_names:
                f.write(f", rbopencv_from({raw_var_name})")
            f.write(");\n")
            f.write(f"            return value_retval_array;\n")
        f.write("        } else {\n")
        f.write("            rbPopulateArgumentConversionErrors(err_msg);\n")
        f.write("        }\n")
        f.write("    }\n")
    f.write(f"    rbRaiseCVOverloadException(\"{cvfunc.name}\");\n")
    f.write("    return Qnil;\n")
    f.write("}\n\n")

def generate_code(api:CvApi):
    sorted_namespaces:list[CvNamespace] = []
    for _, ns in api.cvnamespaces.items():
        sorted_namespaces.append(ns)
    sorted(sorted_namespaces, key=lambda ns: ns.name)
    sorted_klasses:list[CvKlass] = []
    for _, klass in api.cvklasses.items():
        sorted_klasses.append(klass)
    sorted(sorted_klasses, key=lambda klass: klass.name)

    with open(f"{g_out_dir}/rbopencv_namespaceregistration.hpp", "w") as f:
        for ns in sorted_namespaces:
            nsname_us = ns.name.replace(".", "_")
            print(f"init_submodule(\"{ns.name}\", methods_{nsname_us}, consts_{nsname_us});", file=f)
    with open(f"{g_out_dir}/rbopencv_modules_content.hpp", "w") as f:
        for ns in sorted_namespaces:
            name_us = ns.name.replace(".", "_")
            print(f"static MethodDef methods_{name_us}[] = {{", file=f)
            for cvfunc in ns.funcs:
                funcnames_rb = set()
                support_stats = check_func_variants_support_status(cvfunc)
                for i in range(len(cvfunc.variants)):
                    if support_stats[i][0]:
                        if cvfunc.variants[i].wrap_as:
                            funcname_rb = cvfunc.variants[i].wrap_as
                        else:
                            funcname_rb = cvfunc.name.split(".")[-1]
                        funcnames_rb.add(funcname_rb)
                wrapper_func_name = gen_wrapper_func_name(cvfunc)
                for funcname_rb in funcnames_rb:
                    print('    {"%s", %s},' % (funcname_rb, wrapper_func_name), file=f)
            print(f"    {{NULL, NULL}}", file=f)
            print(f"}};", file=f)
            print(f"static ConstDef consts_{name_us}[] = {{", file=f)
            for cvenum in ns.enums:
                if cvenum.isscoped:
                    for v in cvenum.values:
                        def_name = "_".join(v.name.split(".")[-2:])
                        def_value = v.name.replace(".", "::")
                        print('    {"%s", static_cast<long>(%s)},' % (def_name, def_value), file=f)
                else:
                    for v in cvenum.values:
                        def_name = v.name.split(".")[-1]
                        def_value = v.name.replace(".", "::")
                        print('    {"%s", static_cast<long>(%s)},' % (def_name, def_value), file=f)
            for cvklass in ns.klasses:
                for cvenum in cvklass.enums:
                    for v in cvenum.values:
                        def_name = "_".join(v.name.split(".")[-2:])
                        def_value = v.name.replace(".", "::")
                        print('    {"%s", static_cast<long>(%s)},' % (def_name, def_value), file=f)
            print(f"    {{NULL, 0}}", file=f)
            print(f"}};\n", file=f)
    with (open(f"{g_out_dir}/rbopencv_classregistration.hpp", "w") as fcr,
          open(f"{g_out_dir}/rbopencv_wrapclass.hpp", "w") as fwc):
        for klass in sorted_klasses:
            if klass.name == "cv.Mat":
                continue
            def get_parent_mod_name(klass:CvKlass) -> str:
                if klass.ns:
                    mod_name_raw = klass.ns.name
                elif klass.klass:
                    mod_name_raw = klass.klass.ns.name
                else:
                    mod_name_raw = "" # NotReached
                strs = mod_name_raw.split(".")
                if strs[0] == "cv":
                    strs[0] = "CV2"
                for i in range(1, len(strs)):
                    strs[i] = strs[i].capitalize()
                return "_".join(strs)
            # Example: cv.Ns1.Ns11.Foo class
            parent_mod_name = get_parent_mod_name(klass)     # CV2_Ns1_Ns11
            us_klass_name = klass.name.replace(".", "_")     # underscored class name: cv_Ns1_Ns11_Foo
            c_klass = f'c{us_klass_name}'                    # ccv_Ns1_Ns11_Foo (for VALUE name)
            cvrb_klass_basename = klass.name.split(".")[-1]  # Foo
            wrap_struct = f"struct Wrap_{us_klass_name}"     # struct Wrap_cv_Ns1_Ns11_Foo
            qname = klass.name.replace(".", "::")            # "cv::Ns1::Ns11::Foo"
            isabstract = check_is_abstract_class(klass)
            # Write rbopenv_classregistration.hpp
            print(f"{{", file=fcr)
            print(f"    VALUE parent_mod = get_parent_module_by_wname(mCV2, \"{parent_mod_name}\");", file=fcr)
            print(f'    {c_klass} = rb_define_class_under(parent_mod, "{cvrb_klass_basename}", rb_cObject);', file=fcr)
            print(f"    rb_define_alloc_func({c_klass}, wrap_{us_klass_name}_alloc);", file=fcr)
            if not isabstract:
                has_ctor = False
                num_supported_ctor_variants = 0
                for func in klass.funcs:
                    if check_is_constructor(func):
                        has_ctor = True
                        ctor_stats = check_func_variants_support_status(func)
                        for stat in ctor_stats:
                            if stat[0]:
                                num_supported_ctor_variants += 1
                if has_ctor == False or num_supported_ctor_variants >= 1:
                    print(f'    rb_define_private_method({c_klass}, "initialize", RUBY_METHOD_FUNC(wrap_{klass.name.replace(".", "_")}_init), -1);', file=fcr)
            for prop in klass.props:
                getter_wrapper_func_name = f"wrap_{us_klass_name}_{prop.name}_getter"
                setter_wrapper_func_name = f"wrap_{us_klass_name}_{prop.name}_setter"
                print(f'    rb_define_method({c_klass}, "{prop.name}", RUBY_METHOD_FUNC({getter_wrapper_func_name}), 0);', file=fcr)
                print(f'    rb_define_method({c_klass}, "{prop.name}=", RUBY_METHOD_FUNC({setter_wrapper_func_name}), 1);', file=fcr)
            for func in klass.funcs:
                funcnames_rb = set()
                support_stats = check_func_variants_support_status(func)
                for i in range(len(func.variants)):
                    if support_stats[i][0]:
                        if func.variants[i].wrap_as:
                            funcname_rb = func.variants[i].wrap_as
                        else:
                            funcname_rb = func.name.split(".")[-1]
                        funcnames_rb.add(funcname_rb)
                wrapper_func_name = gen_wrapper_func_name(func)
                for funcname_rb in funcnames_rb:
                    if func.isstatic:
                        print(f"    rb_define_singleton_method({c_klass}, \"{funcname_rb}\", RUBY_METHOD_FUNC({wrapper_func_name}), -1);", file=fcr)
                    else:
                        print(f'    rb_define_method({c_klass}, "{funcname_rb}", RUBY_METHOD_FUNC({wrapper_func_name}), -1);', file=fcr)
            print(f"}}", file=fcr)

            # Write rbopenv_wrapclass.hpp
            fwc.write(f"static VALUE {c_klass};\n")
            fwc.write(f"{wrap_struct} {{\n")
            fwc.write(f"    Ptr<{qname}> v;\n")
            fwc.write(f"}};\n")
            fwc.write(f"static void wrap_{us_klass_name}_free({wrap_struct}* ptr){{\n")
            fwc.write(f"    ptr->v.reset();\n")
            fwc.write(f"    ruby_xfree(ptr);\n")
            fwc.write(f"}};\n")
            fwc.write(f"static const rb_data_type_t {us_klass_name}_type {{\n")
            fwc.write(f"    \"{c_klass}\",\n")
            fwc.write(f"    {{NULL, reinterpret_cast<RUBY_DATA_FUNC>(wrap_{us_klass_name}_free), NULL}},\n")
            fwc.write(f"    NULL, NULL,\n")
            fwc.write(f"    RUBY_TYPED_FREE_IMMEDIATELY\n")
            fwc.write(f"}};\n")
            fwc.write(f"static Ptr<{qname}> get_{us_klass_name}(VALUE self){{\n")
            fwc.write(f"    {wrap_struct}* ptr;\n")
            fwc.write(f"    TypedData_Get_Struct(self, {wrap_struct}, &{us_klass_name}_type, ptr);\n")
            fwc.write(f"    return ptr->v;\n")
            fwc.write(f"}}\n")
            fwc.write(f"static VALUE wrap_{us_klass_name}_alloc(VALUE klass){{\n")
            fwc.write(f"    {wrap_struct}* ptr = nullptr;\n")
            fwc.write(f"    VALUE ret = TypedData_Make_Struct(klass, {wrap_struct}, &{us_klass_name}_type, ptr);\n")
            fwc.write(f"    return ret;\n")
            fwc.write(f"}}\n")
            fwc.write(f"template<>\n")
            fwc.write(f"VALUE rbopencv_from(const Ptr<{qname}>& value){{\n")
            fwc.write(f"    TRACE_PRINTF(\"[rbopencv_from Ptr<{qname}>]\\n\");\n")
            fwc.write(f"    {wrap_struct} *ptr;\n")
            fwc.write(f"    VALUE a = wrap_{us_klass_name}_alloc({c_klass});\n")
            fwc.write(f"    TypedData_Get_Struct(a, {wrap_struct}, &{us_klass_name}_type, ptr);\n")
            fwc.write(f"    ptr->v = value;\n")
            fwc.write(f"    return a;\n")
            fwc.write(f"}}\n")
            if isabstract:
                continue
            if klass.name in g_instance_used_as_retval_types:
                fwc.write(f"template<>\n")
                fwc.write(f"bool rbopencv_to(VALUE o, {qname}& value){{\n")
                fwc.write(f"    TRACE_PRINTF(\"[rbopencv_to {qname}]\\n\");\n")
                fwc.write(f"    Ptr<{qname}> p = get_{us_klass_name}(o);\n")
                fwc.write(f"    value = *p;\n")
                fwc.write(f"    return true;\n")
                fwc.write(f"}}\n")
            has_ctor = False
            num_supported_ctor_variants = 0
            for func in klass.funcs:
                if check_is_constructor(func):
                    has_ctor = True
                    stats = check_func_variants_support_status(func)
                    for stat in stats:
                        if stat[0]:
                            num_supported_ctor_variants += 1
            if has_ctor == False or num_supported_ctor_variants >= 1:
                fwc.write(f"static VALUE wrap_{us_klass_name}_init(int argc, VALUE *argv, VALUE self); // implemented in rbopencv_funcs.hpp\n\n")

    with open(f"{g_out_dir}/rbopencv_enum_converter.hpp", "w") as f:
        for _, cvenum in api.cvenums.items():
            if cvenum.name.endswith(".<unnamed>"):
                continue
            qname = cvenum.name.replace(".", "::")
            f.write(f"template<>\n")
            f.write(f"bool rbopencv_to(VALUE obj, {qname}& value){{\n")
            f.write(f"    TRACE_PRINTF(\"[rbopencv_to {qname}]\\n\");\n")
            f.write(f"    if (!FIXNUM_P(obj))\n")
            f.write(f"        return false;\n")
            f.write(f"    int tmp = FIX2INT(obj);\n")
            f.write(f"    value = static_cast<{qname}>(tmp);\n")
            f.write(f"    return true;\n")
            f.write(f"}}\n")
            f.write(f"template<>\n")
            f.write(f"VALUE rbopencv_from(const {qname}& value){{\n")
            f.write(f"    TRACE_PRINTF(\"[rbopencv_from {qname}] %d\", value);\n")
            f.write(f"    return INT2NUM(static_cast<int>(value));\n")
            f.write(f"}}\n")

    with (open(f"{g_out_dir}/rbopencv_funcs.hpp", "w") as f,
          open("./autogen/log-support-status.csv", "w") as log_f):
        print("Support_Status,Function_Name,Variant_Number,Retval_Type,Argument_Types,Reason", file=log_f)
        for _, cvfunc in api.cvfuncs.items():
            support_stats = check_func_variants_support_status(cvfunc)
            num_supported_variants = 0
            supported_vars:list[CvVariant] = []
            for i in range(len(cvfunc.variants)):
                var = cvfunc.variants[i]
                stat = support_stats[i]
                if stat[0]:
                    num_supported_variants += 1
                    supported_vars.append(cvfunc.variants[i])
                    gen_stat = "Generate"
                else:
                    gen_stat = "Skip"
                arg_tps = [arg.tp for arg in var.args]
                str_arg_tps = ",".join(arg_tps)
                print(f'{gen_stat},{cvfunc.name},{i},{var.rettype},"{str_arg_tps}"', file=log_f, end="")
                print(f',"{stat[1]}"', file=log_f)
            if num_supported_variants == 0:
                continue
            generate_wrapper_function_impl(f, cvfunc, log_f)
        for klass in sorted_klasses:
            for prop in klass.props:
                generate_accessor_wrapper_impl(f, klass, prop, log_f)
        for klass in sorted_klasses:
            has_ctor = False
            for func in klass.funcs:
                if check_is_constructor(func):
                    has_ctor = True
                    break
            isabstract = check_is_abstract_class(klass)
            if (not has_ctor) and (not isabstract):
                # If ctor is not defined, ClassName_init() shall be generated to support default ctor
                klass_basename = klass.name.split(".")[-1]
                ctor_name = f"{klass.name}.{klass_basename}"
                ctor_var = CvVariant(wrap_as=None, isconst=False, isvirtual=False, ispurevirtual=False, rettype="",
                    rettype_qname="", args=[])
                dummy_func = CvFunc(filename="(dummy)", ns=klass.ns, klass=klass, name_cpp=ctor_name, name=ctor_name,
                    isstatic=False, variants=[ctor_var])
                generate_wrapper_function_impl(f, dummy_func, log_f)

headers_txt = "./headers.txt"
if len(sys.argv) == 2:
    headers_txt = sys.argv[1]
headers = []
with open(headers_txt) as f:
    for line in f:
        line = line.strip()
        if line.startswith("#"):
            continue
        headers.append(line.split("#")[0].strip())

api = hdr_parser_wrapper.parse_headers(headers, g_out_dir)
os.makedirs(g_out_dir, exist_ok=True)
with open(f"{g_out_dir}/rbopencv_include.hpp", "w") as f:
    for hdr in headers:
        print(f'#include "{hdr}"', file=f)
for _, cvenum in api.cvenums.items():
    g_supported_enum_types.append(cvenum.name)
for _, cvklass in api.cvklasses.items():
    g_supported_class_types.append(cvklass.name)
tmp_instance_used_as_retval_types = set()
for _, cvfunc in api.cvfuncs.items():
    for var in cvfunc.variants:
        if var.rettype_qname in api.cvklasses.keys():
            tmp_instance_used_as_retval_types.add(var.rettype_qname)
g_instance_used_as_retval_types = list(tmp_instance_used_as_retval_types)
generate_code(api)

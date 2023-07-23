#!/usr/bin/env python

import os
import sys
import typing

import hdr_parser_wrapper
from hdr_parser_wrapper import (CvApi, CvArg, CvEnum, CvEnumerator, CvFunc,
                                CvKlass, CvNamespace, CvVariant)

out_dir = "./autogen"

g_supported_rettypes = [
    "void",
    "bool,"
    "char",
    "int",
    "size_t",
    "float",
    "double",
    "cv.String",
    "cv.Mat",
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
    "string",
    "cv.String",
    "cv.Mat",
    "cv.Point",
    "cv.Point*",
]

def check_func_variants_support_status(func:CvFunc) -> list[tuple[bool,str]]:
    global g_supported_rettypes, g_supported_argtypes
    ret = []
    for v in func.variants:
        supported = True
        msg = ""
        if not v.rettype_qname in g_supported_rettypes:
            supported = False
            msg = f"rettype ({v.rettype_qname}) is not supported"
        for i, arg in enumerate(v.args):
            if arg.tp_qname in g_supported_argtypes:
                pass # supported
            else:
                supported = False
                msg = f"arg[{i}] ({arg.tp_qname}) is not supported"
        stat = (supported, msg)
        ret.append(stat)
    return ret

def gen_wrapper_func_name(func:CvFunc):
    wrapper_func_name = "rbopencv_" + func.name.replace(".", "_")
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

def generate_wrapper_function_impl(f:typing.TextIO, cvfunc:CvFunc, log_f):
    support_stats = check_func_variants_support_status(cvfunc)
    num_supported_variants = 0
    supported_vars:list[CvVariant] = []
    for i in range(len(cvfunc.variants)):
        stat = support_stats[i]
        if stat[0]:
            num_supported_variants += 1
            supported_vars.append(cvfunc.variants[i])
        else:
            print(f"Skip {cvfunc.name} {stat[1]}", file=log_f)
    if num_supported_variants == 0:
        return
    print(f"generate wrapper of {cvfunc.name}", file=log_f)
    supported_vars = sorted(supported_vars, reverse=True, key=lambda var: len(var.args))
    wrapper_func_name = gen_wrapper_func_name(cvfunc)
    is_constructor = cvfunc.klass and cvfunc.klass.name.split(".")[-1] == cvfunc.name.split(".")[-1] and cvfunc.rettype == ""
    is_instance_method = cvfunc.klass and cvfunc.isstatic == False
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
                    rvd_raw_types.append(a.tp)
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
                    vvd_value_var_names.append(f"value_{a.name}")
                    vvd_corr_raw_var_names.append(f"raw_{a.name}")
                    rsa_num_optional_args += 1
            if a.outputarg:
                cac_raw_out_var_names.append(f"raw_{a.name}")
                rh_raw_var_names.append(f"raw_{a.name}")

        # Generate raw variable definitions (rvd)
        f.write(f"    if (arity >= {rsa_num_mandatory_args}) {{\n")
        for i in range(len(rvd_raw_types)):
            if rvd_raw_default_values[i]:
                f.write(f"        {rvd_raw_types[i]} {rvd_raw_var_names[i]} = {rvd_raw_default_values[i]};\n")
            else:
                f.write(f"        {rvd_raw_types[i]} {rvd_raw_var_names[i]};\n")
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
        if is_constructor:
            klassname_us = cvfunc.klass.name.replace(".", "_")
            wrap_struct = f"Wrap_{klassname_us}"
            data_type_instance = f"{klassname_us}_type"
            ctor_cname = cvfunc.klass.name.replace("_", '::')
            f.write(f"            struct {wrap_struct} *ptr;\n")
            f.write(f"            TypedData_Get_Struct(self, struct {wrap_struct}, &{data_type_instance}, ptr);\n")
            args_str = ", ".join(cac_args)
            f.write(f"            ptr->v = new {ctor_cname}({args_str});\n")
        else:
            if not v.rettype == "void":
                f.write(f"            {v.rettype} raw_retval;\n")
                f.write(f"            raw_retval = ")
            else:
                f.write(f"            ")
            name_cpp_dcol = cvfunc.name_cpp.replace(".", "::")
            if is_instance_method:
                klassname_us = cvfunc.klass.name.replace(".", "_")
                f.write(f"get_{klassname_us}(klass)->{name_cpp_dcol}")
            else:              # call global function
                f.write(f"{name_cpp_dcol}")
            f.write(f"({', '.join(cac_args)});\n")

        # Convert the return value(s)
        num_ruby_retvals = len(rh_raw_var_names)
        if num_ruby_retvals == 0:
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

    with open(f"{out_dir}/rbopencv_namespaceregistration.hpp", "w") as f:
        for ns in sorted_namespaces:
            nsname_us = ns.name.replace(".", "_")
            print(f"init_submodule(\"{ns.name}\", methods_{nsname_us}, consts_{nsname_us});", file=f)
    with open(f"{out_dir}/rbopencv_modules_content.hpp", "w") as f:
        for ns in sorted_namespaces:
            name_us = ns.name.replace(".", "_")
            print(f"static MethodDef methods_{name_us}[] = {{", file=f)
            for cvfunc in ns.funcs:
                support_stats = check_func_variants_support_status(cvfunc)
                num_supported_variants = 0
                for stat in support_stats:
                    if stat[0]:
                        num_supported_variants += 1
                if num_supported_variants == 0:
                    continue
                wrapper_func_name = gen_wrapper_func_name(cvfunc)
                funcname_rb = cvfunc.name.split(".")[-1]
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
    with open(f"{out_dir}/rbopencv_classregistration.hpp", "w") as f:
        for ns in sorted_namespaces:
            if ns.name == "cv":
                continue
            print(f"{{", file=f)
            wname = "_".join(ns.name.split(".")[1:])
            print(f"    VALUE parent_mod = get_parent_module_by_wname(mCV2, \"{wname}\");", file=f)
            print(f"}}", file=f)

    with open(f"{out_dir}/rbopencv_wrapclass.hpp", "w") as f:
        pass
    with open(f"{out_dir}/rbopencv_enum_converter.hpp", "w") as f:
        pass
    with open(f"{out_dir}/rbopencv_funcs.hpp", "w") as f:
        with open("./autogen/log.txt", "w") as log_f:
            for _, cvfunc in api.cvfuncs.items():
                if cvfunc.klass:
                    continue
                generate_wrapper_function_impl(f, cvfunc, log_f)

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

api = hdr_parser_wrapper.parse_headers(headers)
os.makedirs(out_dir, exist_ok=True)
with open(f"{out_dir}/rbopencv_include.hpp", "w") as f:
    for hdr in headers:
        print(f'#include "{hdr}"', file=f)
generate_code(api)

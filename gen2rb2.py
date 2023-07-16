#!/usr/bin/env python

import os
import sys
import hdr_parser_wrapper
from hdr_parser_wrapper import CvApi, CvArg, CvEnum, CvEnumerator, CvFunc, CvKlass, CvNamespace

out_dir = "./autogen"

def gen_wrapper_func_name(func:CvFunc):
    wrapper_func_name = "rbopencv_" + func.name.replace(".", "_")
    if func.isstatic:
        wrapper_func_name += "_static"
    return wrapper_func_name

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
        for _, ns in api.cvnamespaces.items():
            for cvfunc in ns.funcs:
                wrapper_func_name = gen_wrapper_func_name(cvfunc)
                print(f'static VALUE {wrapper_func_name}(int argc, VALUE *argv, VALUE klass)', file=f)
                print(f'{{', file=f)
                print(f'    return Qnil;', file=f)
                print(f'}}', file=f)

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

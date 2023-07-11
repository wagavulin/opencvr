#!/usr/bin/env python

import os
import sys
import hdr_parser_wrapper
from hdr_parser_wrapper import CvApi, CvArg, CvEnum, CvEnumerator, CvFunc, CvKlass, CvNamespace

out_dir = "./autogen"

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
            wname = "_".join(ns.name.split(".")[1:])
            wname = ns.name.replace(".", "_")
            print(f"static MethodDef methods_{wname}[] = {{", file=f)
            print(f"    {{NULL, NULL}}", file=f)
            print(f"}};", file=f)
            print(f"static ConstDef consts_{wname}[] = {{", file=f)
            print(f"    {{NULL, 0}}", file=f)
            print(f"}};", file=f)
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
        pass

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
for _, cvns in api.cvnamespaces.items():
    print(f"NS {cvns.name}")
for _, cvklass in api.cvklasses.items():
    print(f" C {cvklass.name}")
#hdr_parser_wrapper._show_all_namespaces(api); exit(0)
os.makedirs(out_dir, exist_ok=True)
with open(f"{out_dir}/rbopencv_include.hpp", "w") as f:
    for hdr in headers:
        print(f'#include "{hdr}"', file=f)
generate_code(api)

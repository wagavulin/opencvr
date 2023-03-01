#!/usr/bin/env python

import copy
import json
import os
import re
import sys

import hdr_parser

g_logger = open("log-gen2rb.txt", "w")
g_log_processed_funcs:list["FuncInfo"] = []

def normalize_class_name(name):
    return re.sub(r"^cv\.", "", name).replace(".", "_")

def handle_ptr(tp:str) -> str:
    if tp.startswith('Ptr_'):
        tp = 'Ptr<' + "::".join(tp.split('_')[1:]) + '>'
    return tp

class ArgInfo:
    def __init__(self, arg_tuple:list):
        self.tp:str = handle_ptr(arg_tuple[0]) # type
        self.name:str = arg_tuple[1]           # name
        self.defval = arg_tuple[2]             # default value
        self.isarray:bool = False
        self.arraylen:int = 0
        self.arraycvt = None
        self.inputarg:bool = True
        self.outputarg:bool = False
        self.returnarg:bool = False
        self.isrvalueref:bool = False
        for m in arg_tuple[3]:                 # "/Ref", "/C", etc.
            if m == "/O":
                self.inputarg = False
                self.outputarg = True
                self.returnarg = True
            elif m == "/IO":
                self.inputarg = True
                self.outputarg = True
                self.returnarg = True
            elif m == "/A":
                raise ValueError("/A is not supported")
            elif m == "/CA":
                raise ValueError("/CA is not supported")
            elif m == "/RRef":
                raise ValueError("/RRef is not supported")
            else:
                print(f"unhandled tuple[3]: {m}", file=g_logger)
        self.py_inputarg:bool = False
        self.py_outputarg:bool = False

    def dump(self, depth):
        indent = "  " * depth
        print(f"{indent}tp: {self.tp}, name: {self.name}, defval: {self.defval}")
        print(f"{indent}isarray: {self.isarray}, arraylen: {self.arraylen}, arraycvt: {self.arraycvt}")
        print(f"{indent}input,output,return,rrvalue: {self.inputarg}, {self.outputarg}, {self.returnarg}, {self.isrvalueref}")

class FuncVariant:
    def __init__(self, classname:str, name:str, decl, isconstructor:bool, isphantom:bool=False):
        self.classname:str = classname
        self.name:str = name
        self.wname:str = name
        self.isconstructor = isconstructor
        self.isphantom = isphantom

        self.docstring = decl[5]

        self.rettype = decl[4] or handle_ptr(decl[1])
        if self.rettype == "void":
            self.rettype = ""
        self.args:list[ArgInfo] = []
        self.array_counters = {}
        for a in decl[3]:
            ainfo = ArgInfo(a)
            self.args.append(ainfo)

    def dump(self, depth):
        indent = "  " * depth
        print(f"{indent}classname: {self.classname}")
        print(f"{indent}name: {self.name}")
        print(f"{indent}wname: {self.wname}")
        print(f"{indent}isconstructor: {self.isconstructor}")
        print(f"{indent}isphantom: {self.isphantom}")
        print(f"{indent}docstring: len: {len(self.docstring)}")
        print(f"{indent}rettype: {self.rettype}")

class FuncInfo:
    def __init__(self, classname:str, name:str, cname:str, isconstructor:bool, namespace:str, is_static:bool):
        self.classname:str = classname
        self.name:str = name
        self.cname:str = cname
        self.isconstructor:bool = isconstructor
        self.namespace:str = namespace
        self.is_static:bool = is_static
        self.variants:list[FuncVariant] = []

    def dump(self, depth):
        indent = "  " * depth
        print(f"{indent}classname: {self.classname}")
        print(f"{indent}name: {self.name}")
        print(f"{indent}cname: {self.cname}")
        print(f"{indent}isconstructor: {self.isconstructor}")
        print(f"{indent}namespace: {self.namespace}")
        print(f"{indent}is_static: {self.is_static}")
        for i, variant in enumerate(self.variants):
            print(f"{indent}variants[{i}]")
            variant.dump(depth+1)

    def add_variant(self, decl, isphantom=False):
        self.variants.append(FuncVariant(self.classname, self.name, decl, self.isconstructor, isphantom))

    def get_wrapper_name(self):
        name = self.name
        if self.classname:
            classname = self.classname + "_"
            if "[" in name:
                name = "getelem"
        else:
            classname = ""

        if self.is_static:
            name += "_static"

        return "rbopencv_" + self.namespace.replace('.','_') + '_' + classname + name

    def get_wrapper_prototype(self):
        full_fname = self.get_wrapper_name()
        if self.isconstructor:
            raise ValueError("[TODO] constructor generation is not supported")
        if self.is_static:
            return "static VALUE %s(int argc, VALUE *argv)" % (full_fname)
        return "static VALUE %s(int argc, VALUE *argv, VALUE klass)" % (full_fname)

    def is_target_function(self) -> tuple[int, list[tuple[bool, str]]]:
        supported_rettypes = [
            "", # void
            "int",
            "Point",
        ]
        supported_argtypes = [
            "int",
            "Point",
        ]

        num_supported_variants:int = 0
        support_statuses:list[tuple[bool, str]] = []
        for v in self.variants:
            num_mandatory_args = 0
            num_optional_args = 0
            strs = self.cname.split("::")
            if not v.rettype in supported_rettypes:
                support_statuses.append((False, f"retval type is not supported: {self.variants[0].rettype}"))
                continue
            need_continue = False
            for a in v.args:
                if not a.tp in supported_argtypes:
                    support_statuses.append((False, f"input argument type is not supported: {a.name} {a.tp}"))
                    need_continue = True
                    break
                if a.defval == "":
                    num_mandatory_args += 1
                else:
                    num_optional_args += 1
                if a.py_outputarg:
                    # py_outputarg is True, it's used as return value,
                    # so rbopencv_from will be used
                    if not a.tp in supported_rettypes:
                        support_statuses.append((False, f"output argument type is not supported: {a.name} {a.tp}"))
                        need_continue = True
                        break
            if need_continue:
                continue
            if num_mandatory_args >= 10:
                support_statuses.append((False, f"too many mandatory arguments: {num_mandatory_args}"))
                continue
            if num_optional_args >= 10:
                support_statuses.append((False, f"too many optional arguments: {num_optional_args}"))
                continue
            support_statuses.append((True, ""))
            num_supported_variants += 1
        return num_supported_variants, support_statuses

    def gen_code(self, f, classes:dict[str, "ClassInfo"]) -> None:
        global g_log_processed_funcs
        self.num_supported_variants, self.support_statuses = self.is_target_function()
        g_log_processed_funcs.append(self)
        if self.num_supported_variants == 0:
            return
        proto = self.get_wrapper_prototype()
        f.write(f"%s\n{{\n" % (proto,))
        f.write(f"    using namespace %s;\n\n" % self.namespace.replace(".", "::"))
        f.write(f"    VALUE h = rb_check_hash_type(argv[argc-1]);\n")
        f.write(f"    if (!NIL_P(h)) {{\n        --argc;\n    }}\n")
        f.write(f"    int arity = rb_check_arity(argc, 0, UNLIMITED_ARGUMENTS);\n")
        f.write(f"\n")
        f.write(f"    std::string err_msg;\n")
        #f.write(f"    rbPrepareArgumentConversionErrorsStorage({self.num_supported_variants});\n")
        for var_idx, v in enumerate(self.variants):
            if not self.support_statuses[var_idx][0]:
                continue
            # variables for raw variable definitions (rvd)
            rvd_raw_types = []
            rvd_raw_var_names = []
            rvd_raw_default_values = []
            # variables for value variable definitions (vvd)
            vvd_names = []
            vvd_value_var_names = []
            vvd_corr_raw_var_names = []
            # variables for rb_scan_args() (rsa)
            rsa_num_mandatory_args = 0
            rsa_num_optional_args = 0
            # variables for C++ API calling (cac)
            cac_args = []
            cac_raw_out_var_names = []
            # variables for return values handling (rh)
            rh_raw_var_names = []

            ordered_args = []
            tmp_mandatory_args = []
            tmp_out_pyin_args = []
            tmp_optional_args = []
            for a in v.args:
                if a.inputarg == False and a.outputarg == True and a.py_inputarg == True and a.defval == "":
                    tmp_out_pyin_args.append(copy.deepcopy(a))
                else:
                    if a.defval:
                        tmp_optional_args.append(copy.deepcopy(a))
                    else:
                        tmp_mandatory_args.append(copy.deepcopy(a))
            ordered_args.extend(tmp_mandatory_args)
            ordered_args.extend(tmp_out_pyin_args)
            ordered_args.extend(tmp_optional_args)

            # Collect values
            if v.rettype:
                rh_raw_var_names.append("raw_retval")
            # C++ API calling is based on original arguments order
            for a in v.args:
                if a.inputarg == False and a.outputarg == True and a.tp[-1] == "*":
                    # "&raw_x" is used when calling C++ API.
                    cac_args.append(f"&raw_{a.name}")
                else:
                    cac_args.append(f"raw_{a.name}")
            # Other process is based on ordered arguments
            for a in ordered_args:
                if a.inputarg == False and a.outputarg == True and a.tp[-1] == "*":
                    # If the arg is pointer and for OUT arg (e.g. int* x),
                    # it's declared as non-pointer (int raw_x).
                    rvd_raw_types.append(a.tp[:-1])
                else:
                    rvd_raw_types.append(a.tp)
                rvd_raw_var_names.append(f"raw_{a.name}")
                rvd_raw_default_values.append(a.defval)
                if a.inputarg:
                    vvd_names.append(a.name)
                    vvd_value_var_names.append(f"value_{a.name}")
                    vvd_corr_raw_var_names.append(f"raw_{a.name}")
                    if a.defval:
                        rsa_num_optional_args += 1
                    else:
                        rsa_num_mandatory_args += 1
                else:
                    if a.outputarg == True and a.py_inputarg == True:
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
            if not v.rettype == "":
                f.write(f"            {v.rettype} raw_retval;\n")
                f.write(f"            raw_retval = ")
            else:
                f.write(f"            ")
            if self.classname and not self.is_static: # call instance method
                f.write(f"get_{self.classname}(klass)->{self.name}")
            else:              # call global function
                f.write(f"{self.cname}")
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
        f.write(f"    rbRaiseCVOverloadException(\"{self.name}\");\n")
        f.write("    return Qnil;\n")
        f.write("}\n\n")
        return


g_class_idx = 0
class ClassInfo:
    def __init__(self, name:str, decl=None):
        global g_class_idx
        self.decl_idx = g_class_idx
        g_class_idx += 1
        self.cname = name.replace(".", "::")   # name: "cv.Ns1.Bar", cname: "cv::Ns1::Bar"
        self.wname = normalize_class_name(name) # "Ns1_Bar"
        self.name = self.wname
        self.methods: dict[str, FuncInfo] = {}
        self.constructor: FuncInfo = None

    def dump(self, depth):
        indent = "  " * depth
        print(f"{indent}cname: {self.cname}")
        print(f"{indent}name: {self.name}")
        for i, method_name in enumerate(self.methods):
            print(f"{indent}methods[{i}] {method_name}")
            self.methods[method_name].dump(depth+1)

class Namespace:
    def __init__(self):
        self.funcs: dict[str, FuncInfo] = {}
        self.consts: dict[str, str] = {}     # "MyEnum2_MYENUM2_VALUE_A" => "cv::Ns1::MyEnum2::MYENUM2_VALUE_A"

    def dump(self, depth):
        indent = "  " * depth
        for i, name in enumerate(self.funcs):
            print(f"{indent}funcs[{i}] {name}")

class RubyWrapperGenerator:
    def __init__(self):
        self.parser = hdr_parser.CppHeaderParser(generate_umat_decls=False, generate_gpumat_decls=False)
        self.classes: dict[str, ClassInfo] = {}
        self.namespaces: dict[str, Namespace] = {}
        self.consts: dict[str, str] = {}
        self.enums: dict[str, str] = {}

    def add_class(self, stype:str, name:str, decl:list):
        classinfo = ClassInfo(name, decl)
        if classinfo.name in self.classes:
            print(f"Generator error: class {classinfo.name} (cname={classinfo.cname}) already exists")
            exit(1)
        self.classes[classinfo.name] = classinfo

    def split_decl_name(self, name):
        chunks = name.split('.')
        namespace = chunks[:-1]
        classes = []
        while namespace and '.'.join(namespace) not in self.parser.namespaces:
            classes.insert(0, namespace.pop())
        return namespace, classes, chunks[-1]

    def add_const(self, name:str, decl:list):
        # name: "cv.Ns1.MyEnum2.MYENUM2_VALUE_A"
        cname = name.replace('.','::') # "cv::Ns1::MyEnum2::MYENUM2_VALUE_A"
        namespace, classes, name = self.split_decl_name(name)
        # namespace: ["cv", "Ns1"], classes: ["MyEnum2"], name: "MYENUM2_VALUE_A"
        namespace = '.'.join(namespace) # "cv.Ns1"
        name = '_'.join(classes+[name]) # "MyEnum2_MYENUM2_VALUE_A"
        ns = self.namespaces.setdefault(namespace, Namespace())
        if name in ns.consts:
            print("Generator error: constant %s (cname=%s) already exists" \
                % (name, cname))
            sys.exit(-1)
        ns.consts[name] = cname

    def add_enum(self, name:str, decl:list):
        # name: "cv.Ns1.MyEnum2"
        wname = normalize_class_name(name) # "Ns1_MyEnum2"
        if wname.endswith("<unnamed>"):
            wname = None
        else:
            self.enums[wname] = name
        const_decls = decl[3] # [ ["const cv.Ns1.MyEnum2.MYENUM2_VALUE_A", "-1", [], [], None, ""], ...]

        for decl in const_decls:
            name = decl[0] # "const cv.Ns1.MyEnum2.MYENUM2_VALUE_A"
            self.add_const(name.replace("const ", "").strip(), decl)

    def add_func(self, decl:list):
        # decl[0]: "cv.Ns1.Bar.method1"
        namespace, classes, barename = self.split_decl_name(decl[0])
        # namespace: ["cv", "Ns1"], classes_list: ["Bar"], barename: "method1"
        cname = "::".join(namespace+classes+[barename]) # "cv::Ns1::Bar::method1"
        name = barename # "method1"
        classname = ''
        bareclassname = ''
        if classes:
            classname = normalize_class_name('.'.join(namespace+classes)) # "Ns1_Bar"
            bareclassname = classes[-1]                                   # "Bar"
        namespace_str = '.'.join(namespace) # "cv.Ns1"
        isconstructor = name == bareclassname
        is_static = False
        isphantom = False
        for m in decl[2]:
            if m == "/S":
                is_static = True

        if isconstructor:
            name = "_".join(classes[:-1]+[name])

        if is_static:
            # Add it as a method to the class
            func_map = self.classes[classname].methods
            func = func_map.setdefault(name, FuncInfo(classname, name, cname, isconstructor, namespace_str, is_static))
            func.add_variant(decl, isphantom)

            # Add it as global function
            g_name = "_".join(classes+[name]) # "SubSubC1_smethod1"
            w_classes = [] # will be ["SubSubC1"]
            for i in range(0, len(classes)):
                classes_i = classes[:i+1]
                classname_i = normalize_class_name('.'.join(namespace+classes_i))
                w_classname = self.classes[classname_i].wname
                namespace_prefix = normalize_class_name('.'.join(namespace)) + '_'
                if w_classname.startswith(namespace_prefix):
                    w_classname = w_classname[len(namespace_prefix):]
                w_classes.append(w_classname)
            g_wname = "_".join(w_classes+[name]) # "SubSubC1_smethod1"
            func_map = self.namespaces.setdefault(namespace_str, Namespace()).funcs
            func = func_map.setdefault(g_name, FuncInfo("", g_name, cname, isconstructor, namespace_str, False))
            func.add_variant(decl, isphantom)
            if g_wname != g_name:  # TODO OpenCV 5.0
                wfunc = func_map.setdefault(g_wname, FuncInfo("", g_wname, cname, isconstructor, namespace_str, False))
                wfunc.add_variant(decl, isphantom)
        else:
            if classname and not isconstructor:
                func_map = self.classes[classname].methods
            else:
                func_map = self.namespaces.setdefault(namespace_str, Namespace()).funcs
            func = func_map.setdefault(name, FuncInfo(classname, name, cname, isconstructor, namespace_str, is_static))
            func.add_variant(decl, isphantom)
        if classname and isconstructor:
            self.classes[classname].constructor = func

    def gen(self, headers:list[str], out_dir:str):
        fout_inc = open(f"{out_dir}/rbopencv_include.hpp", "w")
        for hdr in headers:
            decls = self.parser.parse(hdr)
            hdr_fname = os.path.split(hdr)[1]
            hdr_stem = os.path.splitext(hdr_fname)[0]
            out_json_path = f"{out_dir}/tmp-{hdr_stem}.json"
            with open(out_json_path, "w") as f:
                json.dump(decls, f, indent=2)
            fout_inc.write(f'#include "{hdr}"\n')
            for decl in decls:
                # for i in range(len(decl)):
                #     if i == 3:
                #         for j in range(len(decl[i])):
                #             print(f"  item[{j}] {decl[i][j]}")
                #     else:
                #         if decl[i] is None:
                #             print(f"{i} is_None")
                #         else:
                #             print(f"{i} {decl[i]}")
                name:str = decl[0]
                if name.startswith("struct ") or name.startswith("class"):
                    p = name.find(" ")
                    stype = name[:p]          # "class" of "struct"
                    name = name[p+1:].strip() # "cv.Ns1.Bar"
                    self.add_class(stype, name, decl)
                elif name.startswith("const "):
                    self.add_const(name.replace("const ", "").strip(), decl)
                elif name.startswith("enum "):
                    # name: "enum class cv.Ns1.MyEnum2"
                    self.add_enum(name.rsplit(" ", 1)[1], decl) # arg: "cv.Ns1.MyEnum2"
                else:
                    self.add_func(decl)
        fout_inc.close()
        # for i, class_name in enumerate(self.classes):
        #     print(f"classes[{i}] {class_name}")
        #     self.classes[class_name].dump(1)
        classlist = list(self.classes.items())
        classlist.sort()
        classlist1 = [(classinfo.decl_idx, name, classinfo) for name, classinfo in classlist]
        classlist1.sort()

        # gen namespace registration
        with open(f"{out_dir}/rbopencv_namespaceregistration.hpp", "w") as f:
            for ns_name, ns in sorted(self.namespaces.items()):
                # ns_name: "cv.Ns1.Ns11"
                ns_str = ns_name[2:]                        # ".Ns1.Ns11"
                normed_name = normalize_class_name(ns_name) # "Ns1_Ns11"
                f.write(f'init_submodule(mCV2, "CV2{ns_str}", methods_{normed_name}, consts_{normed_name});\n')
        # gen wrapclass
        with open(f"{out_dir}/rbopencv_wrapclass.hpp", "w") as f:
            for decl_idx, name, classinfo in classlist1:
                cClass = f"c{name}" # cFoo
                cname = classinfo.cname # cv::Ns1::Bar
                wrap_struct = f"struct Wrap_{name}" # struct WrapFoo
                classtype = f"{name}_type"
                f.write(f"static VALUE {cClass};\n")
                f.write(f"{wrap_struct} {{\n")
                f.write(f"    {cname}* v;\n")
                f.write(f"}};\n")
                f.write(f"static void wrap_{name}_free({wrap_struct}* ptr){{\n")
                f.write(f"    delete ptr->v;\n")
                f.write(f"    ruby_xfree(ptr);\n")
                f.write(f"}};\n")
                f.write(f"static const rb_data_type_t {classtype} {{\n")
                f.write(f"    \"{name}\",\n")
                f.write(f"    {{NULL, reinterpret_cast<RUBY_DATA_FUNC>(wrap_{name}_free), NULL}},\n")
                f.write(f"    NULL, NULL,\n")
                f.write(f"    RUBY_TYPED_FREE_IMMEDIATELY\n")
                f.write(f"}};\n")
                f.write(f"static {cname}* get_{name}(VALUE self){{\n")
                f.write(f"    {wrap_struct}* ptr;\n")
                f.write(f"    TypedData_Get_Struct(self, {wrap_struct}, &{name}_type, ptr);\n")
                f.write(f"    return ptr->v;\n")
                f.write(f"}}\n")
                f.write(f"static VALUE wrap_{name}_alloc(VALUE klass){{\n")
                f.write(f"    {wrap_struct}* ptr = nullptr;\n")
                f.write(f"    VALUE ret = TypedData_Make_Struct(klass, {wrap_struct}, &{name}_type, ptr);\n")
                f.write(f"    ptr->v = new {classinfo.cname}();\n")
                f.write(f"    return ret;\n")
                f.write(f"}}\n")
                f.write(f"static VALUE wrap_{name}_init(VALUE self){{\n")
                f.write(f"    return Qnil;\n")
                f.write(f"}}\n\n")
        # gen class registration
        with open(f"{out_dir}/rbopencv_classregistration.hpp", "w") as f:
            for decl_idx, name, classinfo in classlist1:
                # name: "Ns1_Bar"
                barename = classinfo.cname.split("::")[-1] # "Bar"
                cClass = f"c{name}" # cNs1_Bar
                wrap_struct = f" struct Wrap_{name}" # struct Wrap_Ns1_Bar
                classtype = f"{name}_type"
                f.write(f"{{\n")
                f.write(f'    VALUE parent_mod = get_parent_module_by_wname(mCV2, "{classinfo.wname}");\n')
                f.write(f"    {cClass} = rb_define_class_under(parent_mod, \"{barename}\", rb_cObject);\n")
                f.write(f"    rb_define_alloc_func({cClass}, wrap_{name}_alloc);\n")
                f.write(f"    rb_define_private_method({cClass}, \"initialize\", RUBY_METHOD_FUNC(wrap_{name}_init), 0);\n")
                for name, func in classinfo.methods.items():
                    num_supported_variants, _ = func.is_target_function()
                    if num_supported_variants == 0:
                        continue
                    wrapper_name = func.get_wrapper_name()
                    if func.is_static:
                        f.write(f"    rb_define_singleton_method({cClass}, \"{func.name}\", RUBY_METHOD_FUNC({wrapper_name}), -1);\n")
                    else:
                        f.write(f"    rb_define_method({cClass}, \"{func.name}\", RUBY_METHOD_FUNC({wrapper_name}), -1);\n")
                f.write(f"}}\n")
        # gen funcs
        with open(f"{out_dir}/rbopencv_funcs.hpp", "w") as f:
            funcs:list[FuncInfo] = []
            for ns_name, ns in sorted(self.namespaces.items()):
                #print(f"ns_name: {ns_name}")
                #ns.dump(1)
                if ns_name.split(".")[0] != "cv":
                    continue
                for name, func in sorted(ns.funcs.items()):
                    if func.isconstructor:
                        continue
                    funcs.append(func)
            for decl_idx, name, classinfo in classlist1:
                for name, func in sorted(classinfo.methods.items()):
                    if func.isconstructor:
                        continue
                    funcs.append(func)
            for func in funcs:
                func.gen_code(f, self.classes)
        # gen MethodDef and ConstDef
        with open(f"{out_dir}/rbopencv_modules_content.hpp", "w") as f:
            for ns_name, ns in sorted(self.namespaces.items()):
                ns = self.namespaces[ns_name]
                wname = normalize_class_name(ns_name)

                f.write('static MethodDef methods_%s[] = {\n'%wname)
                for name, func in sorted(ns.funcs.items()):
                    num_supported_variants, support_statuses = func.is_target_function()
                    if num_supported_variants == 0:
                        continue
                    wrapper_name = func.get_wrapper_name()
                    if func.isconstructor:
                        continue
                    if func.is_static:
                        continue
                    #self.code_ns_reg.write(func.get_tab_entry()) # [orig-content]
                    f.write(f'    {{"{name}", {wrapper_name}}},\n')
                custom_entries_macro = 'RBOPENCV_EXTRA_METHODS_{}'.format(wname.upper())
                f.write('#ifdef {}\n    {}\n#endif\n'.format(custom_entries_macro, custom_entries_macro))
                f.write('    {NULL, NULL}\n};\n\n')

                f.write('static ConstDef consts_%s[] = {\n'%wname)
                for name, cname in sorted(ns.consts.items()):
                    f.write('    {"%s", static_cast<long>(%s)},\n'%(name, cname))
                    compat_name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name).upper()
                    if name != compat_name:
                        f.write('    {"%s", static_cast<long>(%s)},\n'%(compat_name, cname))
                custom_entries_macro = 'RBOPENCV_EXTRA_CONSTANTS_{}'.format(wname.upper())
                f.write('#ifdef {}\n    {}\n#endif\n'.format(custom_entries_macro, custom_entries_macro))
                f.write('    {NULL, 0}\n};\n\n')


headers_txt = "./headers.txt"
if len(sys.argv) == 2:
    headers_txt = sys.argv[1]
headers = []
with open(headers_txt) as f:
    for line in f:
        line = line.strip()
        if not line.startswith("#"):
            headers.append(line)
dstdir = "./autogen"
os.makedirs(dstdir, exist_ok=True)
generator = RubyWrapperGenerator()
generator.gen(headers, dstdir)
g_logger.close()

with open(f"{dstdir}/support-status.csv", "w") as f:
    for func in g_log_processed_funcs:
        for vi, v in enumerate(func.variants):
            arg_types = [a.tp for a in v.args]
            args_str = ",".join(arg_types)
            is_supported, reason = func.support_statuses[vi]
            print(f'{is_supported},{func.cname},"{args_str}",{reason}', file=f)

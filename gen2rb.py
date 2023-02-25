#!/usr/bin/env python

import copy
import json
import os
import re
import sys

import hdr_parser

g_log_processed_funcs:list["FuncInfo"] = []

def normalize_class_name(name):
    return re.sub(r"^cv\.", "", name).replace(".", "_")

def split_decl_name(name, namespaces):
    chunks = name.split('.')
    namespace = chunks[:-1]
    classes = []
    while namespace and '.'.join(namespace) not in namespaces:
        classes.insert(0, namespace.pop())
    return namespace, classes, chunks[-1]

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
                raise ValueError("/O is not supported")
                self.inputarg = False
                self.outputarg = True
                self.returnarg = True
            elif m == "/IO":
                raise ValueError("/IO is not supported")
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
                print(f"unhandled tuple[3]: {m}")
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
        return "static VALUE %s(int argc, VALUE *argv, VALUE klass)" % (full_fname)

    def is_target_function(self) -> tuple[int, list[tuple[bool, str]]]:
        supported_rettypes = [
            "", # void
            "int",
        ]
        supported_argtypes = [
            "int",
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
            if self.classname: # call instance method
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
    def __init__(self, name, decl=None):
        global g_class_idx
        self.decl_idx = g_class_idx
        g_class_idx += 1
        self.cname = name.replace(".", "::")
        self.name = normalize_class_name(name)
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
        self.funcs = {}

    def dump(self, depth):
        indent = "  " * depth
        for i, name in enumerate(self.funcs):
            print(f"{indent}funcs[{i}] {name}")

def gen(headers:list[str], out_dir:str):
    classes: dict[str, ClassInfo] = {}
    namespaces: dict[str, Namespace] = {}
    parser = hdr_parser.CppHeaderParser(generate_umat_decls=False, generate_gpumat_decls=False)
    for hdr in headers:
        decls = parser.parse(hdr)
        hdr_fname = os.path.split(hdr)[1]
        hdr_stem = os.path.splitext(hdr_fname)[0]
        out_json_path = f"./autogen/tmp-{hdr_stem}.json"
        with open(out_json_path, "w") as f:
            json.dump(decls, f, indent=2)
        with open("./autogen/rbopencv_include.hpp", "w") as f:
            f.write(f'#include "{hdr}"\n')
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
            name = decl[0]
            if name.startswith("struct") or name.startswith("class"):
                cols = name.split(" ", 1)
                stype = cols[0] # "struct" or "class"
                name = cols[1]
                classinfo = ClassInfo(name, decl)
                if classinfo.name in classes:
                    print(f"Generator error: class {classinfo.name} (cname={classinfo.cname}) already exists")
                    exit(1)
                classes[classinfo.name] = classinfo
            else:
                namespace, classes_list, barename = split_decl_name(decl[0], parser.namespaces)
                #print(f"namespace: {namespace}, classes_list: {classes_list}, barename: {barename}")
                cname = "::".join(namespace+classes_list+[barename])
                name = barename
                classname = ''
                bareclassname = ''
                if classes_list:
                    classname = normalize_class_name('.'.join(namespace+classes_list))
                    bareclassname = classes_list[-1]
                namespace_str = '.'.join(namespace)
                isconstructor = name == bareclassname
                is_static = False
                isphantom = False
                for i, m in enumerate(decl[2]):
                    print(f"{i} {m}")
                    if m == "/S":
                        is_static = True
                if isconstructor:
                    name = "_".join(classes_list[:-1]+[name])
                #print(f"  name: {name}, cname: {cname}, bareclassname: {bareclassname}, namespace_str: {namespace_str}, isconstructor: {isconstructor}")
                if is_static:
                    pass
                else:
                    if classname and not isconstructor:
                        func_map = classes[classname].methods
                    else:
                        func_map = namespaces.setdefault(namespace_str, Namespace()).funcs
                    func = func_map.setdefault(name, FuncInfo(classname, name, cname, isconstructor, namespace_str, is_static))
                    func.add_variant(decl, isphantom)
                if classname and isconstructor:
                    classes[classname].constructor = func
    #for i, class_name in enumerate(classes):
    #    print(f"classes[{i}] {class_name}")
    #    classes[class_name].dump(1)
    classlist = list(classes.items())
    classlist.sort()
    classlist1 = [(classinfo.decl_idx, name, classinfo) for name, classinfo in classlist]
    classlist1.sort()

    # gen wrapclass
    with open("./autogen/rbopencv_wrapclass.hpp", "w") as f:
        for decl_idx, name, classinfo in classlist1:
            cClass = f"c{name}" # cFoo
            wrap_struct = f"struct Wrap_{name}" # struct WrapFoo
            classtype = f"{name}_type"
            f.write(f"static VALUE {cClass};\n")
            f.write(f"{wrap_struct} {{\n")
            f.write(f"    {name}* v;\n")
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
            f.write(f"}};")
            f.write(f"static {name}* get_{name}(VALUE self){{\n")
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
            f.write(f"}}\n")
    # gen class registration
    with open("./autogen/rbopencv_classregistration.hpp", "w") as f:
        for decl_idx, name, classinfo in classlist1:
            cClass = f"c{name}" # cFoo
            wrap_struct = f" struct Wrap_{name}" # struct WrapFoo
            classtype = f"{name}_type"
            f.write(f"{{\n")
            f.write(f"    {cClass} = rb_define_class_under(mCV2, \"{name}\", rb_cObject);\n")
            f.write(f"    rb_define_alloc_func({cClass}, wrap_{name}_alloc);\n")
            f.write(f"    rb_define_private_method({cClass}, \"initialize\", RUBY_METHOD_FUNC(wrap_{name}_init), 0);\n")
            for name, func in classinfo.methods.items():
                wrapper_name = func.get_wrapper_name()
                f.write(f"    rb_define_method({cClass}, \"{func.name}\", RUBY_METHOD_FUNC({wrapper_name}), -1);\n")
            f.write(f"}}\n")
    # gen funcs
    with open("./autogen/rbopencv_funcs.hpp", "w") as f:
        funcs:list[FuncInfo] = []
        for ns_name, ns in sorted(namespaces.items()):
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
            func.gen_code(f, classes)

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
gen(headers, dstdir)

with open("./autogen/support-status.csv", "w") as f:
    for func in g_log_processed_funcs:
        for vi, v in enumerate(func.variants):
            arg_types = [a.tp for a in v.args]
            args_str = ",".join(arg_types)
            is_supported, reason = func.support_statuses[vi]
            print(f'{is_supported},{func.cname},"{args_str}",{reason}', file=f)

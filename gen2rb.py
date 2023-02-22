#!/usr/bin/env python

import json
import os
import re
import sys

import hdr_parser


def normalize_class_name(name):
    return re.sub(r"^cv\.", "", name).replace(".", "_")

def split_decl_name(name, namespaces):
    chunks = name.split('.')
    namespace = chunks[:-1]
    classes = []
    while namespace and '.'.join(namespace) not in namespaces:
        classes.insert(0, namespace.pop())
    return namespace, classes, chunks[-1]

def handle_ptr(tp):
    if tp.startswith('Ptr_'):
        tp = 'Ptr<' + "::".join(tp.split('_')[1:]) + '>'
    return tp

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

def gen(headers:list[str], out_dir:str):
    classes: dict[str, ClassInfo] = {}
    namespaces = {}
    parser = hdr_parser.CppHeaderParser(generate_umat_decls=False, generate_gpumat_decls=False)
    for hdr in headers:
        decls = parser.parse(hdr)
        hdr_fname = os.path.split(hdr)[1]
        hdr_stem = os.path.splitext(hdr_fname)[0]
        out_json_path = f"tmp-{hdr_stem}.json"
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
            wrap_struct = f" struct Wrap_{name}" # struct WrapFoo
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
            f.write(f"}}\n")


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

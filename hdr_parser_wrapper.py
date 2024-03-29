#!/usr/bin/env python

import enum
import dataclasses
import os
import re
import hdr_parser

@dataclasses.dataclass
class CvArg:
    tp:str
    tp_qname:str|None
    name:str
    defval:str
    inputarg:bool
    outputarg:bool

@dataclasses.dataclass
class CvVariant:
    wrap_as:str|None
    isconst:bool
    isvirtual:bool
    ispurevirtual:bool
    rettype:str
    rettype_qname:str|None
    args:list[CvArg]

@dataclasses.dataclass
class CvFunc:
    filename:str             # header filename (for debug)
    ns:"CvNamespace|None"    # For global function. None if it's a member func
    klass:"CvKlass|None"     # For member func. None if it's global function
    name_cpp:str             # name in C++ API
    name:str                 # name of CV_WRAP_AS or CV_EXPORTS_AS if specified, else same as name
    isstatic:bool
    variants:list[CvVariant]

@dataclasses.dataclass
class CvEnumerator:
    name:str
    value:int

@dataclasses.dataclass
class CvEnum:
    filename:str           # header filename (for debug)
    ns:"CvNamespace|None"  # For global enum. None if it's defined in a class
    klass:"CvKlass|None"   # For enum in class. None if it's global enum
    name:str
    isscoped:bool
    values:list[CvEnumerator]

@dataclasses.dataclass
class CvProp:
    tp:str
    tp_qname:str|None
    name:str
    rw:bool

@dataclasses.dataclass
class CvKlass:
    filename:str            # header filename (for debug)
    ns:"CvNamespace|None"   # namespace if it's defined directly under namespace, else None
    klass:"CvKlass|None"    # class if it's defined inside other class, else None
    name:str
    klasses:list["CvKlass"] # classes/structs defined in this class
    enums:list[CvEnum]
    props:list[CvProp]
    funcs:list[CvFunc]
    str_parent_klass:str|None
    parent_klass:"CvKlass|None"
    child_klasses:list["CvKlass"]
    depth:int               # depth in class hierarchy (root class is 0)
    no_bind:bool = False

@dataclasses.dataclass
class CvNamespace:
    name:str
    klasses:list[CvKlass]
    enums:list[CvEnum]
    funcs:list[CvFunc]

class TypedefType(enum.Enum):
    CLASS = enum.auto()
    FUNC = enum.auto()
    ENUM = enum.auto()
    OTHER = enum.auto() # int, short, std::vector<int>, etc.

@dataclasses.dataclass
class CvTypedef:
    tdtype:TypedefType
    name:str
    klass:CvKlass|None
    func:CvFunc|None
    enum:CvEnum|None
    other:str|None

@dataclasses.dataclass
class CvApi:
    cvnamespaces:dict[str,CvNamespace]
    cvenums:dict[str,CvEnum]
    cvklasses:dict[str,CvKlass]
    cvfuncs:dict[str,CvFunc]
    cvtypedefs:dict[str,CvTypedef]

# Returns the string representaion of parent class. "" if no parent.
def _parse_parent_klass_str(str_parent_klasses:str, str_this_klass:str) -> str|None:
    if str_parent_klasses.startswith(": "):
        str_parent_klasses = str_parent_klasses[2:]
    parent_class_strs = str_parent_klasses.split(",")
    parent_class_str = None
    if len(parent_class_strs) == 1:
        parent_class_str = parent_class_strs[0].replace("::", ".")
    elif len(parent_class_strs) >= 2:
        parent_class_str = parent_class_strs[0].replace("::", ".")
        print(f"[Warning] {str_this_klass} has multipe parenet clasess. Only the first one ({parent_class_str}) is used")
    else:
        print(f"[Error] parent_class_str shall not be None (\"\" for non-parent class)")
        exit(1)
    return parent_class_str

def _parse_headers(headers:list[str]) -> CvApi:
    cvklasses:dict[str,CvKlass] = {}
    cvnamespaces:dict[str,CvNamespace] = {}
    cvenums:dict[str,CvEnum] = {}
    cvfuncs:dict[str,CvFunc] = {}
    parser = hdr_parser.CppHeaderParser(generate_umat_decls=False, generate_gpumat_decls=False)
    for hdr in headers:
        decls = parser.parse(hdr)
        for decl in decls:
            # Remove unexpected whitespace in decl[0] of "cv.ClassName.operator ()"
            decl0 = decl[0].replace("operator ()", "operator()")
            decl0_strs = decl0.split()
            if len(decl0_strs) >= 2:
                if not decl0_strs[0] in ["class", "struct", "enum"]:
                    print(f"[Error] unsupported decl type: {decl[0]} in {hdr}")
                    exit(0)
            d00 = decl0.split()[0]
            if d00 in ["class", "struct"]:
                clsname = decl0.split()[1]
                cvprops:list[CvProp] = []
                for prop_strs in decl[3]:
                    prop_tp = prop_strs[0]
                    prop_name = prop_strs[1]
                    if not prop_strs[2] == "":
                        print(f"[Error] prop_strs[2] is not empty")
                        exit(0)
                    prop_rw = False
                    for prop_prop_str in prop_strs[3]:
                        if prop_prop_str == "/RW":
                            prop_rw = True
                        else:
                            print(f"[Error] unsupported prop_prop: {prop_prop_str} in {clsname} {hdr}")
                            exit(0)
                    cvprops.append(CvProp(tp=prop_tp, tp_qname=None, name=prop_name, rw=prop_rw))
                cvklass = CvKlass(filename=hdr, ns=None, klass=None, name=clsname, klasses=[], enums=[], props=cvprops, funcs=[],
                    str_parent_klass=None, parent_klass=None, child_klasses=[], depth=-1)
                cvklasses[clsname] = cvklass
                cvklass.str_parent_klass = _parse_parent_klass_str(decl[1], clsname)
                ns = ".".join(clsname.split(".")[0:-1])
            elif d00 in ["enum"]:
                ss = decl0.split()
                enum_name = ""
                isscoped = False
                if len(ss) == 2:
                    enum_name = ss[1]
                elif len(ss) == 3:
                    enum_name = ss[2]
                    isscoped = True
                if not (enum_name.startswith("cv.") or enum_name.startswith("cvflann.")):
                    # Exclude enums which are not under cv nor cvflann namespace
                    # e.g. CpuFeatures, etc.
                    continue
                enum = CvEnum(filename=hdr, ns=None, klass=None, name=enum_name, isscoped=isscoped, values=[])
                for value_info in decl[3]:
                    value = CvEnumerator(name=value_info[0].split()[1], value=value_info[1])
                    enum.values.append(value)
                cvenums[enum_name] = enum
            else: # func
                rettype = decl[4] if decl[4] else ""
                wrap_as = None
                isconst = False
                isstatic = False
                isvirtual = False
                ispurevirtual = False
                for func_attr in decl[2]:
                    if func_attr.startswith("="):
                        wrap_as = func_attr[1:]
                    elif func_attr == "/C":
                        isconst = True
                    elif func_attr == "/S":
                        isstatic = True
                    elif func_attr == "/V":
                        isvirtual = True
                    elif func_attr == "/PV":
                        ispurevirtual = True
                    else:
                        print(f"[Warning] {decl0} has unsupported func attribute: {func_attr}")

                args = []
                for arg_tuple in decl[3]:
                    if arg_tuple[0].startswith("Ptr_"):
                        tp = "Ptr<" + "::".join(arg_tuple[0].split("_")[1:]) + ">"
                    else:
                        tp = arg_tuple[0]
                    if tp == "string":
                        tp = "std::string"
                    inputarg = True
                    outputarg = False
                    for arg_attr in arg_tuple[3]:
                        if arg_attr == "/O":
                            inputarg = False
                            outputarg = True
                        elif arg_attr == "/IO":
                            inputarg = True
                            outputarg = True
                        elif arg_attr == "/C":
                            pass # no need to handle "const"
                        elif arg_attr == "/Ref":
                            pass # no need to handle lvalueref
                        else:
                            print(f"[Warning] {decl0} has unsupported arg attribute: {arg_attr}")
                    cvarg = CvArg(tp=tp, tp_qname=None, name=arg_tuple[1], defval=arg_tuple[2], inputarg=inputarg, outputarg=outputarg)
                    args.append(cvarg)

                variant = CvVariant(wrap_as=wrap_as, isconst=isconst, isvirtual=isvirtual,
                    ispurevirtual=ispurevirtual, rettype=rettype, rettype_qname=None, args=args)
                if wrap_as:
                    name = ".".join(decl0.split(".")[0:-1]) + "." + wrap_as
                else:
                    name = decl0
                if name in cvfuncs.keys():
                    func = cvfuncs[name]
                else:
                    func = CvFunc(filename=hdr, ns=None, klass=None, name_cpp=decl0, name=name,
                        isstatic=isstatic, variants=[])
                    cvfuncs[name] = func
                func.variants.append(variant)

    # Append defined namespaces
    for nsname in parser.namespaces:
        ns = CvNamespace(nsname, klasses=[], enums=[], funcs=[])
        cvnamespaces[nsname] = ns

    # Construct parent/child class structure
    for _, cvklass in cvklasses.items():
        if cvklass.str_parent_klass:
            if not cvklass.str_parent_klass in cvklasses.keys():
                print(f"[Warning] {cvklass.name} has parent class ({cvklass.str_parent_klass}, "
                    "but not defined. Bind without parent class")
                continue
            pklass = cvklasses[cvklass.str_parent_klass]
            cvklass.parent_klass = pklass
            pklass.child_klasses.append(cvklass)

    # Construct tree structure of definition: enum <-> namespace or class
    for _, cvenum in cvenums.items():
        ns_or_klass = ".".join(cvenum.name.split(".")[0:-1])
        if ns_or_klass in parser.namespaces:
            #print(f"ENUM {cvenum.name:40s} in ns")
            ns = cvnamespaces[ns_or_klass]
            ns.enums.append(cvenum)
            cvenum.ns = ns
        elif ns_or_klass in cvklasses.keys():
            #print(f"ENUM {cvenum.name:40s} in class")
            klass = cvklasses[ns_or_klass]
            klass.enums.append(cvenum)
            cvenum.klass = klass
        else:
            # Special handling for cv.PCA.Flags, cv.SVD.Flags, etc.
            # If an enum (.e.g cv.Foo.Bar.Enum1) is not included in neither namespaces nor klasses,
            # it's assumed that cv.Foo.Bar is a class without CV_EXPORTS_W, and cv.Foo is a namespace.
            #print(f"ENUM {cvenum.name:40s} nb_class")
            nsname = ".".join(ns_or_klass.split(".")[0:-1])
            if not nsname in cvnamespaces.keys():
                print(f"[Error] {nsname} of {cvenum.name} is assumed to be a namespace, but not defined")
                exit(1)
            # Class name should start with small character or "_".
            first_char = ns_or_klass.split(".")[-1][0]
            if not (first_char.isupper() or first_char == "_"):
                print(f"[Error] {ns_or_klass} of {cvenum} is probably a class, but does not start with [A-Z_]")
                exit(1)
            ns = cvnamespaces[nsname]
            klass = CvKlass(filename=cvenum.filename, ns=ns, klass=None, name=ns_or_klass, klasses=[], enums=[], props=[], funcs=[],
                str_parent_klass=None, parent_klass=None, child_klasses=[], depth=-1, no_bind=True)
            cvklasses[ns_or_klass] = klass
            klass.enums.append(cvenum)
            cvenum.klass = klass

    # Construct tree structure of definition: class <-> namespace or class
    sorted_klassnames = sorted(cvklasses.keys())
    for klassname in sorted_klassnames:
        cvklass = cvklasses[klassname]
        ns_or_klass = ".".join(cvklass.name.split(".")[0:-1])
        if ns_or_klass in cvnamespaces.keys():
            ns = cvnamespaces[ns_or_klass]
            ns.klasses.append(cvklass)
            cvklass.ns = ns
            #print(f"CLASS {cvklass.name:40s}  ns: {ns.name}")
        elif ns_or_klass in cvklasses.keys():
            defining_klass = cvklasses[ns_or_klass]
            defining_klass.klasses.append(cvklass)
            cvklass.klass = defining_klass
            #print(f"CLASS {cvklass.name:40s}  class: {defining_klass.name}")
        else:
            print(f"[Error] class {cvklass.name} is not defined in neither namespaces nor other classes")
            exit(0)

    # Construct tree structure of definition: func <-> namespace or class
    for _, cvfunc in cvfuncs.items():
        ns_or_klass = ".".join(cvfunc.name.split(".")[0:-1])
        if ns_or_klass in cvnamespaces.keys():
            ns = cvnamespaces[ns_or_klass]
            ns.funcs.append(cvfunc)
            cvfunc.ns = ns
            #print(f"FUNC {cvfunc.name:40s}  ns: {ns.name}")
        elif ns_or_klass in cvklasses.keys():
            klass = cvklasses[ns_or_klass]
            klass.funcs.append(cvfunc)
            cvfunc.klass = klass
            #print(f"FUNC {cvfunc.name:40s}  class: {klass.name}")
        else:
            print(f"[Error] FUNC {cvfunc.name} is not defined in neither namespaces nor other classes")
            exit(0)

    # Check unsupported structures
    for _, cvenum in cvenums.items():
        if cvenum.klass and cvenum.isscoped:
            print(f"[Error] {cvenum.name}: scoped enum in class is not supported: {cvenum.filename}")
            exit(1)
    for _, cvklass in cvklasses.items():
        if cvklass.ns:
            continue
        elif cvklass.klass:
            if cvklass.klass.ns:
                continue
            else:
                print(f"[Error] class inside class inside class is not supported: {cvklass} -> {cvklass.klass} -> ?")
                exit(1)
        else:
            pass # NotReached

    # Add some classes/structs which are not declared as CV_EXPORTS_W.
    # They are necessary because they are used with typedef
    if "cv.flann" in cvnamespaces.keys():
        klass_IndexParams = CvKlass(filename="(root)/opencv2/flann/miniflann.hpp", ns=cvnamespaces["cv.flann"], klass=None, name="cv.flann.IndexParams",
            klasses=[], enums=[], props=[], funcs=[], str_parent_klass=None, parent_klass=None, child_klasses=[], depth=-1, no_bind=True)
        cvklasses["cv.flann.IndexParams"] = klass_IndexParams
        klass_SearchParams = CvKlass(filename="(root)/opencv2/flann/miniflann.hpp", ns=cvnamespaces["cv.flann"], klass=None, name="cv.flann.SearchParams",
            klasses=[], enums=[], props=[], funcs=[], str_parent_klass=klass_IndexParams.name, parent_klass=klass_IndexParams, child_klasses=[], depth=-1, no_bind=True)
        cvklasses["cv.flann.SearchParams"] = klass_SearchParams
        klass_IndexParams.child_klasses.append(klass_SearchParams)

    # Manually add typedefs because hdr_parser.py does not provide them
    cvtypedefs:dict[str,CvTypedef] = {}
    if "cv.Feature2D" in cvklasses.keys():
        cvtypedefs["cv.FeatureDetector"] = CvTypedef(tdtype=TypedefType.CLASS, name="cv.FeatureDetector", klass=cvklasses["cv.Feature2D"],
            func=None, enum=None, other=None)
        cvtypedefs["cv.DescriptorExtractor"] = CvTypedef(tdtype=TypedefType.CLASS, name="cv.DescriptorExtractor", klass=cvklasses["cv.Feature2D"],
            func=None, enum=None, other=None)
    if "cv.dnn.DictValue" in cvklasses.keys():
        cvtypedefs["cv.dnn.Net.LayerId"] = CvTypedef(tdtype=TypedefType.CLASS, name="cv.dnn.Net.LayerId", klass=cvklasses["cv.dnn.DictValue"],
            func=None, enum=None, other=None)
    cvtypedefs["cv.dnn.MatShape"] = CvTypedef(tdtype=TypedefType.OTHER, name="cv.dnn.MatShape", klass=None, func=None, enum=None, other="vector<int>")

    cvapi = CvApi(cvnamespaces=cvnamespaces, cvenums=cvenums, cvklasses=cvklasses, cvfuncs=cvfuncs, cvtypedefs=cvtypedefs)
    return cvapi

def gen_supported_primitive_types() -> list[str]:
    supported_primitive_types = [
        "char", "short", "int", "long", "float", "double", "int64", "bool", "void", "uchar", "size_t",
        "std.string", "c_string",
    ]
    return supported_primitive_types

def gen_supported_typenames(api:CvApi) -> list[str]:
    supported_cv_basic_types = [
        "cv.Mat", "cv.UMat",
        "cv.Rect", "cv.Rect2d",
        "cv.Point", "cv.Point2d", "cv.Point2f", "cv.Point3f",
        "cv.Size", "cv.Size2i", "cv.Size2f",
        "cv.Vec4f", "cv.Vec6f", "cv.Vec3d",
        "cv.Scalar",
        "cv.RotatedRect",
        "cv.Vec2i", "cv.Vec3i", "cv.Vec2d",
        "cv.String",
    ]

    declared_typenames:list[str] = []
    for _, cvenum in api.cvenums.items():
        declared_typenames.append(cvenum.name)
    for _, cvklass in api.cvklasses.items():
        declared_typenames.append(cvklass.name)
    for _, cvtypedef in api.cvtypedefs.items():
        declared_typenames.append(cvtypedef.name)

    supported_typenames = []
    for t in declared_typenames:
        supported_typenames.append(t)
    for t in supported_cv_basic_types:
        supported_typenames.append(t)
    return supported_typenames

# current_qualifier:
#   if tp is arg/retval of class/instance method => class qname (cv.Ns1.C1)
#   if tp is arg/retval of global function       => ns qname (cv.Ns1)
#   if tp is public member of class              => class qname
def check_qname(tp:str, current_qualifier:str, supported_primitive_types:list[str], supported_typenames:list[str]) -> str|None:
    if tp == "":  # for constructor rettype
        return ""
    template = "%s"
    tp = tp.replace("std::", "")
    if tp[-1] == "*":
        template = "%s*"
        tp = tp[0:-1]
    main_type = tp # main_type is Xxx of vector<Xxx>, Ptr<Xxx>, etc.
    m = re.match("vector_(.+)", tp)
    if m:
        template = "std.vector<%s>"
        main_type = m.group(1)
    m = re.match("vector_vector_(.+)", tp)
    if m:
        template = "std.vector<std.vector<%s>>"
        main_type = m.group(1)
    m = re.match("vector<(.+)>", tp)
    if m:
        template = "std.vector<%s>"
        main_type = m.group(1)
    m = re.match("vector<vector<(.+)> *>", tp)
    if m:
        template = "std.vector<std.vector<%s>>"
        main_type = m.group(1)
    m = re.match("Ptr<(.+)>", tp)
    if m:
        template = "Ptr<%s>"
        # Special handling for ANN_MLP. It's not ANN.MLP
        if m.group(1) == "ANN_MLP":
            main_type = m.group(1)
        else:
            main_type = m.group(1).replace("_", ".")

    main_type = main_type.replace("::", ".")
    if main_type in ["string", "String"]:
        main_type = "std.string"
    if main_type in supported_primitive_types:
        return template % main_type
    if main_type.startswith("cv."):
        if main_type in supported_typenames:
            return template % main_type
    else:
        if main_type in supported_typenames:
            return template % main_type
        elif "cv." + main_type in supported_typenames:
            return template % ("cv." + main_type)

    # qualifiler_elems: ["cv", "NsName1", "Class1"]
    qualifier_elems = current_qualifier.split(".")
    # qualifier_candidates: ["cv.NsName1.Class1", "cv.NsName1", "cv"]
    qualifier_candidates = [".".join(qualifier_elems[0:i]) for i in range(len(qualifier_elems), 0, -1)]
    for qualifier_candidate in qualifier_candidates:
        qname = qualifier_candidate + "." + main_type
        if qname in supported_typenames:
            return template % qname
    return None

def _set_klass_depth(cvklass:CvKlass):
    depth = 0
    pklass = cvklass
    while True:
        pklass = pklass.parent_klass
        if not pklass:
            break
        depth += 1
    cvklass.depth = depth

def _dump_api(cvapi:CvApi,log_dir:str):
    os.makedirs(log_dir, exist_ok=True)
    with open(f"{log_dir}/log-cvnamespaces.txt", "w") as f:
        for _, cvns in cvapi.cvnamespaces.items():
            print(f"{cvns.name}", file=f)
    with open(f"{log_dir}/log-cvklasses.txt", "w") as f:
        for _, cvklass in cvapi.cvklasses.items():
            print(f"{cvklass.name}", file=f)
    with open(f"{log_dir}/log-cvenums.txt", "w") as f:
        for _, cvenum in cvapi.cvenums.items():
            print(f"{cvenum.name}", file=f)
    with open(f"{log_dir}/log-cvtypedefs.txt", "w") as f:
        for _, cvtypedef in cvapi.cvtypedefs.items():
            print(f"{cvtypedef.name}", file=f)
    with open(f"{log_dir}/log-cvfuncs.txt", "w") as f:
        for _, cvfunc in cvapi.cvfuncs.items():
            for var_i, var in enumerate(cvfunc.variants, 1):
                print(f"{cvfunc.name} {var_i} {var.rettype_qname}", file=f)
                for arg in var.args:
                    print(f"  {arg.tp} {arg.tp_qname} {arg.inputarg} {arg.outputarg}", file=f)

def parse_headers(headers:list[str], log_dir:str|None=None) -> CvApi:
    cvapi = _parse_headers(headers)
    supported_primitive_types = gen_supported_primitive_types()
    supported_typenames = gen_supported_typenames(cvapi)
    # Set qname of public members
    for _, cvklass in cvapi.cvklasses.items():
        if cvklass.ns:
            current_qualifier = cvklass.ns.name
        elif cvklass.klass:
            current_qualifier = cvklass.klass.name
        else:
            current_qualifier = ""
        for prop in cvklass.props:
            tp_qname = check_qname(prop.tp, current_qualifier, supported_primitive_types, supported_typenames)
            if tp_qname is None:
                print(f"[Error] Could not find qname of public member: {cvklass.name}.{prop.name}")
                exit(1)
            prop.tp_qname = tp_qname
    # Set qname of each arg
    for _, cvfunc in cvapi.cvfuncs.items():
        for var in cvfunc.variants:
            if cvfunc.ns:
                current_qualifier = cvfunc.ns.name
            elif cvfunc.klass:
                current_qualifier = cvfunc.klass.name
            else:
                current_qualifier = ""
            rettype_qname = check_qname(var.rettype, current_qualifier, supported_primitive_types, supported_typenames)
            if rettype_qname is None:
                print(f"[Error] Could not find qname of rettype: {var.rettype} {cvfunc.name}")
                exit(1)
            var.rettype_qname = rettype_qname
            for arg in var.args:
                tp_qname = check_qname(arg.tp, current_qualifier, supported_primitive_types, supported_typenames)
                if tp_qname is None:
                    print(f"[Error] Could not find qname argtype: {arg.tp} {cvfunc.name}")
                    exit(1)
                arg.tp_qname = tp_qname
    # Set depth of each CvKlass
    for _, cvklass in cvapi.cvklasses.items():
        _set_klass_depth(cvklass)

    if log_dir:
        log_dir = log_dir.replace("\\", "/").rstrip("/")
        _dump_api(cvapi, log_dir)
    return cvapi

if __name__ == "__main__":
    import sys
    if not len(sys.argv) == 3:
        print(f"usage: hdr_parser_wraper.py <headers.txt> <log_dir>", file=sys.stderr)
        exit(1)
    headers = []
    with open(sys.argv[1], "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                continue
            headers.append(line.split("#")[0].strip())
    cvapi = parse_headers(headers, sys.argv[2])

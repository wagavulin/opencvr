#!/usr/bin/env python

import dataclasses
import sys
import hdr_parser

@dataclasses.dataclass
class CvArg:
    tp:str
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
    #wrap_as:str|None
    #isconst:bool
    #isstatic:bool
    #isvirtual:bool
    #ispurevirtual:bool
    #args:list[CvArg]

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
class CvKlass:
    filename:str            # header filename (for debug)
    ns:"CvNamespace|None"   # namespace if it's defined directly under namespace, else None
    klass:"CvKlass|None"    # class if it's defined inside other class, else None
    name:str
    klasses:list["CvKlass"] # classes/structs defined in this class
    enums:list[CvEnum]
    funcs:list[CvFunc]
    str_parent_klass:str|None
    parent_klass:"CvKlass|None"
    child_klasses:list["CvKlass"]
    no_bind:bool = False

@dataclasses.dataclass
class CvNamespace:
    name:str
    klasses:list[CvKlass]
    enums:list[CvEnum]
    funcs:list[CvFunc]

@dataclasses.dataclass
class CvApi:
    cvnamespaces:dict[str,CvNamespace]
    cvenums:dict[str,CvEnum]
    cvklasses:dict[str,CvKlass]
    cvfuncs:dict[str,CvFunc]

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

def parse_headers(headers:list[str]) -> CvApi:
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
                cvklass = CvKlass(filename=hdr, ns=None, klass=None, name=clsname, klasses=[], enums=[], funcs=[],
                    str_parent_klass=None, parent_klass=None, child_klasses=[])
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
                if not enum_name.startswith("cv."):
                    # Exclude enums which are not under cv namespace
                    # e.g. CpuFeatures, cvflann.flann_algorithm_t, etc.
                    continue
                enum = CvEnum(filename=hdr, ns=None, klass=None, name=enum_name, isscoped=isscoped, values=[])
                for value_info in decl[3]:
                    value = CvEnumerator(name=value_info[0].split()[1], value=value_info[1])
                    enum.values.append(value)
                cvenums[enum_name] = enum
            else: # func
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
                    cvarg = CvArg(tp=tp, name=arg_tuple[1], defval=arg_tuple[2], inputarg=inputarg, outputarg=outputarg)
                    args.append(cvarg)

                variant = CvVariant(wrap_as=wrap_as, isconst=isconst, isvirtual=isvirtual,
                    ispurevirtual=ispurevirtual, args=args)
                if wrap_as:
                    name = ".".join(decl0.split(".")[0:-1]) + "." + wrap_as
                else:
                    name = decl0
                if name in cvfuncs.keys():
                    func = cvfuncs[name]
                else:
                    func = CvFunc(filename=hdr, ns=None, klass=None, name_cpp=decl0, name=name, isstatic=isstatic, variants=[])
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
            klass = CvKlass(filename=cvenum.filename, ns=ns, klass=None, name=ns_or_klass, klasses=[], enums=[], funcs=[],
                str_parent_klass=None, parent_klass=None, child_klasses=[], no_bind=True)
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

    cvapi = CvApi(cvnamespaces=cvnamespaces, cvenums=cvenums, cvklasses=cvklasses, cvfuncs=cvfuncs)
    return cvapi

# headers_txt = "./headers.txt"
# headers = []
# with open(headers_txt) as f:
#     for line in f:
#         line = line.strip()
#         if line.startswith("#"):
#             continue
#         headers.append(line.split("#")[0].strip())

#cvapi = parse_headers()
#show_all_funcs(cvapi)

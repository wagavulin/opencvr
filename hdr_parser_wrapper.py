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
class CvFunc:
    filename:str           # header filename (for debug)
    ns:"CvNamespace|None"  # For global function. None if it's a member func
    klass:"CvKlass|None"   # For member func. None if it's global function
    name:str
    wrap_as:str|None
    isconst:bool
    isstatic:bool
    isvirtual:bool
    ispurevirtual:bool
    args:list[CvArg]

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
    filename:str      # header filename (for debug)
    name:str
    enums:list[CvEnum]
    funcs:list[CvFunc]
    str_parent_klass:str|None
    parent_klass:"CvKlass|None"
    child_klasses:list["CvKlass"]

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

def _parse_parent_klass_str(str_parent_klasses:str, str_this_klass:str) -> str|None:
    parent_class_strs = str_parent_klasses.split(",")
    parent_class_str = None
    if len(parent_class_strs) == 1:
        if parent_class_strs[0].startswith(": "):
            parent_class_str = parent_class_strs[0][2:].replace("::", ".") # remove the beginning ": "
        else:
            parent_class_str = parent_class_strs[0].replace("::", ".")
        if len(parent_class_strs) >= 2:
            print(f"[Warning] {str_this_klass} has multipe parenet clasess. Only the first one ({parent_class_str}) is used")
    return parent_class_str

def parse_headers(headers:list[str]):
    cvklasses:dict[str,CvKlass] = {}
    cvnamespaces:dict[str,CvNamespace] = {}
    cvenums:dict[str,CvEnum] = {}
    parser = hdr_parser.CppHeaderParser(generate_umat_decls=False, generate_gpumat_decls=False)
    for hdr in headers:
        decls = parser.parse(hdr)
        for decl in decls:
            d00 = decl[0].split()[0]
            if d00 in ["class", "struct"]:
                clsname = decl[0].split()[1]
                cvklass = CvKlass(filename=hdr, name=clsname, enums=[], funcs=[], str_parent_klass=None, parent_klass=None, child_klasses=[])
                cvklasses[clsname] = cvklass
                cvklass.str_parent_klass = _parse_parent_klass_str(decl[1], clsname)
                ns = ".".join(clsname.split(".")[0:-1])
                if ns in cvklasses.keys():
                    pass # do nothing
                elif ns in cvnamespaces.keys():
                    cvnamespaces[ns].klasses.append(cvklass)
                else:
                    cvnamespaces[ns] = CvNamespace(name=ns, klasses=[cvklass], enums=[], funcs=[])
            elif d00 in ["enum"]:
                ss = decl[0].split()
                enum_name = ""
                isscoped = False
                if len(ss) == 2:
                    enum_name = ss[1]
                elif len(ss) == 3:
                    enum_name = ss[2]
                    isscoped = True
                enum = CvEnum(filename=hdr, ns=None, klass=None, name=enum_name, isscoped=isscoped, values=[])
                for value_info in decl[3]:
                    value = CvEnumerator(name=value_info[0].split()[1], value=value_info[1])
                    enum.values.append(value)
                ns_or_klass:str = ".".join(enum_name.split(".")[0:-1])
                if ns_or_klass in cvklasses.keys():
                    klass = cvklasses[ns_or_klass]
                    klass.enums.append(enum)
                    enum.klass = klass
                else:
                    if ns_or_klass in cvnamespaces.keys():
                        ns = cvnamespaces[ns_or_klass]
                    else:
                        ns = CvNamespace(name=ns_or_klass, klasses=[], enums=[enum], funcs=[])
                        cvnamespaces[ns_or_klass] = ns
                    ns.enums.append(enum)
                    enum.ns = ns
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
                        print(f"[Warning] {decl[0]} has unsupported func attribute: {func_attr}")

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
                            print(f"[Warning] {decl[0]} has unsupported arg attribute: {arg_attr}")
                    cvarg = CvArg(tp=tp, name=arg_tuple[1], defval=arg_tuple[2], inputarg=inputarg, outputarg=outputarg)
                    args.append(cvarg)

                func = CvFunc(filename=hdr, ns=None, klass=None, name=decl[0].split(".")[-1], wrap_as=wrap_as, isconst=isconst,
                    isstatic=isstatic, isvirtual=isvirtual, ispurevirtual=ispurevirtual, args=args)
                ns_or_klass:str = ".".join(decl[0].split(".")[0:-1])
                if ns_or_klass in cvklasses.keys(): # ns_or_klass is a class name
                    klass = cvklasses[ns_or_klass]
                    klass.funcs.append(func)
                    func.klass = klass
                else: # ns_or_klass is a namespace name
                    if ns_or_klass in cvnamespaces.keys():
                        ns = cvnamespaces[ns_or_klass]
                    else:
                        ns = CvNamespace(name=ns_or_klass, klasses=[], enums=[], funcs=[func])
                        cvnamespaces[ns_or_klass] = ns
                    ns.funcs.append(func)
                    func.ns = ns

    for clsname, cvklass in cvklasses.items():
        if cvklass.str_parent_klass:
            pklass = cvklasses[cvklass.str_parent_klass]
            cvklass.parent_klass = pklass
            pklass.child_klasses.append(cvklass)
    cvapi = CvApi(cvnamespaces=cvnamespaces, cvenums=cvenums, cvklasses=cvklasses)
    return cvapi

def _show_all_funcs(cvapi:CvApi):
    all_funcs:list[tuple[str,str,CvFunc]] = []
    for _, cvns in cvapi.cvnamespaces.items():
        for func in cvns.funcs:
            all_funcs.append(("F", cvns.name, func))
        for cvklass in cvns.klasses:
            for func in cvklass.funcs:
                all_funcs.append(("M", cvklass.name, func))
    for t in all_funcs:
        print(f"{t[0]} {t[1]} {t[2].name}", end="")
        if t[2].wrap_as:
            print(f" -> {t[2].wrap_as}")
        else:
            print()
        for arg in t[2].args:
            print(f"  {arg.name}  {arg.tp}")

def _show_all_enums(cvapi:CvApi):
    for _, cvenum in cvapi.cvenums.items():
        print(f"{cvenum.name} in {cvenum.filename}")
        if cvenum.ns:
            print(f"  NS {cvenum.ns.name}")
        elif cvenum.klass:
            print(f"   C {cvenum.klass.name}")
        for value in cvenum.values:
            print(f"    {value.name}  {value.value}")

def _show_all_namespaces(cvapi:CvApi):
    for _, cvns in cvapi.cvnamespaces.items():
        print(f"{cvns.name}")

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

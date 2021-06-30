#!/usr/bin/env python

# About thie file
# This file is created by modifying gen2.py in OpenCV, which is under
# Apache License Version 2.0. Refer the original file:
# https://github.com/opencv/opencv/blob/4.5.2/modules/python/src2/gen2.py
#
# About modified parts
# Copyright 2021 wagavulin

from io import StringIO
import hdr_parser, sys, re, os
from string import Template
import pprint
from collections import namedtuple
import copy

log_processed_funcs = []

forbidden_arg_types = ["void*"]

ignored_arg_types = ["RNG*"]

pass_by_val_types = ["Point*", "Point2f*", "Rect*", "String*", "double*", "float*", "int*"]

gen_template_check_self = Template("""
    ${cname} * self1 = 0;
    if (!pyopencv_${name}_getp(self, self1))
        return failmsgp("Incorrect type of self (must be '${name}' or its derivative)");
    ${pname} _self_ = ${cvt}(self1);
""")
gen_template_call_constructor_prelude = Template("""new (&(self->v)) Ptr<$cname>(); // init Ptr with placement new
        if(self) """)

gen_template_call_constructor = Template("""self->v.reset(new ${cname}${py_args})""")

gen_template_simple_call_constructor_prelude = Template("""if(self) """)

gen_template_simple_call_constructor = Template("""new (&(self->v)) ${cname}${py_args}""")

gen_template_parse_args = Template("""const char* keywords[] = { $kw_list, NULL };
    if( PyArg_ParseTupleAndKeywords(py_args, kw, "$fmtspec", (char**)keywords, $parse_arglist)$code_cvt )""")

gen_template_func_body = Template("""$code_decl
    $code_parse
    {
        ${code_prelude}ERRWRAP2($code_fcall);
        $code_ret;
    }
""")

gen_template_mappable = Template("""
    {
        ${mappable} _src;
        if (pyopencv_to_safe(src, _src, info))
        {
            return cv_mappable_to(_src, dst);
        }
    }
""")

gen_template_type_decl = Template("""
// Converter (${name})

template<>
struct PyOpenCV_Converter< ${cname} >
{
    static PyObject* from(const ${cname}& r)
    {
        return pyopencv_${name}_Instance(r);
    }
    static bool to(PyObject* src, ${cname}& dst, const ArgInfo& info)
    {
        if(!src || src == Py_None)
            return true;
        ${cname} * dst_;
        if (pyopencv_${name}_getp(src, dst_))
        {
            dst = *dst_;
            return true;
        }
        ${mappable_code}
        failmsg("Expected ${cname} for argument '%s'", info.name);
        return false;
    }
};

""")

gen_template_map_type_cvt = Template("""
template<> bool pyopencv_to(PyObject* src, ${cname}& dst, const ArgInfo& info);

""")

gen_template_set_prop_from_map = Template("""
    if( PyMapping_HasKeyString(src, (char*)"$propname") )
    {
        tmp = PyMapping_GetItemString(src, (char*)"$propname");
        ok = tmp && pyopencv_to_safe(tmp, dst.$propname, ArgInfo("$propname", false));
        Py_DECREF(tmp);
        if(!ok) return false;
    }""")

gen_template_type_impl = Template("""
// GetSet (${name})

${getset_code}

// Methods (${name})

${methods_code}

// Tables (${name})

static PyGetSetDef pyopencv_${name}_getseters[] =
{${getset_inits}
    {NULL}  /* Sentinel */
};

static PyMethodDef pyopencv_${name}_methods[] =
{
${methods_inits}
    {NULL,          NULL}
};
""")


gen_template_get_prop = Template("""
static PyObject* pyopencv_${name}_get_${member}(pyopencv_${name}_t* p, void *closure)
{
    return pyopencv_from(p->v${access}${member});
}
""")

gen_template_get_prop_algo = Template("""
static PyObject* pyopencv_${name}_get_${member}(pyopencv_${name}_t* p, void *closure)
{
    $cname* _self_ = dynamic_cast<$cname*>(p->v.get());
    if (!_self_)
        return failmsgp("Incorrect type of object (must be '${name}' or its derivative)");
    return pyopencv_from(_self_${access}${member});
}
""")

gen_template_set_prop = Template("""
static int pyopencv_${name}_set_${member}(pyopencv_${name}_t* p, PyObject *value, void *closure)
{
    if (!value)
    {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the ${member} attribute");
        return -1;
    }
    return pyopencv_to_safe(value, p->v${access}${member}, ArgInfo("value", false)) ? 0 : -1;
}
""")

gen_template_set_prop_algo = Template("""
static int pyopencv_${name}_set_${member}(pyopencv_${name}_t* p, PyObject *value, void *closure)
{
    if (!value)
    {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the ${member} attribute");
        return -1;
    }
    $cname* _self_ = dynamic_cast<$cname*>(p->v.get());
    if (!_self_)
    {
        failmsgp("Incorrect type of object (must be '${name}' or its derivative)");
        return -1;
    }
    return pyopencv_to_safe(value, _self_${access}${member}, ArgInfo("value", false)) ? 0 : -1;
}
""")


gen_template_prop_init = Template("""
    {(char*)"${member}", (getter)pyopencv_${name}_get_${member}, NULL, (char*)"${member}", NULL},""")

gen_template_rw_prop_init = Template("""
    {(char*)"${member}", (getter)pyopencv_${name}_get_${member}, (setter)pyopencv_${name}_set_${member}, (char*)"${member}", NULL},""")

gen_template_overloaded_function_call = Template("""
    {
${variant}

        pyPopulateArgumentConversionErrors();
    }
""")

class FormatStrings:
    string = 's'
    unsigned_char = 'b'
    short_int = 'h'
    int = 'i'
    unsigned_int = 'I'
    long = 'l'
    unsigned_long = 'k'
    long_long = 'L'
    unsigned_long_long = 'K'
    size_t = 'n'
    float = 'f'
    double = 'd'
    object = 'O'

ArgTypeInfo = namedtuple('ArgTypeInfo',
                        ['atype', 'format_str', 'default_value',
                         'strict_conversion'])
# strict_conversion is False by default
ArgTypeInfo.__new__.__defaults__ = (False,)

simple_argtype_mapping = {
    "bool": ArgTypeInfo("bool", FormatStrings.unsigned_char, "0", True),
    "size_t": ArgTypeInfo("size_t", FormatStrings.unsigned_long_long, "0", True),
    "int": ArgTypeInfo("int", FormatStrings.int, "0", True),
    "float": ArgTypeInfo("float", FormatStrings.float, "0.f", True),
    "double": ArgTypeInfo("double", FormatStrings.double, "0", True),
    "c_string": ArgTypeInfo("char*", FormatStrings.string, '(char*)""'),
    "string": ArgTypeInfo("std::string", FormatStrings.object, None, True),
}


def normalize_class_name(name):
    return re.sub(r"^cv\.", "", name).replace(".", "_")


def get_type_format_string(arg_type_info):
    if arg_type_info.strict_conversion:
        return FormatStrings.object
    else:
        return arg_type_info.format_str


class ClassProp(object):
    def __init__(self, decl):
        self.tp = decl[0].replace("*", "_ptr")
        self.name = decl[1]
        self.readonly = True
        if "/RW" in decl[3]:
            self.readonly = False

class ClassInfo(object):
    def __init__(self, name, decl=None):
        self.cname = name.replace(".", "::")
        self.name = self.wname = normalize_class_name(name)
        self.sname = name[name.rfind('.') + 1:]
        self.ismap = False
        self.issimple = False
        self.isalgorithm = False
        self.methods = {}
        self.props = []
        self.mappables = []
        self.consts = {}
        self.base = None
        self.constructor = None
        customname = False

        if decl:
            bases = decl[1].split()[1:]
            if len(bases) > 1:
                print("Note: Class %s has more than 1 base class (not supported by Python C extensions)" % (self.name,))
                print("      Bases: ", " ".join(bases))
                print("      Only the first base class will be used")
                #return sys.exit(-1)
            elif len(bases) == 1:
                self.base = bases[0].strip(",")
                if self.base.startswith("cv::"):
                    self.base = self.base[4:]
                if self.base == "Algorithm":
                    self.isalgorithm = True
                self.base = self.base.replace("::", "_")

            for m in decl[2]:
                if m.startswith("="):
                    wname = m[1:]
                    npos = name.rfind('.')
                    if npos >= 0:
                        self.wname = normalize_class_name(name[:npos] + '.' + wname)
                    else:
                        self.wname = wname
                    customname = True
                elif m == "/Map":
                    self.ismap = True
                elif m == "/Simple":
                    self.issimple = True
            self.props = [ClassProp(p) for p in decl[3]]

        if not customname and self.wname.startswith("Cv"):
            self.wname = self.wname[2:]

    def gen_map_code(self, codegen):
        all_classes = codegen.classes
        code = "static bool pyopencv_to(PyObject* src, %s& dst, const ArgInfo& info)\n{\n    PyObject* tmp;\n    bool ok;\n" % (self.cname)
        code += "".join([gen_template_set_prop_from_map.substitute(propname=p.name,proptype=p.tp) for p in self.props])
        if self.base:
            code += "\n    return pyopencv_to_safe(src, (%s&)dst, info);\n}\n" % all_classes[self.base].cname
        else:
            code += "\n    return true;\n}\n"
        return code

    def gen_code(self, codegen):
        all_classes = codegen.classes
        if self.ismap:
            return self.gen_map_code(codegen)

        getset_code = StringIO()
        getset_inits = StringIO()

        sorted_props = [(p.name, p) for p in self.props]
        sorted_props.sort()

        access_op = "->"
        if self.issimple:
            access_op = "."

        for pname, p in sorted_props:
            if self.isalgorithm:
                getset_code.write(gen_template_get_prop_algo.substitute(name=self.name, cname=self.cname, member=pname, membertype=p.tp, access=access_op))
            else:
                getset_code.write(gen_template_get_prop.substitute(name=self.name, member=pname, membertype=p.tp, access=access_op))
            if p.readonly:
                getset_inits.write(gen_template_prop_init.substitute(name=self.name, member=pname))
            else:
                if self.isalgorithm:
                    getset_code.write(gen_template_set_prop_algo.substitute(name=self.name, cname=self.cname, member=pname, membertype=p.tp, access=access_op))
                else:
                    getset_code.write(gen_template_set_prop.substitute(name=self.name, member=pname, membertype=p.tp, access=access_op))
                getset_inits.write(gen_template_rw_prop_init.substitute(name=self.name, member=pname))

        methods_code = StringIO()
        methods_inits = StringIO()

        sorted_methods = list(self.methods.items())
        sorted_methods.sort()

        if self.constructor is not None:
            methods_code.write(self.constructor.gen_code(codegen))

        for mname, m in sorted_methods:
            methods_code.write(m.gen_code(codegen))
            methods_inits.write(m.get_tab_entry())

        code = gen_template_type_impl.substitute(name=self.name, wname=self.wname, cname=self.cname,
            getset_code=getset_code.getvalue(), getset_inits=getset_inits.getvalue(),
            methods_code=methods_code.getvalue(), methods_inits=methods_inits.getvalue())

        return code

    def gen_def(self, codegen):
        all_classes = codegen.classes
        baseptr = "NoBase"
        if self.base and self.base in all_classes:
            baseptr = all_classes[self.base].name

        constructor_name = "0"
        if self.constructor is not None:
            constructor_name = self.constructor.get_wrapper_name()

        return "CVPY_TYPE({}, {}, {}, {}, {}, {});\n".format(
            self.wname,
            self.name,
            self.cname if self.issimple else "Ptr<{}>".format(self.cname),
            self.sname if self.issimple else "Ptr",
            baseptr,
            constructor_name
        )


def handle_ptr(tp):
    if tp.startswith('Ptr_'):
        tp = 'Ptr<' + "::".join(tp.split('_')[1:]) + '>'
    return tp


class ArgInfo(object):
    def __init__(self, arg_tuple):
        self.tp = handle_ptr(arg_tuple[0])
        self.name = arg_tuple[1]
        self.defval = arg_tuple[2]
        self.isarray = False
        self.arraylen = 0
        self.arraycvt = None
        self.inputarg = True
        self.outputarg = False
        self.returnarg = False
        self.isrvalueref = False
        for m in arg_tuple[3]:
            if m == "/O":
                self.inputarg = False
                self.outputarg = True
                self.returnarg = True
            elif m == "/IO":
                self.inputarg = True
                self.outputarg = True
                self.returnarg = True
            elif m.startswith("/A"):
                self.isarray = True
                self.arraylen = m[2:].strip()
            elif m.startswith("/CA"):
                self.isarray = True
                self.arraycvt = m[2:].strip()
            elif m == "/RRef":
                self.isrvalueref = True
        self.py_inputarg = False
        self.py_outputarg = False

    # [for-debug]
    def dump(self, depth):
        indent = "  " * depth
        print(f"{indent}tp {self.tp}")
        print(f"{indent}name {self.name}")
        print(f"{indent}defval {self.defval}")
        print(f"{indent}isarray {self.isarray}")
        print(f"{indent}arraylen {self.arraylen}")
        print(f"{indent}arraycvt {self.arraycvt}")
        print(f"{indent}inputarg {self.inputarg}")
        print(f"{indent}outputarg {self.outputarg}")
        print(f"{indent}returnarg {self.returnarg}")
        print(f"{indent}isrvalueref {self.isrvalueref}")
        print(f"{indent}py_inputarg {self.py_inputarg}")
        print(f"{indent}py_outputarg {self.py_outputarg}")
    # [for-debug-end]

    def isbig(self):
        return self.tp in ["Mat", "vector_Mat", "cuda::GpuMat", "GpuMat", "vector_GpuMat", "UMat", "vector_UMat"] # or self.tp.startswith("vector")

    def crepr(self):
        return "ArgInfo(\"%s\", %d)" % (self.name, self.outputarg)


class FuncVariant(object):
    def __init__(self, classname, name, decl, isconstructor, isphantom=False):
        self.classname = classname
        self.name = self.wname = name
        self.isconstructor = isconstructor
        self.isphantom = isphantom

        self.docstring = decl[5]

        self.rettype = decl[4] or handle_ptr(decl[1])
        if self.rettype == "void":
            self.rettype = ""
        self.args = []
        self.array_counters = {}
        for a in decl[3]:
            ainfo = ArgInfo(a)
            if ainfo.isarray and not ainfo.arraycvt:
                c = ainfo.arraylen
                c_arrlist = self.array_counters.get(c, [])
                if c_arrlist:
                    c_arrlist.append(ainfo.name)
                else:
                    self.array_counters[c] = [ainfo.name]
            self.args.append(ainfo)
        self.init_pyproto()

    # [for-debug]
    def dump(self, depth):
        indent = "  " * depth
        print(f"{indent}classname {self.classname}")
        print(f"{indent}name {self.name}")
        print(f"{indent}isconstructor {self.isconstructor}")
        print(f"{indent}isphantom {self.isphantom}")
        print(f"{indent}rettype {self.rettype}")
        for i, arg in enumerate(self.args):
            print(f"{indent}arg[{i}]")
            arg.dump(depth+1)
        print(f"{indent}array_counters")
        indent1 = " " * (depth+1)
        for k, v in self.array_counters.items():
            print(f"{indent1}{k} {v}")
    # [for-debug-end]

    def init_pyproto(self):
        # string representation of argument list, with '[', ']' symbols denoting optional arguments, e.g.
        # "src1, src2[, dst[, mask]]" for cv.add
        argstr = ""

        # list of all input arguments of the Python function, with the argument numbers:
        #    [("src1", 0), ("src2", 1), ("dst", 2), ("mask", 3)]
        # we keep an argument number to find the respective argument quickly, because
        # some of the arguments of C function may not present in the Python function (such as array counters)
        # or even go in a different order ("heavy" output parameters of the C function
        # become the first optional input parameters of the Python function, and thus they are placed right after
        # non-optional input parameters)
        arglist = []

        # the list of "heavy" output parameters. Heavy parameters are the parameters
        # that can be expensive to allocate each time, such as vectors and matrices (see isbig).
        outarr_list = []

        # the list of output parameters. Also includes input/output parameters.
        outlist = []

        firstoptarg = 1000000
        argno = -1
        for a in self.args:
            argno += 1
            if a.name in self.array_counters:
                continue
            assert not a.tp in forbidden_arg_types, 'Forbidden type "{}" for argument "{}" in "{}" ("{}")'.format(a.tp, a.name, self.name, self.classname)
            if a.tp in ignored_arg_types:
                continue
            if a.returnarg:
                outlist.append((a.name, argno))
            if (not a.inputarg) and a.isbig():
                outarr_list.append((a.name, argno))
                continue
            if not a.inputarg:
                continue
            if not a.defval:
                arglist.append((a.name, argno))
            else:
                firstoptarg = min(firstoptarg, len(arglist))
                # if there are some array output parameters before the first default parameter, they
                # are added as optional parameters before the first optional parameter
                if outarr_list:
                    arglist += outarr_list
                    outarr_list = []
                arglist.append((a.name, argno))

        if outarr_list:
            firstoptarg = min(firstoptarg, len(arglist))
            arglist += outarr_list
        firstoptarg = min(firstoptarg, len(arglist))

        noptargs = len(arglist) - firstoptarg
        argnamelist = [aname for aname, argno in arglist]
        argstr = ", ".join(argnamelist[:firstoptarg])
        argstr = "[, ".join([argstr] + argnamelist[firstoptarg:])
        argstr += "]" * noptargs
        if self.rettype:
            outlist = [("retval", -1)] + outlist
        elif self.isconstructor:
            assert outlist == []
            outlist = [("self", -1)]
        if self.isconstructor:
            classname = self.classname
            if classname.startswith("Cv"):
                classname=classname[2:]
            outstr = "<%s object>" % (classname,)
        elif outlist:
            outstr = ", ".join([o[0] for o in outlist])
        else:
            outstr = "None"

        self.py_arg_str = argstr
        self.py_return_str = outstr
        self.py_prototype = "%s(%s) -> %s" % (self.wname, argstr, outstr)
        self.py_noptargs = noptargs
        self.py_arglist = arglist
        for aname, argno in arglist:
            self.args[argno].py_inputarg = True
        for aname, argno in outlist:
            if argno >= 0:
                self.args[argno].py_outputarg = True
        self.py_outlist = outlist

class FuncInfo(object):
    def __init__(self, classname, name, cname, isconstructor, namespace, is_static):
        self.classname = classname
        self.name = name
        self.cname = cname
        self.isconstructor = isconstructor
        self.namespace = namespace
        self.is_static = is_static
        self.variants = []

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

    def get_wrapper_prototype(self, codegen):
        full_fname = self.get_wrapper_name()
        if self.isconstructor:
            raise ValueError("[TODO] constructor generation is not supported")

        return "static VALUE %s(int argc, VALUE *argv, VALUE klass)" % (full_fname)

    def get_tab_entry(self):
        prototype_list = []
        docstring_list = []

        have_empty_constructor = False
        for v in self.variants:
            s = v.py_prototype
            if (not v.py_arglist) and self.isconstructor:
                have_empty_constructor = True
            if s not in prototype_list:
                prototype_list.append(s)
                docstring_list.append(v.docstring)

        # if there are just 2 constructors: default one and some other,
        # we simplify the notation.
        # Instead of ClassName(args ...) -> object or ClassName() -> object
        # we write ClassName([args ...]) -> object
        if have_empty_constructor and len(self.variants) == 2:
            idx = self.variants[1].py_arglist != []
            s = self.variants[idx].py_prototype
            p1 = s.find("(")
            p2 = s.rfind(")")
            prototype_list = [s[:p1+1] + "[" + s[p1+1:p2] + "]" + s[p2:]]

        # The final docstring will be: Each prototype, followed by
        # their relevant doxygen comment
        full_docstring = ""
        for prototype, body in zip(prototype_list, docstring_list):
            full_docstring += Template("$prototype\n$docstring\n\n\n\n").substitute(
                prototype=prototype,
                docstring='\n'.join(
                    ['.   ' + line
                     for line in body.split('\n')]
                )
            )

        # Escape backslashes, newlines, and double quotes
        full_docstring = full_docstring.strip().replace("\\", "\\\\").replace('\n', '\\n').replace("\"", "\\\"")
        # Convert unicode chars to xml representation, but keep as string instead of bytes
        full_docstring = full_docstring.encode('ascii', errors='xmlcharrefreplace').decode()

        return Template('    {"$py_funcname", CV_PY_FN_WITH_KW_($wrap_funcname, $flags), "$py_docstring"},\n'
                        ).substitute(py_funcname = self.variants[0].wname, wrap_funcname=self.get_wrapper_name(),
                                     flags = 'METH_STATIC' if self.is_static else '0', py_docstring = full_docstring)

    # [for-debug]
    def dump(self, depth):
        indent = "  " * depth
        print(f"{indent}classname {self.classname}")
        print(f"{indent}name {self.name}")
        print(f"{indent}cname {self.cname}")
        print(f"{indent}isconstructor {self.isconstructor}")
        print(f"{indent}namespace {self.namespace}")
        print(f"{indent}is_static {self.is_static}")
        for i, variant in enumerate(self.variants):
            print(f"{indent}variant[{i}]")
            variant.dump(depth+1)
    # [for-debug-end]

    def is_target_function(self):
        supported_rettypes = [
            "", # void
            "Mat",
            #"Matx<_Tp, m, n>",
            #"Scalar",
            "bool",
            "size_t",
            "int",
            "int*", # tentative
            "uchar",
            "double",
            "float",
            #"int64",
            #"String",
            #"std::string",
            "Size",
            #"Size_<float>",
            #"Rect",
            #"Rect2d",
            #"Ragne",
            "Point",
            "Point2f",
            #"Point3f",
            #"Vec4d",
            #"Vec4f",
            #"Vec4i",
            #"Vec3d",
            #"Vec3f",
            #"Vec3i",
            #"Vec2d",
            #"Vec2f",
            #"Vec2i",
            #"Point2d",
            #"Point3d",
            #"std::vector<_Tp>",
            #"std::tuple<Ts...>",
            #"std::pair<int, double>",
            #"TermCriteria",
            "RotatedRect",
            #"Moments",
            # Manual bindings
            "vector_Mat",
            "vector_Point",
            "Size2f", # Is this same as Size_<float>?
        ]
        supported_argtypes = [
            "Mat",
            #"Matx<_Tp, m, n>",
            #"Vec<_Tp, cn>",
            #"void*",
            "Scalar",
            "bool",
            "size_t",
            "int",
            "int*", # tentative: for Out arg (not InOut)
            "uchar",
            "double",
            "float",
            "String",
            "Size",
            #"Size_<float>",
            "Rect",
            #"Rect2d",
            #"Range",
            "Point",
            "Point2f",
            #"Point2d",
            #"Point3f",
            #"Point3d",
            #"Vec4d",
            #"Vec4f",
            #"Vec4i",
            #"Vec3d",
            #"Vec3f",
            #"Vec3i",
            #"Vec2d",
            #"Vec2f",
            #"Vec2i",
            #"std::vector<_Tp>",
            #"TermCriteria",
            "RotatedRect",
            "vector_int",
            "RNG*", # ignorable
            # Manual bindings
            "vector_Mat",
            "vector_Point",
            "Size2f", # Is this same as Size_<float>?
        ]

        num_supported_variants = 0
        support_statuses = []
        for v in self.variants:
            num_mandatory_args = 0
            num_optional_args = 0
            if self.classname:
                support_statuses.append((False, "member function is not supported"))
                continue
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

    def gen_code(self, codegen):
        self.num_supported_variants, self.support_statuses = self.is_target_function()
        log_processed_funcs.append(self)
        if self.num_supported_variants == 0:
            return ""

        proto = self.get_wrapper_prototype(codegen)
        code = "%s\n{\n" % (proto,)
        code += "    using namespace %s;\n\n" % self.namespace.replace(".", "::")
        code += "    VALUE h = rb_check_hash_type(argv[argc-1]);\n"
        code += "    if (!NIL_P(h)) {\n        --argc;\n    }\n"
        code += "    int arity = rb_check_arity(argc, 0, UNLIMITED_ARGUMENTS);\n\n"

        code += "    std::string err_msg;\n"
        code += f"    rbPrepareArgumentConversionErrorsStorage({self.num_supported_variants});\n"

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
            code += f"    if (arity >= {rsa_num_mandatory_args}) {{\n"
            for i in range(len(rvd_raw_types)):
                if rvd_raw_default_values[i]:
                    code += f"        {rvd_raw_types[i]} {rvd_raw_var_names[i]} = {rvd_raw_default_values[i]};\n"
                else:
                    code += f"        {rvd_raw_types[i]} {rvd_raw_var_names[i]};\n"
            code += "\n"

            # Generate value variable definitions (vvd)
            for i in range(len(vvd_value_var_names)):
                code += f"        VALUE {vvd_value_var_names[i]};\n"
            code += "\n"

            # Call rb_scan_args() (rsa)
            rsa_scan_args_fmt = f"{rsa_num_mandatory_args}{rsa_num_optional_args}"
            code += f"        int scan_ret = rb_scan_args(argc, argv, \"{rsa_scan_args_fmt}\""
            for i in range(len(vvd_value_var_names)):
                code += f", &{vvd_value_var_names[i]}"
            code += ");\n"

            # Check the result of rb_scan_args()
            code += "        bool conv_args_ok = true;\n"
            for i in range(rsa_num_mandatory_args):
                code += f"        conv_args_ok &= rbopencv_to({vvd_value_var_names[i]}, {vvd_corr_raw_var_names[i]});\n"
                code += f"        if (!conv_args_ok) {{\n"
                code += f"            err_msg = \" can't parse '{vvd_names[i]}'\";\n"
                code += f"        }}\n"
            rsa_idx_optional_start = rsa_num_mandatory_args
            rsa_idx_optional_end = rsa_num_mandatory_args + rsa_num_optional_args - 1
            if rsa_num_optional_args >= 1:
                for i in range(rsa_idx_optional_start, rsa_idx_optional_end+1):
                    code += f"        if (scan_ret >= {i+1}) {{\n"
                    code += f"            conv_args_ok &= rbopencv_to({vvd_value_var_names[i]}, {vvd_corr_raw_var_names[i]});\n"
                    code += f"            if (!conv_args_ok) {{\n"
                    code += f"                err_msg = \" can't parse '{vvd_names[i]}'\";\n"
                    code += f"            }}\n"
                    code += f"        }}\n"
            code += "\n"

            # Call rb_get_kwargs() for keyword arguments
            if rsa_num_optional_args >= 1:
                code += f"        if (!NIL_P(h)) {{\n"
                code += f"            ID table[{rsa_num_optional_args}];\n"
                code += f"            VALUE values[{rsa_num_optional_args}];\n"
                for i in range(rsa_idx_optional_start, rsa_idx_optional_end+1):
                    j = i - rsa_idx_optional_start
                    code += f"            table[{j}] = rb_intern(\"{vvd_names[i]}\");\n"
                code += f"            rb_get_kwargs(h, table, 0, {rsa_num_optional_args}, values);\n"

                # Check the result of rb_get_kwargs()
                for i in range(rsa_idx_optional_start, rsa_idx_optional_end+1):
                    j = i - rsa_idx_optional_start
                    code += f"            if (values[{j}] == Qundef) {{\n"
                    code += f"                // Do nothing. Already set by arg w/o keyword, or use {vvd_corr_raw_var_names[i]} default value\n"
                    code += f"            }} else {{\n"
                    code += f"                conv_args_ok &= rbopencv_to(values[{j}], {vvd_corr_raw_var_names[i]});\n"
                    code += f"                if (!conv_args_ok) {{\n"
                    code += f"                    err_msg = \"Can't parse '{vvd_names[i]}'\";\n"
                    code += f"                }}\n"
                    code += f"            }}\n"
                code += f"        }}\n"

            # Call C++ API if arguments are ready
            code += "        if (conv_args_ok) {\n"
            if v.rettype == "":
                code += f"            {self.cname}({', '.join(cac_args)});\n"
            else:
                code += f"            {v.rettype} raw_retval;\n"
                code += f"            raw_retval = {self.cname}({', '.join(cac_args)});\n"

            # Convert the return value(s)
            num_ruby_retvals = len(rh_raw_var_names)
            if num_ruby_retvals == 0:
                # If no retvals for ruby, return Qnil
                code += f"            return Qnil;\n"
            elif num_ruby_retvals == 1:
                # If 1 ruby retval, return it as VALUE
                retval_raw_var_name = rh_raw_var_names[0]
                code += f"            VALUE value_retval = rbopencv_from({retval_raw_var_name});\n"
                code += f"            return value_retval;\n"
            else:
                # If 2 or more ruby retvals, return as array
                code += f"            VALUE value_retval_array = rb_ary_new3({num_ruby_retvals}"
                for raw_var_name in rh_raw_var_names:
                    code += f", rbopencv_from({raw_var_name})"
                code += ");\n"
                code += f"            return value_retval_array;\n"
            code += "        } else {\n"
            code += "            rbPopulateArgumentConversionErrors(err_msg);\n"
            code += "        }\n"
            code += "    }\n"
        code += f"    rbRaiseCVOverloadException(\"{self.name}\");\n"
        code += "    return Qnil;\n"
        code += "}\n\n"
        return code


class Namespace(object):
    def __init__(self):
        self.funcs = {}
        self.consts = {}


class PythonWrapperGenerator(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.classes = {}
        self.namespaces = {}
        self.consts = {}
        self.enums = {}
        self.code_include = StringIO()
        self.code_enums = StringIO()
        self.code_types = StringIO()
        self.code_funcs = StringIO()
        self.code_ns_reg = StringIO()
        self.code_ns_init = StringIO()
        self.code_type_publish = StringIO()
        self.py_signatures = dict()
        self.class_idx = 0

    def add_class(self, stype, name, decl):
        classinfo = ClassInfo(name, decl)
        classinfo.decl_idx = self.class_idx
        self.class_idx += 1

        if classinfo.name in self.classes:
            print("Generator error: class %s (cname=%s) already exists" \
                % (classinfo.name, classinfo.cname))
            sys.exit(-1)
        self.classes[classinfo.name] = classinfo

        # Add Class to json file.
        namespace, classes, name = self.split_decl_name(name)
        namespace = '.'.join(namespace)
        name = '_'.join(classes+[name])

        py_name = 'cv.' + classinfo.wname  # use wrapper name
        py_signatures = self.py_signatures.setdefault(classinfo.cname, [])
        py_signatures.append(dict(name=py_name))
        #print('class: ' + classinfo.cname + " => " + py_name)

    def split_decl_name(self, name):
        chunks = name.split('.')
        namespace = chunks[:-1]
        classes = []
        while namespace and '.'.join(namespace) not in self.parser.namespaces:
            classes.insert(0, namespace.pop())
        return namespace, classes, chunks[-1]


    def add_const(self, name, decl):
        cname = name.replace('.','::')
        namespace, classes, name = self.split_decl_name(name)
        namespace = '.'.join(namespace)
        name = '_'.join(classes+[name])
        ns = self.namespaces.setdefault(namespace, Namespace())
        if name in ns.consts:
            print("Generator error: constant %s (cname=%s) already exists" \
                % (name, cname))
            sys.exit(-1)
        ns.consts[name] = cname

        # [orig-content]
        # value = decl[1]
        # py_name = '.'.join([namespace, name])
        # py_signatures = self.py_signatures.setdefault(cname, [])
        # py_signatures.append(dict(name=py_name, value=value))
        # #print(cname + ' => ' + str(py_name) + ' (value=' + value + ')')
        # [orig-content-end]

    def add_enum(self, name, decl):
        wname = normalize_class_name(name)
        if wname.endswith("<unnamed>"):
            wname = None
        else:
            self.enums[wname] = name
        const_decls = decl[3]

        for decl in const_decls:
            name = decl[0]
            self.add_const(name.replace("const ", "").strip(), decl)

    def add_func(self, decl):
        namespace, classes, barename = self.split_decl_name(decl[0])
        cname = "::".join(namespace+classes+[barename])
        name = barename
        classname = ''
        bareclassname = ''
        if classes:
            classname = normalize_class_name('.'.join(namespace+classes))
            bareclassname = classes[-1]
        namespace_str = '.'.join(namespace)

        isconstructor = name == bareclassname
        is_static = False
        isphantom = False
        mappable = None
        for m in decl[2]:
            if m == "/S":
                is_static = True
            elif m == "/phantom":
                isphantom = True
                cname = cname.replace("::", "_")
            elif m.startswith("="):
                name = m[1:]
            elif m.startswith("/mappable="):
                mappable = m[10:]
                self.classes[classname].mappables.append(mappable)
                return

        if isconstructor:
            name = "_".join(classes[:-1]+[name])

        if is_static:
            # Add it as a method to the class
            func_map = self.classes[classname].methods
            func = func_map.setdefault(name, FuncInfo(classname, name, cname, isconstructor, namespace_str, is_static))
            func.add_variant(decl, isphantom)

            # Add it as global function
            g_name = "_".join(classes+[name])
            w_classes = []
            for i in range(0, len(classes)):
                classes_i = classes[:i+1]
                classname_i = normalize_class_name('.'.join(namespace+classes_i))
                w_classname = self.classes[classname_i].wname
                namespace_prefix = normalize_class_name('.'.join(namespace)) + '_'
                if w_classname.startswith(namespace_prefix):
                    w_classname = w_classname[len(namespace_prefix):]
                w_classes.append(w_classname)
            g_wname = "_".join(w_classes+[name])
            func_map = self.namespaces.setdefault(namespace_str, Namespace()).funcs
            func = func_map.setdefault(g_name, FuncInfo("", g_name, cname, isconstructor, namespace_str, False))
            func.add_variant(decl, isphantom)
            if g_wname != g_name:  # TODO OpenCV 5.0
                wfunc = func_map.setdefault(g_wname, FuncInfo("", g_wname, cname, isconstructor, namespace_str, False))
                wfunc.add_variant(decl, isphantom)
        else:
            if classname and not isconstructor:
                if not isphantom:
                    cname = barename
                func_map = self.classes[classname].methods
            else:
                func_map = self.namespaces.setdefault(namespace_str, Namespace()).funcs

            func = func_map.setdefault(name, FuncInfo(classname, name, cname, isconstructor, namespace_str, is_static))
            func.add_variant(decl, isphantom)

        if classname and isconstructor:
            self.classes[classname].constructor = func


    def gen_namespace(self, ns_name):
        ns = self.namespaces[ns_name]
        wname = normalize_class_name(ns_name)

        self.code_ns_reg.write('static MethodDef methods_%s[] = {\n'%wname)
        for name, func in sorted(ns.funcs.items()):
            num_supported_variants, support_statuses = func.is_target_function()
            if num_supported_variants == 0:
                continue
            wrapper_name = func.get_wrapper_name()
            if func.isconstructor:
                continue
            #self.code_ns_reg.write(func.get_tab_entry()) # [orig-content]
            self.code_ns_reg.write(f'    {{"{name}", {wrapper_name}}},\n')
        custom_entries_macro = 'RBOPENCV_EXTRA_METHODS_{}'.format(wname.upper())
        self.code_ns_reg.write('#ifdef {}\n    {}\n#endif\n'.format(custom_entries_macro, custom_entries_macro))
        self.code_ns_reg.write('    {NULL, NULL}\n};\n\n')

        self.code_ns_reg.write('static ConstDef consts_%s[] = {\n'%wname)
        for name, cname in sorted(ns.consts.items()):
            self.code_ns_reg.write('    {"%s", static_cast<long>(%s)},\n'%(name, cname))
            compat_name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name).upper()
            if name != compat_name:
                self.code_ns_reg.write('    {"%s", static_cast<long>(%s)},\n'%(compat_name, cname))
        custom_entries_macro = 'RBOPENCV_EXTRA_CONSTANTS_{}'.format(wname.upper())
        self.code_ns_reg.write('#ifdef {}\n    {}\n#endif\n'.format(custom_entries_macro, custom_entries_macro))
        self.code_ns_reg.write('    {NULL, 0}\n};\n\n')

    def gen_enum_reg(self, enum_name):
        name_seg = enum_name.split(".")
        is_enum_class = False
        if len(name_seg) >= 2 and name_seg[-1] == name_seg[-2]:
            enum_name = ".".join(name_seg[:-1])
            is_enum_class = True

        wname = normalize_class_name(enum_name)
        cname = enum_name.replace(".", "::")

        code = ""
        if re.sub(r"^cv\.", "", enum_name) != wname:
            code += "typedef {0} {1};\n".format(cname, wname)
        code += "CV_RB_FROM_ENUM({0});\nCV_RB_TO_ENUM({0});\n\n".format(wname)
        self.code_enums.write(code)

    def save(self, path, name, buf):
        with open(path + "/" + name, "wt") as f:
            f.write(buf.getvalue())

    # [orig-content]
    # def save_json(self, path, name, value):
    #     import json
    #     with open(path + "/" + name, "wt") as f:
    #         json.dump(value, f)
    # [orig-content-end]

    def gen(self, srcfiles, output_path):
        self.clear()
        self.parser = hdr_parser.CppHeaderParser(generate_umat_decls=True, generate_gpumat_decls=True)

        # step 1: scan the headers and build more descriptive maps of classes, consts, functions
        for hdr in srcfiles:
            decls = self.parser.parse(hdr)
            if len(decls) == 0:
                continue

            if hdr.find('misc/python/shadow_') < 0:  # Avoid including the "shadow_" files
                if hdr.find('opencv2/') >= 0:
                    # put relative path
                    self.code_include.write('#include "{0}"\n'.format(hdr[hdr.rindex('opencv2/'):]))
                else:
                    self.code_include.write('#include "{0}"\n'.format(hdr))

            for decl in decls:
                name = decl[0]
                if name.startswith("struct") or name.startswith("class"):
                    # class/struct
                    p = name.find(" ")
                    stype = name[:p]
                    name = name[p+1:].strip()
                    self.add_class(stype, name, decl)
                elif name.startswith("const"):
                    # constant
                    self.add_const(name.replace("const ", "").strip(), decl)
                elif name.startswith("enum"):
                    # enum
                    self.add_enum(name.rsplit(" ", 1)[1], decl)
                else:
                    # function
                    self.add_func(decl)

        # [orig-content]
        # # step 1.5 check if all base classes exist
        # for name, classinfo in self.classes.items():
        #     if classinfo.base:
        #         chunks = classinfo.base.split('_')
        #         base = '_'.join(chunks)
        #         while base not in self.classes and len(chunks)>1:
        #             del chunks[-2]
        #             base = '_'.join(chunks)
        #         if base not in self.classes:
        #             print("Generator error: unable to resolve base %s for %s"
        #                 % (classinfo.base, classinfo.name))
        #             sys.exit(-1)
        #         base_instance = self.classes[base]
        #         classinfo.base = base
        #         classinfo.isalgorithm |= base_instance.isalgorithm  # wrong processing of 'isalgorithm' flag:
        #                                                             # doesn't work for trees(graphs) with depth > 2
        #         self.classes[name] = classinfo

        # # tree-based propagation of 'isalgorithm'
        # processed = dict()
        # def process_isalgorithm(classinfo):
        #     if classinfo.isalgorithm or classinfo in processed:
        #         return classinfo.isalgorithm
        #     res = False
        #     if classinfo.base:
        #         res = process_isalgorithm(self.classes[classinfo.base])
        #         #assert not (res == True or classinfo.isalgorithm is False), "Internal error: " + classinfo.name + " => " + classinfo.base
        #         classinfo.isalgorithm |= res
        #         res = classinfo.isalgorithm
        #     processed[classinfo] = True
        #     return res
        # for name, classinfo in self.classes.items():
        #     process_isalgorithm(classinfo)

        # # step 2: generate code for the classes and their methods
        # classlist = list(self.classes.items())
        # classlist.sort()
        # for name, classinfo in classlist:
        #     self.code_types.write("//{}\n".format(80*"="))
        #     self.code_types.write("// {} ({})\n".format(name, 'Map' if classinfo.ismap else 'Generic'))
        #     self.code_types.write("//{}\n".format(80*"="))
        #     self.code_types.write(classinfo.gen_code(self))
        #     if classinfo.ismap:
        #         self.code_types.write(gen_template_map_type_cvt.substitute(name=classinfo.name, cname=classinfo.cname))
        #     else:
        #         mappable_code = "\n".join([
        #                               gen_template_mappable.substitute(cname=classinfo.cname, mappable=mappable)
        #                                   for mappable in classinfo.mappables])
        #         code = gen_template_type_decl.substitute(
        #             name=classinfo.name,
        #             cname=classinfo.cname if classinfo.issimple else "Ptr<{}>".format(classinfo.cname),
        #             mappable_code=mappable_code
        #         )
        #         self.code_types.write(code)

        # # register classes in the same order as they have been declared.
        # # this way, base classes will be registered in Python before their derivatives.
        # classlist1 = [(classinfo.decl_idx, name, classinfo) for name, classinfo in classlist]
        # classlist1.sort()

        # for decl_idx, name, classinfo in classlist1:
        #     if classinfo.ismap:
        #         continue
        #     self.code_type_publish.write(classinfo.gen_def(self))
        # [orig-content-end]

        # step 3: generate the code for all the global functions
        for ns_name, ns in sorted(self.namespaces.items()):
            if ns_name.split('.')[0] != 'cv':
                continue
            for name, func in sorted(ns.funcs.items()):
                if func.isconstructor:
                    continue
                code = func.gen_code(self)
                self.code_funcs.write(code)
            self.gen_namespace(ns_name)
            self.code_ns_init.write('CVRB_MODULE("{}", {});\n'.format(ns_name[2:], normalize_class_name(ns_name)))

        # step 4: generate the code for enum types
        enumlist = list(self.enums.values())
        enumlist.sort()
        for name in enumlist:
            self.gen_enum_reg(name)

        # step 5: generate the code for constants
        constlist = list(self.consts.items())
        constlist.sort()
        for name, constinfo in constlist:
            self.gen_const_reg(constinfo)

        # That's it. Now save all the files
        self.save(output_path, "rbopencv_generated_include.h", self.code_include)
        self.save(output_path, "rbopencv_generated_funcs.h", self.code_funcs)
        self.save(output_path, "rbopencv_generated_enums.h", self.code_enums)
        # self.save(output_path, "pyopencv_generated_types.h", self.code_type_publish)
        # self.save(output_path, "pyopencv_generated_types_content.h", self.code_types)
        self.save(output_path, "rbopencv_generated_modules.h", self.code_ns_init)
        self.save(output_path, "rbopencv_generated_modules_content.h", self.code_ns_reg)
        # self.save_json(output_path, "pyopencv_signatures.json", self.py_signatures)



if not len(sys.argv) == 2:
    sys.stderr.write("usage: gen2rb.py <headers.txt>\n")
    exit(1)

headers = []
with open(sys.argv[1]) as f:
    for line in f:
        line = line.rstrip()
        headers.append(line)
headers.append("./test_funcs.hpp")
srcfiles = headers
dstdir = "./generated"
os.makedirs(dstdir, exist_ok=True)

generator = PythonWrapperGenerator()
generator.gen(srcfiles, dstdir)

with open("generated/support-status.csv", "w") as fo:
    fo.write("cname,supported,reason\n")
    for f in log_processed_funcs:
        for var_idx, v in enumerate(f.variants):
            is_supported, reason = f.support_statuses[var_idx]
            fo.write(f"{f.cname},{is_supported},{reason}\n")

with open("generated/args.csv", "w") as fo:
    fo.write("ns,classname,name,cname,ctor,static,phantom,rettype")
    fo.write(",tp,name,defval,isarray,arraylen,arraycvt")
    fo.write(",inarg,outarg,retarg,rvalueref,py_inarg,py_outarg\n")
    for f in log_processed_funcs:
        for var_idx, v in enumerate(f.variants):
            is_supported, reason = f.support_statuses[var_idx]
            for a in v.args:
                fo.write(f"{f.namespace},{f.classname},{f.name},{f.cname},{f.isconstructor},{f.is_static}")
                fo.write(f",{v.isphantom},\"{v.rettype}\"")
                fo.write(f",{a.tp},{a.name},\"{a.defval}\",{a.isarray},{a.arraylen},{a.arraycvt}")
                fo.write(f",{a.inputarg},{a.outputarg},{a.returnarg},{a.isrvalueref},{a.py_inputarg},{a.py_outputarg}")
                fo.write("\n")

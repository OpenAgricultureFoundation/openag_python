from openag.categories import SENSORS, ACTUATORS, all_categories
import os
import re
from urlparse import urlparse

def synthesize_firmware_module_info(modules, module_types):
    """
    Modules are allowed to define attributes on their inputs and outputs that
    override the values defined in their respective module types. This function
    takes as input a dictionary of `modules` (mapping module IDs to
    :class:`~openag.models.FirmwareModule` objects) and a dictionary of
    `module_types` (mapping module type IDs to
    :class:`~openag.models.FirmwareModuleType` objects). For each module, it
    synthesizes the information in that module and the corresponding module
    type and returns all the results in a dictionary keyed on the ID of the
    module
    """
    res = {}
    for mod_id, mod_info in modules.items():
        mod_info = dict(mod_info)
        mod_type = module_types[mod_info["type"]]
        # Directly copy any fields only defined on the type
        if "repository" in mod_type:
            mod_info["repository"] = mod_type["repository"]
        mod_info["header_file"] = mod_type["header_file"]
        mod_info["class_name"] = mod_type["class_name"]
        if "dependencies" in mod_type:
            mod_info["dependencies"] = mod_type["dependencies"]
        if "status_codes" in mod_type:
            mod_info["status_codes"] = mod_type["status_codes"]
        # Update the arguments
        mod_info["arguments"] = process_args(
            mod_id, mod_info.get("arguments", []), 
            mod_type.get("arguments", [])
        )
        # Update the categories
        if not "categories" in mod_info:
            mod_info["categories"] = mod_type.get(
                "categories", all_categories
            )
        # Update the inputs
        mod_inputs = mod_info.get("inputs", {})
        for input_name, type_input_info in mod_type.get("inputs", {}).items():
            mod_input_info = dict(type_input_info)
            mod_input_info.update(mod_inputs.get(input_name, {}))
            mod_input_info["variable"] = mod_input_info.get(
                "variable", input_name
            )
            mod_input_info["categories"] = mod_input_info.get(
                "categories", [ACTUATORS]
            )
            mod_inputs[input_name] = mod_input_info
        mod_info["inputs"] = mod_inputs
        # Update the outputs
        mod_outputs = mod_info.get("outputs", {})
        for output_name, type_output_info in mod_type.get("outputs", {}).items():
            mod_output_info = dict(type_output_info)
            mod_output_info.update(mod_outputs.get(output_name, {}))
            mod_output_info["variable"] = mod_output_info.get(
                "variable", output_name
            )
            mod_output_info["categories"] = mod_output_info.get(
                "categories", [SENSORS]
            )
            mod_outputs[output_name] = mod_output_info
        mod_info["outputs"] = mod_outputs
        res[mod_id] = mod_info
    return res

def synthesize_software_module_info(modules, module_types):
    """
    This function takes as input a dictionary of `modules` (mapping module IDs
    to :class:`~openag.models.SoftwareModule` objects) and a dictionary of
    `module_types` (mapping module type IDs to
    :class:`~openag.models.FirmwareModuleType` objects). For each module, it
    synthesizes the information in that module and the corresponding module
    type and returns all the results in a dictionary keyed on the ID of the
    module.
    """
    res = {}
    for mod_id, mod_info in modules.items():
        mod_info = dict(mod_info)
        mod_type = module_types[mod_info["type"]]

        # Directly copy any fields only defined on the type
        mod_info["package"] = mod_type["package"]
        mod_info["executable"] = mod_type["executable"]
        if not "categories" in mod_info:
            mod_info["categories"] = mod_type.get(
                "categories", all_categories
            )
        mod_info["inputs"] = mod_type["inputs"]
        mod_info["outputs"] = mod_type["outputs"]

        # Update the arguments
        mod_info["arguments"] = process_args(
            mod_id, mod_info.get("arguments", []), mod_type["arguments"]
        )

        # Update the parameters
        mod_info["parameters"] = process_params(
            mod_id, mod_info.get("parameters", {}), mod_type["parameters"]
        )
        res[mod_id] = mod_info
    return res

def process_args(mod_id, args, type_args):
    """
    Takes as input a list of arguments defined on a module and the information
    about the required arguments defined on the corresponding module type.
    Validates that the number of supplied arguments is valid and fills any
    missing arguments with their default values from the module type
    """
    res = list(args)
    if len(args) > len(type_args):
        raise ValueError(
            'Too many arguments specified for module "{}" (Got {}, expected '
            '{})'.format(mod_id, len(args), len(type_args))
        )
    for i in range(len(args), len(type_args)):
        arg_info = type_args[i]
        if "default" in arg_info:
            args.append(arg_info["default"])
        else:
            raise ValueError(
                'Not enough module arguments supplied for module "{}" (Got '
                '{}, expecting {})'.format(
                    mod_id, len(args), len(type_args)
                )
            )
    return args

def process_params(mod_id, params, type_params):
    """
    Takes as input a dictionary of parameters defined on a module and the
    information about the required parameters defined on the corresponding
    module type. Validatates that are required parameters were supplied and
    fills any missing parameters with their default values from the module
    type. Returns a nested dictionary of the same format as the `type_params`
    but with an additional key `value` on each inner dictionary that gives the
    value of that parameter for this specific module
    """
    res = {}
    for param_name, param_info in type_params.items():
        val = params.get(param_name, param_info.get("default", None))
        if val:
            param_res = dict(param_info)
            param_res["value"] = val
            res[param_name] = param_res
        elif type_params.get("required", False):
            raise ValueError(
                'Required parameter "{}" is not defined for module '
                '"{}"'.format(param_name, mod_id)
            )
    return res

def index_by_id(docs):
    """Index a list of docs using `_id` field.
    Returns a dictionary keyed by _id."""
    return {doc["_id"]: doc for doc in docs}

def dedupe_by(things, key=None):
    """
    Given an iterator of things and an optional key generation function, return
    a new iterator of deduped things. Things are compared and de-duped by the
    key function, which is hash() by default.
    """
    if not key:
        key = hash
    index = {key(thing): thing for thing in things}
    return index.values()

def parent_dirname(file_path):
    return os.path.basename(os.path.dirname(file_path))

def make_dir_name_from_url(url):
    """This function attempts to emulate something like Git's "humanish"
    directory naming for clone. It's probably not a perfect facimile,
    but it's close."""
    url_path = urlparse(url).path
    head, tail = os.path.split(url_path)
    # If tail happens to be empty as in case `/foo/`, use foo.
    # If we are looking at a valid but ugly path such as
    # `/foo/.git`, use the "foo" not the ".git".
    if len(tail) is 0 or tail[0] is ".":
        head, tail = os.path.split(head)
    dir_name, ext = os.path.splitext(tail)
    return dir_name

# C++ keywords list
CPP_KEYWORDS = [
    "alignas", "alignof", "and", "and_eq", "asm", "atomic_cancel",
    "atomic_commit", "atomic_noexcept", "auto", "bitand", "bitor", "bool",
    "break", "case", "catch", "char", "char16_t", "char32_t", "class",
    "compl", "concept", "const", "constexpr", "const_cast", "continue",
    "decltype", "default", "delete", "do", "double", "dynamic_cast",
    "else", "enum", "explicit", "export", "extern", "false", "float",
    "for", "friend", "goto", "if", "inline", "int", "long", "mutable",
    "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator",
    "or", "or_eq", "private", "protected", "public", "register",
    "reinterpret_cast", "requires", "return short", "signed", "sizeof",
    "static", "static_assert", "static_cast", "struct", "switch",
    "synchronized", "template", "this", "thread_local", "throw", "true",
    "try", "typedef", "typeid", "typename", "union", "unsigned", "using",
    "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq"
]

def safe_cpp_var(s):
    """
    Given a string representing a variable, return a new string that is safe
    for C++ codegen. If string is already safe, will leave it alone.
    """
    s = str(s)
    # Remove non-word, non-space characters
    s = re.sub(r"[^\w\s]", '', s)
    # Replace spaces with _
    s = re.sub(r"\s+", '_', s)
    # Prefix with underscore if what is left is a reserved word
    s = "_" + s if s in CPP_KEYWORDS or s[0].isdigit() else s
    return s

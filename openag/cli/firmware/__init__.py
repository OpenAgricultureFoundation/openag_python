import os
import sys
import json
import click
import subprocess
from importlib import import_module
from voluptuous import Invalid

from base import CodeGen
from plugins import plugin_map
from ..config import config
from openag.couch import Server
from openag.models import FirmwareModuleType, FirmwareModule
from openag.db_names import FIRMWARE_MODULE_TYPE, FIRMWARE_MODULE

def board_option(f):
    f = click.option(
        "-b", "--board", default="megaatmega2560",
        help="The board to use for compilation. Defaults to megaatmega2560 "
        "(Arduino Mega 2560)"
    )(f)
    return f

def project_dir_option(f):
    f = click.option(
        "-d", "--project-dir", default=".",
        help="The directory in which the project should reside"
    )(f)
    return f

def codegen_options(f):
    f = click.option(
        "-c", "--categories", multiple=True, default=["sensors", "actuators"],
        type=click.Choice(["sensors", "actuators", "calibration"]),
        help="A list of the categories of inputs and outputs that should "
        "be enabled"
    )(f)
    f = click.option(
        "-f", "--modules_file", type=click.File(),
        help="JSON file describing the modules to include in the generated "
        "code"
    )(f)
    f = click.option(
        "-p", "--plugin", multiple=True, help="Enable a specific plugin"
    )(f)
    f = click.option(
        "-t", "--target", help="PlatformIO target (e.g.  upload)"
    )(f)
    f = click.option(
        "--status_update_interval", default=5,
        help="Minimum interval between driver status updates (in seconds)"
    )(f)
    return f

@click.group("firmware")
def firmware():
    """ Tools for dealing with firmware modules """

@firmware.command()
@board_option
@project_dir_option
def init(board, project_dir, **kwargs):
    """ Initialize an OpenAg-based project """
    project_dir = os.path.abspath(project_dir)

    # Initialize the platformio project
    click.echo("Initializing PlatformIO project")
    with open("/dev/null", "wb") as null:
        try:
            init = subprocess.Popen(
                ["platformio", "init", "-b", board], stdin=subprocess.PIPE,
                stdout=null, cwd=project_dir
            )
            init.communicate("y\n")
        except OSError as e:
            raise RuntimeError("PlatformIO is not installed")
    if init.returncode != 0:
        raise RuntimeError(
            "Failed to initialize PlatformIO project"
        )

    # Create an empty modules.json file
    modules_path = os.path.join(project_dir, "modules.json")
    with open(modules_path, "w+") as f:
        json.dump({}, f)
    click.echo("OpenAg firmware project initialized!")

@firmware.command()
@project_dir_option
@codegen_options
def run(
    categories, modules_file, project_dir, plugin, target,
    status_update_interval
):
    """ Generate code for this project and run it """
    project_dir = os.path.abspath(project_dir)

    # Make sure the project has been initialized
    pio_config = os.path.join(project_dir, "platformio.ini")
    if not os.path.isfile(pio_config):
        raise click.ClickException(
            "Not an OpenAg firmware project. To initialize a new project "
            "please use the `openag firmware init` command"
        )

    # Get the list of module types
    module_types = {}
    # Read from the local couchdb server
    local_server = config["local_server"]["url"]
    if local_server:
        server = Server(local_server)
        db = server[FIRMWARE_MODULE_TYPE]
        for _id in db:
            if _id.startswith("_"):
                continue
            click.echo(
                "Parsing firmware module type \"{}\" from server".format(_id)
            )
            module_types[_id] = FirmwareModuleType(db[_id])
    # Check for working modules in the lib folder
    # Do this second so project-local values overwrite values from the server
    lib_path = os.path.join(project_dir, "lib")
    for dir_name in os.listdir(lib_path):
        dir_path = os.path.join(lib_path, dir_name)
        if not os.path.isdir(dir_path):
            continue
        config_path = os.path.join(dir_path, "module.json")
        if os.path.isfile(config_path):
            with open(config_path) as f:
                click.echo(
                    "Parsing firmware module type \"{}\" from lib "
                    "folder".format(dir_name)
                )
                module_types[dir_name] = FirmwareModuleType(json.load(f))

    # Update the module types using the categories
    for mod_name, mod_info in module_types.items():
        for output_name, output_info in mod_info["outputs"].items():
            for c in output_info["categories"]:
                if c in categories:
                    break
            else:
                del mod_info["outputs"][output_name]
        for input_name, input_info in mod_info["inputs"].items():
            for c in input_info["categories"]:
                if c in categories:
                    break
            else:
                del mod_info["inputs"][input_name]

    # Get the list of modules
    modules = {}
    # Read from the local couchdb server
    if modules_file:
        _modules = json.load(modules_file)
        for _id, info in _modules.items():
            click.echo(
                "Parsing firmware module \"{}\" from modules file".format(_id)
            )
            modules[_id] = FirmwareModule(info)
    elif local_server:
        db = server[FIRMWARE_MODULE]
        for _id in db:
            if _id.startswith("_"):
                continue
            click.echo("Parsing firmware module \"{}\"".format(_id))
            modules[_id] = FirmwareModule(db[_id])
    else:
        raise click.ClickException("No modules specified for the project")

    # Populate the modules with data from their types
    for mod_id, mod_info in modules.items():
        mod_type = module_types[mod_info["type"]]
        if "pio_id" in mod_type:
            mod_info["pio_id"] = mod_type["pio_id"]
        if "repository" in mod_type:
            mod_info["repository"] = mod_type["repository"]
        mod_info["header_file"] = mod_type["header_file"]
        mod_info["class_name"] = mod_type["class_name"]
        # Update the arguments
        args = list(mod_info.get("arguments", []))
        if len(args) > len(mod_type["arguments"]):
            raise click.ClickException(
                'Too many arguments specified for module "{}". (Got {}, '
                'expected {})'.format(
                    mod_id, len(args), len(mod_type["arguments"])
                )
            )
        for i in range(len(args), len(mod_type["arguments"])):
            arg_info = mod_type["arguments"][i]
            if "default" in arg_info:
                args.append(arg_info["default"])
            else:
                raise click.ClickException(
                    'Not enough module arguments supplied for module "{}" '
                    '(Got {}, expecting {})'.format(
                        mod_id, len(args), len(mod_type["arguments"])
                    )
                )
        mod_info["arguments"] = args
        # Apply mappings to inputs and outputs
        mappings = mod_info.get("mappings", {})
        mod_inputs = {}
        for input_name, input_info in mod_type["inputs"].items():
            if input_name in mappings:
                mapped_name = mappings[input_name]
            else:
                mapped_name = input_name
            real_input_info = dict(input_info)
            real_input_info["mapped_name"] = mapped_name
            mod_inputs[input_name] = real_input_info
        mod_info["inputs"] = mod_inputs
        mod_outputs = {}
        for output_name, output_info in mod_type["outputs"].items():
            if output_name in mappings:
                mapped_name = mappings[output_name]
            else:
                mapped_name = output_name
            real_output_info = dict(output_info)
            real_output_info["mapped_name"] = mapped_name
            mod_outputs[output_name] = real_output_info
        mod_info["outputs"] = mod_outputs

    # Generate src.ino
    src_dir = os.path.join(project_dir, "src")
    src_file_path = os.path.join(src_dir, "src.ino")
    # Create the plugins
    plugins = []
    for plugin_name in plugin:
        plugin_cls = plugin_map.get(plugin_name, None)
        if not plugin_cls:
            try:
                plugin_module_name, plugin_cls_name = plugin_name.split(":")
                plugin_module = import_module(plugin_module_name)
                plugin_cls = getattr(plugin_module, plugin_cls_name)
            except ValueError:
                raise click.ClickException(
                    '"{}" is not a valid plugin path'.format(plugin_name)
                )
            except ImportError:
                raise click.ClickException(
                    '"{}" does not name a Python module'.format(
                        plugin_module_name
                    )
                )
            except AttributeError:
                raise click.ClickException(
                    'Module "{}" does not contain the class "{}"'.format(
                        plugin_module_name, plugin_cls_name
                    )
                )
        plugins.append(plugin_cls(modules))

    # Generate the code
    codegen = CodeGen(
        modules=modules, plugins=plugins,
        status_update_interval=status_update_interval
    )
    for dep in codegen.all_pio_dependencies():
        subprocess.call(["platformio", "lib", "install", str(dep)])
    lib_dir = os.path.join(project_dir, "lib")
    for dep in codegen.all_git_dependencies():
        subprocess.call(["git", "clone", dep], cwd=lib_dir)
    with open(src_file_path, "w+") as f:
        codegen.write_to(f)

    # Compile the generated code
    command = ["platformio", "run"]
    if target:
        command.append("-t")
        command.append(target)
    if subprocess.call(command, cwd=project_dir):
        raise click.ClickException("Compilation failed")

@firmware.command()
@click.argument("arguments", nargs=-1)
@board_option
@project_dir_option
@codegen_options
@click.pass_context
def run_module(
    ctx, arguments, project_dir, board, **kwargs
):
    """ Run a single instance of this module """

    # Read the module config
    here = os.path.abspath(project_dir)
    module_json_path = os.path.join(here, "module.json")
    try:
        with open(module_json_path) as f:
            module_type = FirmwareModuleType(json.load(f))
    except IOError:
        raise click.ClickException("No module.json file found")

    # Create the build directory
    build_path = os.path.join(here, "_build")
    if not os.path.isdir(build_path):
        os.mkdir(build_path)
    kwargs["project_dir"] = build_path

    # Initialize an openag project in the build directory
    ctx.invoke(init, board=board, **kwargs)

    # Link the source files into the lib directory
    lib_path = os.path.join(build_path, "lib")
    module_path = os.path.join(lib_path, "module")
    if not os.path.isdir(module_path):
        os.mkdir(module_path)
    for file_name in os.listdir(here):
        file_path = os.path.join(here, file_name)
        if not os.path.isfile(file_path) or file_name.startswith("."):
            continue
        source = "../../../{}".format(file_name)
        link_name = os.path.join(module_path, file_name)
        if os.path.isfile(link_name):
            os.remove(link_name)
        os.symlink(source, link_name)

    # Parse the arguments based on the module type
    real_args = []
    for i in range(len(arguments)):
        if i >= len(module_type["arguments"]):
            raise click.ClickException(
                "Too many module arguments specified. (Got {}, expected "
                "{})".format(len(arguments), len(module_type["arguments"]))
            )
        val = arguments[i]
        arg_info = module_type["arguments"][i]
        if arg_info["type"] == "int":
            val = int(val)
        elif arg_info["type"] == "float":
            val = float(val)
        elif arg_info["type"] == "bool":
            if val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            else:
                raise click.BadParameter(
                    "Argument number {} should be a boolean value "
                    '("true" or "false")'.format(i)
                )
        real_args.append(val)

    # Write the modules.json file
    modules = {
        "module": FirmwareModule({
            "type": "module",
            "arguments": list(real_args)
        })
    }
    modules_file = os.path.join(build_path, "modules.json")
    with open(modules_file, "w") as f:
        json.dump(modules, f)
    with open(modules_file, "r") as f:
        kwargs["modules_file"] = f
        # Run the project
        ctx.invoke(run, **kwargs)

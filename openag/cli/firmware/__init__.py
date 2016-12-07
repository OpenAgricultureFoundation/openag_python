import os
import sys
import json
import click
import subprocess
from importlib import import_module
from voluptuous import Invalid
from ConfigParser import ConfigParser

from base import CodeGen
from plugins import plugin_map
from ..config import config
from openag.couch import Server
from openag.utils import (
    synthesize_firmware_module_info, make_dir_name_from_url, index_by_id,
    parent_dirname
)
from openag.models import FirmwareModuleType, FirmwareModule
from openag.db_names import FIRMWARE_MODULE_TYPE, FIRMWARE_MODULE
from openag.categories import all_categories, SENSORS, ACTUATORS, CALIBRATION

PLATFORMIO_CONFIG = "platformio.ini"

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
        "-c", "--categories", multiple=True, default=[SENSORS, ACTUATORS],
        type=click.Choice([SENSORS, ACTUATORS, CALIBRATION]),
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
    pio_config_path = os.path.join(project_dir, "platformio.ini")
    if not os.path.isfile(pio_config_path):
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

    firmware_types = []
    firmware = []

    local_server = config["local_server"]["url"]
    server = Server(local_server) if local_server else None
    modules_json = json.load(modules_file) if modules_file else {}

    if modules_json.get(FIRMWARE_MODULE_TYPE):
        for module in modules_json[FIRMWARE_MODULE_TYPE]:
            click.echo(
                "Parsing firmware module type \"{}\" from modules file"
                .format(module["_id"])
            )
            firmware_types.append(FirmwareModuleType(module))
    elif server:
        db = server[FIRMWARE_MODULE_TYPE]
        for _id in db:
            if _id.startswith("_"):
                continue
            click.echo(
                "Parsing firmware module type \"{}\" from server".format(_id)
            )
            firmware_types.append(FirmwareModuleType(db[_id]))

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
                doc = json.load(f)
                if not doc.get("_id"):
                    # Patch in id if id isn't present
                    doc["_id"] = parent_dirname(config_path)
                firmware_types.append(FirmwareModuleType(doc))

    # Get the list of modules
    if modules_json.get(FIRMWARE_MODULE):
        for module in modules_json[FIRMWARE_MODULE]:
            click.echo(
                "Parsing firmware module \"{}\" from modules file"
                .format(module["_id"])
            )
            firmware.append(FirmwareModule(module))
    elif server:
        db = server[FIRMWARE_MODULE]
        for _id in db:
            if _id.startswith("_"):
                continue
            click.echo("Parsing firmware module \"{}\" from server".format(_id))
            firmware.append(FirmwareModule(db[_id]))

    if len(firmware) == 0:
        click.echo("Warning: no modules specified for the project")

    module_types = index_by_id(firmware_types)
    modules = index_by_id(firmware)
    # Synthesize the module and module type dicts
    modules = synthesize_firmware_module_info(modules, module_types)
    # Update the module inputs and outputs using the categories
    modules = prune_unspecified_categories(modules, categories)

    # Generate src.ino
    src_dir = os.path.join(project_dir, "src")
    src_file_path = os.path.join(src_dir, "src.ino")
    # Load the plugins
    plugin_fns = (load_plugin(plugin_name) for plugin_name in plugin)
    # Run modules through each plugin
    plugins = [plugin_fn(modules) for plugin_fn in plugin_fns]

    # Generate the code
    codegen = CodeGen(
        modules=modules, plugins=plugins,
        status_update_interval=status_update_interval
    )
    pio_ids = (dep["id"] for dep in codegen.all_pio_dependencies())
    for _id in pio_ids:
        subprocess.call(["platformio", "lib", "install", str(_id)])
    lib_dir = os.path.join(project_dir, "lib")
    for dep in codegen.all_git_dependencies():
        url = dep["url"]
        branch = dep.get("branch", "master")
        dep_folder_name = make_dir_name_from_url(url)
        dep_folder = os.path.join(lib_dir, dep_folder_name)
        if os.path.isdir(dep_folder):
            click.echo('Updating "{}"'.format(dep_folder_name))
            subprocess.call(
                ["git", "checkout", "--quiet", branch], cwd=dep_folder)
            subprocess.call(["git", "pull"], cwd=dep_folder)
        else:
            click.echo('Downloading "{}"'.format(dep_folder_name))
            subprocess.call(
                ["git", "clone", "-b", branch, url, dep_folder], cwd=lib_dir)
    with open(src_file_path, "w+") as f:
        codegen.write_to(f)

    # Compile the generated code
    command = ["platformio", "run"]
    if target:
        command.append("-t")
        command.append(target)
    env = os.environ.copy()
    build_flags = []
    for c in categories:
        build_flags.append("-DOPENAG_CATEGORY_{}".format(c.upper()))
    env["PLATFORMIO_BUILD_FLAGS"] = " ".join(build_flags)
    if subprocess.call(command, cwd=project_dir, env=env):
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
    """
    Run a single instance of this module. [ARGUMENTS] specifies a list of
    implementation-specific arguments to the module (for example, configuring
    Arduino pin numbers for the module).

    Example:

    \b
    openag firmware run_module -t upload 4

    This command fetches module definitions from CouchDB. CouchDB must be
    running on port 5984 and the firmware_module_type database populated with
    appropriate type records for this command to work. Loading the default
    fixture from openag_brain will populate a default set of
    firmware_module_type records.
    """
    # Read the module config
    here = os.path.abspath(project_dir)
    module_json_path = os.path.join(here, "module.json")
    try:
        with open(module_json_path) as f:
            doc = json.load(f)
            if not doc.get("_id"):
                # Patch in id if not present
                doc["_id"] = parent_dirname(module_json_path)
            module_type = FirmwareModuleType(doc)
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
        FIRMWARE_MODULE: [
            FirmwareModule({
                "_id": "module_1",
                "type": "module",
                "arguments": list(real_args)
            })
        ]
    }
    modules_file = os.path.join(build_path, "modules.json")
    with open(modules_file, "w") as f:
        json.dump(modules, f)
    with open(modules_file, "r") as f:
        kwargs["modules_file"] = f
        # Run the project
        ctx.invoke(run, **kwargs)

def prune_unspecified_categories(modules, categories):
    """
    Removes unspecified module categories.
    Mutates dictionary and returns it.
    """
    for mod_name, mod_info in modules.items():
        for input_name, input_info in mod_info["inputs"].items():
            for c in input_info["categories"]:
                if c in categories:
                    break
            else:
                del mod_info["inputs"][input_name]
        for output_name, output_info in mod_info["outputs"].items():
            for c in output_info["categories"]:
                if c in categories:
                    break
            else:
                del mod_info["outputs"][output_name]
    return modules

def load_plugin(plugin_name):
    """
    Given a plugin name, load plugin cls from plugin directory.
    Will throw an exception if no plugin can be found.
    """
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
    return plugin_cls

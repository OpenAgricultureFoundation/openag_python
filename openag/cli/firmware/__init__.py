import os
import sys
import json
import click
import subprocess
from voluptuous import Invalid

from .codegen import CodeGen
from .codegen.plugins import plugin_map
from openag.models import FirmwareModuleType, FirmwareModule

@click.group("firmware")
def firmware():
    """ Tools for dealing with firmware modules """
    pass

@firmware.command()
@click.option(
    "-b", "--board", default="megaatmega2560",
    help="The board to use for compilation. Defaults to megaatmega2560 "
    "(Arduino Mega 2560)"
)
@click.option(
    "-d", "--project-dir", default=".",
    help="The directory in which the project should reside"
)
def init(board, project_dir, **kwargs):
    """ Initialize an OpenAg-based project """
    project_dir = os.path.abspath(project_dir)

    # Initialize the platformio project
    init = subprocess.Popen(
        ["platformio", "init", "-b", board], stdin=subprocess.PIPE,
        cwd=project_dir
    )
    init.communicate("y\n")
    if (init.wait()):
        raise RuntimeError(
            "Failed to initialize PlatformIO project"
        )

    # Create an empty modules.json file
    modules_path = os.path.join(project_dir, "modules.json")
    with open(modules_path, "w+") as f:
        json.dump({}, f)

@firmware.command()
@click.option(
    "-b", "--board", default="megaatmega2560",
    help="The board to use for compilaton. Defaults to megaatmega2560 "
    "(Arduino Mega 2560)"
)
@click.option(
    "-c", "--categories", multiple=True, default=["sensors", "actuators"],
    type=click.Choice(["sensors", "actuators", "calibration"]),
    help="A list of the categories of inputs and outputs that should be "
    "enabled"
)
@click.option(
    "-d", "--project-dir", default=".",
    help="The directory in which the project should reside"
)
@click.option("-p", "--plugin", multiple=True, help="Enable a specific plugin")
@click.option("-t", "--target", help="PlatformIO target (e.g. upload)")
@click.option(
    "--status_update_interval", default=5,
    help="Minimum interval between driver status updates (in seconds)"
)
def run(
    board, categories, project_dir, plugin, target, status_update_interval
):
    """ Generate code for this project and run it """
    project_dir = os.path.abspath(project_dir)

    # Get the list of modules
    modules_path = os.path.join(project_dir, "modules.json")
    with open(modules_path) as f:
        modules = json.load(f)

    # Get the list of module types
    module_types = {}
    lib_path = os.path.join(project_dir, "lib")
    for dir_name in os.listdir(lib_path):
        dir_path = os.path.join(lib_path, dir_name)
        if not os.path.isdir(dir_path):
            continue
        config_path = os.path.join(dir_path, "module.json")
        if os.path.isfile(config_path):
            with open(config_path) as f:
                module_types[dir_name] = FirmwareModuleType(json.load(f))

    # Update the module types using the categories
    for mod_name, mod_info in module_types.items():
        for output_name, output_info in mod_info["outputs"].items():
            for c in output_info["categories"]:
                if c in categories:
                    break
            else:
                del mod_info["outputs"][output_name]
        for input_name, input_info in mod_info["inputs"]:
            for c in input_info["categories"]:
                if c in categories:
                    break
            else:
                del mod_info["inputs"][input_name]

    # Generate src.ino
    src_dir = os.path.join(project_dir, "src")
    src_file_path = os.path.join(src_dir, "src.ino")
    try:
        plugins = [
            plugin_map[plugin_name](modules, module_types) for plugin_name in
            plugin
        ]
    except KeyError as e:
        raise click.ClickException(
            'Plugin "{}" does not exist'.format(e.args[0])
        )
    codegen = CodeGen(
        modules=modules, module_types=module_types, plugins=plugins,
        status_update_interval=status_update_interval
    )
    for dep in codegen.dependencies():
        subprocess.call(["platformio", "lib", "install", str(dep)])
    with open(src_file_path, "w+") as f:
        codegen.write_to(f)

    # Compile the generated code
    command = ["platformio", "run"]
    if target:
        command.append("-t")
        command.append(target)
    subprocess.call(command, cwd=project_dir)

@firmware.command()
@click.argument("arguments", nargs=-1)
@click.option(
    "-b", "--board", default="megaatmega2560",
    help="The board to use for compilaton. Defaults to megaatmega2560 "
    "(Arduino Mega 2560)"
)
@click.option(
    "-c", "--categories", multiple=True, default=["sensors", "actuators"],
    type=click.Choice(["sensors", "actuators", "calibration"]),
    help="A list of the categories of inputs and outputs that should be "
    "enabled"
)
@click.option("-p", "--plugin", multiple=True, help="Enable a specific plugin")
@click.option("-t", "--target", help="PlatformIO target (e.g. upload)")
@click.option(
    "--status_update_interval", default=5,
    help="Minimum interval between driver status updates (in seconds)"
)
@click.pass_context
def run_module(
    ctx, board, categories, plugin, target, status_update_interval,
    arguments
):
    """ Run a single instance of this module """
    # Read the module config
    with open("module.json") as f:
        module_type = FirmwareModuleType(json.load(f))

    # Parse the module arguments
    real_args = []
    i = 0
    for arg_info in module_type["arguments"]:
        if i >= len(arguments):
            if "default" in arg_info:
                real_args.append(arg_info["default"])
            else:
                raise click.ClickException(
                    "Not enough module arguments supplied (expecting {})".format(
                        len(module_type["arguments"])
                    )
                )
        else:
            val = arguments[i]
            if arg_info["type"] == "int":
                val = int(val)
            if arg_info["type"] == "bool":
                if val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                else:
                    raise click.BadParameter(
                        "Argument number {} should be a boolean value "
                        '("true" or "false")'.format(i+1)
                    )
            real_args.append(val)
        i += 1

    # Create the build directory
    here = os.getcwd()
    build_path = os.path.join(here, "_build")
    if not os.path.isdir(build_path):
        os.mkdir(build_path)

    # Initialize an openag project in the build directory
    ctx.invoke(init, board=board, project_dir=build_path)

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

    # Write the modules.json file
    modules = {
        "module": FirmwareModule({
            "type": "module",
            "arguments": real_args
        })
    }
    modules_file = os.path.join(build_path, "modules.json")
    with open(modules_file, "w") as f:
        json.dump(modules, f)

    # Run the project
    ctx.invoke(
        run, board=board, categories=categories, plugin=plugin, target=target,
        project_dir=build_path, status_update_interval=status_update_interval
    )

import os
import sys
import json
import click
import subprocess
from voluptuous import Invalid

from .codegen import CodeGen
from openag.models import FirmwareModuleType, FirmwareModule

@click.group("firmware")
def firmware_commands():
    """ Tools for dealing with firmware modules """
    pass

@firmware_commands.command()
def init():
    raise NotImplementedError()

@firmware_commands.command()
def run():
    raise NotImplementedError()

@firmware_commands.command()
def clean():
    raise NotImplementedError()

@firmware_commands.group()
def module():
    """ Tools for developing an individual module """
    pass

@module.command(context_settings=dict(ignore_unknown_options=True))
@click.option(
    "-b", "--board", default="megaatmega2560",
    help="The board to use for compilaton. Defaults to megaatmega2560 "
    "(Arduino Mega 2560)"
)
@click.option(
    "-c", "--config", type=click.File(), default="module.json",
    help="Path to the json file describing the module to run. Defaults to "
    "module.json"
)
@click.option("-t", "--target", help="PlatformIO target (e.g. upload)")
@click.argument("values", nargs=-1, type=click.UNPROCESSED)
def run(config, board, target, values):
    """
    Generate and run Arduino code for this module
    """
    # Parse the module.json file
    try:
        module_types = {
            "module": FirmwareModuleType(json.load(config))
        }
    except Invalid as e:
        sys.stderr.write("Invalid module configuration\n")
        raise e

    # Parse the command line arguments
    arguments = []
    parameters = {}
    i = 0
    while i < len(values):
        if values[i].startswith("-"): # Treat it as a parameter
            param_name = values[i][values[i].rfind("-")+1:]
            i += 1
            param_value = values[i]
            parameters[param_name] = param_value
        else: # Treat it as an argument
            if parameters:
                raise ValueError("Invalid command line arguments")
            arguments.append(values[i])
        i += 1
    modules = {
        "module": FirmwareModule({
            "type": "module",
            "arguments": arguments,
            "parameters": parameters
        })
    }

    # Create the build directory
    here = os.getcwd()
    build_path = os.path.join(here, "_build")
    if not os.path.isdir(build_path):
        os.mkdir(build_path)

    # Initialize a platformio project in the build directory
    init = subprocess.Popen(
        ["platformio", "init", "-b", board], stdin=subprocess.PIPE,
        stdout=open(os.devnull, 'wb'), cwd=build_path
    )
    init.communicate("y\n")
    init.wait()

    # Create the src directory
    src_path = os.path.join(build_path, "src")
    if not os.path.isdir(src_path):
        os.mkdir(src_path)

    # Link the source files into the lib directory
    lib_path = os.path.join(build_path, "lib")
    if not os.path.isdir(lib_path):
        os.mkdir(lib_path)
    module_path = os.path.join(lib_path, "module")
    if not os.path.isdir(module_path):
        os.mkdir(module_path)
    for file_name in os.listdir("."):
        if not os.path.isfile(file_name) or file_name.startswith("."):
            continue
        if file_name.endswith(".cpp") or file_name.endswith(".h"):
            source = "../../../{}".format(file_name)
            link_name = os.path.join(module_path, file_name)
            if os.path.islink(link_name):
                os.remove(link_name)
            os.symlink(source, link_name)

    # Generate src.ino
    src_file_path = os.path.join(src_path, "src.ino")
    codegen = CodeGen(modules, module_types)
    with open(src_file_path, "w+") as f:
        codegen.write_to(f)

    # Compile the generated code
    command = ["pio", "run"]
    if target:
        command.append("-t")
        command.append(target)
    subprocess.call(command, cwd=build_path)

@module.command()
def clean():
    """ Deletes the build directory """
    raise NotImplementedError()

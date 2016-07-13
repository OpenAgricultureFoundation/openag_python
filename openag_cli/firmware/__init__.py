import json
import click

@click.group()
def firmware():
    """ Tools for dealing with firmware modules """
    pass

@firmware.command()
@click.argument("module_json", type=click.File(), default="module.json")
def run_module(module_json):
    """
    Generate Arduino code for this module and run it
    """
    module_type = json.load(module_json)
    module_types = {
        "module": module_type
    }
    modules = {
        "module": {
        }
    }
    click.echo(module_types)

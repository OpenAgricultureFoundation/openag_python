import json
import click

from .firmware import firmware
from . import models

@click.group()
def main():
    """ Command Line Interface for OpenAg software """
    pass

@main.command()
def create_user():
    raise NotImplementedError()

@main.command()
def register_farm():
    raise NotImplementedError()

@main.command()
def log_in():
    raise NotImplementedError()

@main.command()
def log_out():
    raise NotImplementedError()

main.add_command(firmware)

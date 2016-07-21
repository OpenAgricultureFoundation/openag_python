import click

@click.group()
def main():
    """ Command Line Interface for OpenAg software """
    pass

from .cloud import cloud
from .farms import farms
from .firmware import firmware
main.add_command(cloud)
main.add_command(farms)
main.add_command(firmware)

import json
import click

from .firmware import firmware

@click.group()
def main():
    """ Command Line Interface for OpenAg software """
    pass

main.add_command(firmware)

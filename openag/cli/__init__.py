import click

@click.group()
def main():
    """ Command Line Interface for OpenAg software """
    pass

from db import db
from cloud import cloud
from firmware import firmware
main.add_command(db)
main.add_command(cloud)
main.add_command(firmware)

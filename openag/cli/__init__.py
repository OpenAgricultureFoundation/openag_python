import click

@click.group()
def main():
    """ Command Line Interface for OpenAg software """

from db import db as db_commands
from farm import farm as farm_commands
from user import user as user_commands
from cloud import cloud as cloud_commands
from firmware import firmware as firmware_commands
main.add_command(db_commands)
main.add_command(farm_commands)
main.add_command(user_commands)
main.add_command(cloud_commands)
main.add_command(firmware_commands)

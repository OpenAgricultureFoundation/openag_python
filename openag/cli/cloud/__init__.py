import click

from .db import init, show, deinit
from .user import register, login, logout
from .farm import create_farm, list_farms, init_farm, deinit_farm

@click.group()
def cloud():
    """
    Manage your cloud server.

    Provides commands for selecting a cloud server with which to exchange grow
    data, managing your user account on that
    """

cloud.add_command(init)
cloud.add_command(show)
cloud.add_command(deinit)

cloud.add_command(register)
cloud.add_command(login)
cloud.add_command(logout)

cloud.add_command(create_farm)
cloud.add_command(list_farms)
cloud.add_command(init_farm)
cloud.add_command(deinit_farm)

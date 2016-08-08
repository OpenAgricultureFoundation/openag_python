import click

from openag.couch import Server
from .farm import deinit_farm
from ..utils import check_for_cloud_server, check_for_cloud_user
from ..config import config

@click.command()
@click.option("--username", prompt=True, help="Username for the account")
@click.option(
    "--password", prompt=True, hide_input=True, confirmation_prompt=True,
    help="Password for the account"
)
def register(username, password):
    """
    Create a new user account. Creates a user account with the given
    credentials on the selected cloud server.
    """
    check_for_cloud_server()
    server = Server(config["cloud_server"]["url"])
    server.create_user(username, password)

@click.command()
@click.option("--username", prompt=True, help="Username for the account")
@click.option(
    "--password", prompt=True, hide_input=True, help="Password for the account"
)
def login(username, password):
    """ Log into your user account """
    check_for_cloud_server()
    old_username = config["cloud_server"]["username"]
    if old_username and old_username != username:
        raise click.ClickException(
            "Already logged in as user \"{}\". Run `openag cloud user logout` "
            "before attempting to log in as a different user".format(
                old_username
            )
        )
    server = Server(config["cloud_server"]["url"])
    server.log_in(username, password)
    config["cloud_server"]["username"] = username
    config["cloud_server"]["password"] = password

@click.command()
@click.pass_context
def logout(ctx):
    """ Log out of your user account """
    check_for_cloud_server()
    check_for_cloud_user()
    if config["cloud_server"]["farm_name"]:
        ctx.invoke(deinit_farm)
    config["cloud_server"]["username"] = None
    config["cloud_server"]["password"] = None

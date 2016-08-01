import click

from openag.couchdb import Server
from ..config import Config
from ..utils import check_for_cloud_server, check_for_cloud_user

@click.group()
def user():
    """ Manage your cloud user account """
    pass

@user.command()
def show():
    """ Show info about your user account """
    config = Config()
    check_for_cloud_server()
    check_for_cloud_user()
    click.echo(
        "Logged in as user \"{}\"".format(config["cloud_server"]["username"])
    )

@user.command()
@click.option("--username", prompt=True, help="Username for the account")
@click.option(
    "--password", prompt=True, hide_input=True, confirmation_prompt=True,
    help="Password for the account"
)
def register(username, password):
    """ Create a new user account """
    config = Config()
    check_for_cloud_server()
    server = Server(config["cloud_server"]["url"])
    server.create_user(username, password)

@user.command()
@click.option("--username", prompt=True, help="Username for the account")
@click.option(
    "--password", prompt=True, hide_input=True, help="Password for the account"
)
def login(username, password):
    """ Log into your user account """
    config = Config()
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

@user.command()
def logout():
    """ Log out of your user account """
    config = Config()
    check_for_cloud_server()
    check_for_cloud_user()
    del config["cloud_server"]["username"]
    del config["cloud_server"]["password"]

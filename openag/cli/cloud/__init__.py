import click
from urlparse import urlparse

from .farm import unselect as unselect_farm
from ..utils import *
from ..config import config

@click.group()
def cloud():
    """
    Manage your cloud configuration.

    Provides commands for selecting a cloud server with which to exchange data
    and setting up that exchange.
    """
    pass

@cloud.command()
@click.argument("cloud_url")
def init(cloud_url):
    """
    Choose a cloud server to use. Sets CLOUD_URL as the cloud server to use and
    sets up replication of global databases from that cloud server if a local
    database is already initialized (via `openag db init`).
    """
    old_cloud_url = config["cloud_server"]["url"]
    if old_cloud_url and old_cloud_url != cloud_url:
        raise click.ClickException(
            'Server "{}" already selected. Call `openag cloud remove` to '
            'detach from that server before selecting a new one'.format(
                old_cloud_url
            )
        )
    parsed_url = urlparse(cloud_url)
    if not parsed_url.scheme or not parsed_url.netloc or not parsed_url.port:
        raise click.BadParameter("Invalid url")
    if config["local_server"]["url"]:
        replicate_global_dbs(cloud_url=cloud_url)
    config["cloud_server"]["url"] = cloud_url

@cloud.command()
def show():
    """
    Shows the URL of the current cloud server
    """
    check_for_cloud_server()
    click.echo("Using cloud server at \"{}\"".format(
        config["cloud_server"]["url"]
    ))

@cloud.command()
@click.pass_context
def remove(ctx):
    """
    Detach from the current cloud server
    """
    check_for_cloud_server()
    if config["local_server"]["url"]:
        replicate_global_dbs(
            cloud_url=config["cloud_server"]["url"], cancel=True
        )
        if config["cloud_server"]["farm_name"]:
            ctx.invoke(unselect_farm)
    del config["cloud_server"]["url"]

from .user import user
from .farm import farm
cloud.add_command(user)
cloud.add_command(farm)

import click
from urlparse import urlparse

from .. import utils
from ..config import config
from .user import logout as logout_user

@click.command()
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
            'Server "{}" already selected. Call `openag cloud deinit` to '
            'detach from that server before selecting a new one'.format(
                old_cloud_url
            )
        )
    parsed_url = urlparse(cloud_url)
    if not parsed_url.scheme or not parsed_url.netloc or not parsed_url.port:
        raise click.BadParameter("Invalid url")
    if config["local_server"]["url"]:
        utils.replicate_global_dbs(cloud_url=cloud_url)
    config["cloud_server"]["url"] = cloud_url

@click.command()
def show():
    """
    Shows the URL of the current cloud server or throws an error if no cloud
    server is selected
    """
    utils.check_for_cloud_server()
    click.echo("Using cloud server at \"{}\"".format(
        config["cloud_server"]["url"]
    ))
    if config["cloud_server"]["username"]:
        click.echo(
            "Logged in as user \"{}\"".format(config["cloud_server"]["username"])
        )
    if config["cloud_server"]["farm_name"]:
        click.echo(
            "Using farm \"{}\"".format(config["cloud_server"]["farm_name"])
        )

@click.command()
@click.pass_context
def deinit(ctx):
    """
    Detach from the current cloud server
    """
    utils.check_for_cloud_server()
    if config["local_server"]["url"]:
        utils.cancel_global_db_replication()
    if config["cloud_server"]["username"]:
        ctx.invoke(logout_user)
    config["cloud_server"]["url"] = None

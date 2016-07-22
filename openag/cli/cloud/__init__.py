import click
from urlparse import urlparse

from ..utils import *
from ..config import Config

@click.group()
def cloud():
    """ Manage your cloud configuration """
    pass

@cloud.command()
@click.argument("cloud_url")
def init(cloud_url):
    """ Choose a cloud server to use """
    config = Config()
    old_cloud_url = config["cloud_server"]["url"]
    if old_cloud_url:
        raise click.ClickException(
            "Server \"{}\" already selected. Switching cloud servers is not "
            "supported at this time".format(old_cloud_url)
        )
    parsed_url = urlparse(cloud_url)
    if not parsed_url.scheme or not parsed_url.netloc or not parsed_url.port:
        raise click.BadParameter("Invalid url")
    if config["local_server"]["url"]:
        replicate_global_dbs(config, cloud_url=cloud_url)
    config["cloud_server"]["url"] = cloud_url

@cloud.command()
def show():
    """ Show info about the cloud server """
    config = Config()
    check_for_cloud_server(config)
    click.echo("Using cloud server at \"{}\"".format(
        config["cloud_server"]["url"]
    ))

from .user import user
from .farm import farm
cloud.add_command(user)
cloud.add_command(farm)

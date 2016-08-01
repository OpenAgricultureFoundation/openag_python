import click

from openag.couchdb import Server
from ..utils import *
from ..config import config

@click.group()
def farm():
    """ Manage the cloud mirror of your data """
    pass

@farm.command()
def show():
    """ Show the current configuration """
    check_for_cloud_server()
    check_for_cloud_user()
    check_for_cloud_farm()
    click.echo(
        "Using farm \"{}\" under user \"{}\"".format(
            config["cloud_server"]["farm_name"],
            config["cloud_server"]["username"]
        )
    )

@farm.command()
@click.argument("farm_name")
def create(farm_name):
    """ Create a farm """
    check_for_cloud_server()
    check_for_cloud_user()
    server = Server(config["cloud_server"]["url"])
    username = config["cloud_server"]["username"]
    password = config["cloud_server"]["password"]
    server.log_in(username, password)
    res = server.post(
        "/_openag/v0.1/register_farm", data={
            "name": username,
            "farm_name": farm_name
        }
    )
    if not res.status_code == 200:
        raise click.ClickException(
            "Failed to register farm with cloud server ({}): {}".format(
                res.status_code, res.content
            )
        )

@farm.command()
def list():
    """ List all farms you can manage """
    check_for_cloud_server()
    check_for_cloud_user()
    server = Server(config["cloud_server"]["url"])
    server.log_in(
        config["cloud_server"]["username"], config["cloud_server"]["password"]
    )
    farms_list = server.get_user_info().get("farms", [])
    if not len(farms_list):
        raise click.ClickException(
            "No farms exist. Run `openag cloud farms create` to create one"
        )
    active_farm_name = config["cloud_server"]["farm_name"]
    for farm_name in farms_list:
        if farm_name == active_farm_name:
            click.echo("*"+farm_name)
        else:
            click.echo(farm_name)

@farm.command()
@click.argument("farm_name")
def select(farm_name):
    """ Select a farm to manage """
    check_for_cloud_server()
    check_for_cloud_user()
    old_farm_name = config["cloud_server"]["farm_name"]
    if old_farm_name and old_farm_name != farm_name:
        raise click.ClickException(
            "Farm \"{}\" already selected. Switching farms is not supported "
            "at this time".format(old_farm_name)
        )
    if config["local_server"]["url"]:
        replicate_per_farm_dbs(config, farm_name=farm_name)
    config["cloud_server"]["farm_name"] = farm_name

@farm.command()
def unselect():
    """
    Detach from the current farm
    """
    check_for_cloud_server()
    check_for_cloud_user()
    check_for_cloud_farm()
    farm_name = config["cloud_server"]["farm_name"]
    if farm_name and config["local_server"]["url"]:
        replicate_per_farm_dbs(config, farm_name=farm_name)
    config["cloud_server"]["farm_name"] = None

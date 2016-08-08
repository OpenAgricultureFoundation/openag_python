import json
import click
from couchdb.http import urljoin

from openag.couch import Server
from .. import utils
from ..config import config

@click.command()
@click.argument("farm_name")
def create_farm(farm_name):
    """
    Create a farm. Creates a farm named FARM_NAME on the currently selected
    cloud server. You can use the `openag cloud select_farm` command to start
    mirroring data into it.
    """
    utils.check_for_cloud_server()
    utils.check_for_cloud_user()
    server = Server(config["cloud_server"]["url"])
    username = config["cloud_server"]["username"]
    password = config["cloud_server"]["password"]
    server.log_in(username, password)
    url = urljoin(server.resource.url, "_openag", "v0.1", "register_farm")
    status, _, content = server.resource.session.request(
        "POST", url, headers=server.resource.headers.copy(), body={
            "name": username, "farm_name": farm_name
        }, credentials=(username, password)
    )
    if status != 200:
        raise click.ClickException(
            "Failed to register farm with cloud server ({}): {}".format(
                status, content
            )
        )

@click.command()
def list_farms():
    """
    List all farms you can manage. If you have selected a farm already, the
    name of that farm will be prefixed with an asterisk in the returned list.
    """
    utils.check_for_cloud_server()
    utils.check_for_cloud_user()
    server = Server(config["cloud_server"]["url"])
    server.log_in(
        config["cloud_server"]["username"], config["cloud_server"]["password"]
    )
    farms_list = server.get_user_info().get("farms", [])
    if not len(farms_list):
        raise click.ClickException(
            "No farms exist. Run `openag cloud create_farm` to create one"
        )
    active_farm_name = config["cloud_server"]["farm_name"]
    for farm_name in farms_list:
        if farm_name == active_farm_name:
            click.echo("*"+farm_name)
        else:
            click.echo(farm_name)

@click.command()
@click.argument("farm_name")
def init_farm(farm_name):
    """
    Select a farm to use. This command sets up the replication between your
    local database and the selected cloud server if you have already
    initialized your local database with the `openag db init` command.
    """
    utils.check_for_cloud_server()
    utils.check_for_cloud_user()
    old_farm_name = config["cloud_server"]["farm_name"]
    if old_farm_name and old_farm_name != farm_name:
        raise click.ClickException(
            "Farm \"{}\" already initialized. Run `openag cloud deinit_farm` "
            "to deinitialize it".format(old_farm_name)
        )
    if config["local_server"]["url"]:
        utils.replicate_per_farm_dbs(farm_name=farm_name)
    config["cloud_server"]["farm_name"] = farm_name

@click.command()
def deinit_farm():
    """
    Detach from the current farm. Cancels the replication between your local
    server and the cloud instance if it is set up.
    """
    utils.check_for_cloud_server()
    utils.check_for_cloud_user()
    utils.check_for_cloud_farm()
    farm_name = config["cloud_server"]["farm_name"]
    if farm_name and config["local_server"]["url"]:
        utils.cancel_per_farm_db_replication()
    config["cloud_server"]["farm_name"] = None

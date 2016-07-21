import json
import click
import requests
from urllib import quote
from urlparse import urljoin

from .utils import CouchSession
from .config import Config
from .db_names import per_farm_dbs

@click.group()
def farms():
    """ Set up data mirroring with the cloud server """
    pass

@farms.command()
def show():
    """ Show what the server knows about this farm """
    config = Config()
    active_server = config["active_server"]
    if active_server:
        click.echo("Using cloud server \"{}\"".format(active_server))
    else:
        click.echo("No cloud server selected")
    farm_name = config["servers"][active_server]["farm_name"]
    if farm_name:
        click.echo("Using farm \"{}\"".format(farm_name))
    else:
        click.echo("No farm selected")

@farms.command()
def list():
    """ List the farms you can manage """
    config = Config()
    s = CouchSession.from_config(config)
    active_server = config["active_server"]
    username = config["servers"][active_server]["username"]
    user_id = "org.couchdb.user:" + username
    user_info = s.get("_users/"+user_id).json()
    farms_list = user_info.get("farms", [])
    if not len(farms_list):
        click.echo("No farms exist")
    active_farm_name = config["servers"][active_server]["farm_name"]
    for farm_name in farms_list:
        if farm_name == active_farm_name:
            click.echo("*"+farm_name)
        else:
            click.echo(farm_name)

@farms.command()
@click.argument("farm_name")
def create(farm_name):
    """ Create a farm on the cloud server """
    config = Config()
    s = CouchSession.from_config(config)
    username = config["servers"][active_server]["username"]
    res = s.post(
        "/_openag/v0.1/register_farm", data={
            "name": username,
            "farm_name": farm_name
        }
    )
    if not res.status_code == 201:
        raise click.ClickException(
            "Failed to register farm with cloud server ({}): {}".format(
                res.status_code, res.content
            )
        )

@farms.command()
@click.argument("farm_name")
def select(farm_name):
    """ Select a farm to mirror data into """
    config = Config()
    active_server = config["active_server"]
    username = config["servers"][active_server]["username"]
    for db_name in per_farm_dbs:
        remote_db_name = "{}/{}/{}".format(username, farm_name, db_name)
        res = requests.post(
            "http://localhost:5984/_replicate", data=json.dumps({
                "source": db_name,
                "target": urljoin(active_server, quote(remote_db_name, "")),
                "continuous": True,
                "create_target": True
            }), headers={
                "Content-Type": "application/json"
            }
        )
        print res.request.body
        if not res.status_code == 200:
            raise click.ClickException(
                "Failed to set up replication from cloud server ({}): {}".format(
                    res.status_code, res.content
                )
            )
    config["servers"][config["active_server"]]["farm_name"] = farm_name

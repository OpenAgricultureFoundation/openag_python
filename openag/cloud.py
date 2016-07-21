import json
import click
import requests
from urllib import quote
from urlparse import urlparse, urljoin

from .utils import CouchSession
from .config import Config
from .db_names import global_dbs

@click.group()
def cloud():
    """ Manage your cloud user account """
    pass

@cloud.command()
def show():
    """ Show info about the cloud server """
    config = Config()
    active_server = config["active_server"]
    if active_server:
        click.echo("Using cloud server \"{}\"".format(active_server))
    else:
        click.echo("No cloud server selected")
    username = config["servers"][active_server]["username"]
    if username:
        click.echo("Logged in as user \"{}\"".format(username))
    else:
        click.echo("Not logged in")

@cloud.command()
@click.argument("server_url")
def set_url(server_url):
    """ Set the URL of the cloud server to use """
    url = urlparse(server_url)
    if not url.scheme or not url.netloc or not url.port:
        raise click.BadParameter("Invalid url supplied")
    for db_name in global_dbs:
        res = requests.post(
            "http://localhost:5984/_replicate", data=json.dumps({
                "source": urljoin(server_url, db_name),
                "target": db_name,
                "continuous": True,
                "create_target": True
            }), headers={
                "Content-Type": "application/json"
            }
        )
        if not res.status_code == 200:
            raise click.ClickException(
                "Failed to set up replication from cloud server ({}): {}".format(
                    res.status_code, res.content
                )
            )
    Config()["active_server"] = server_url

@cloud.command()
@click.option("--username", prompt=True, help="Username for the account")
@click.option(
    "--password", prompt=True, hide_input=True, confirmation_prompt=True,
    help="Password for the account"
)
def register(username, password):
    """ Create an account on the cloud server """
    s = CouchSession(Config()["active_server"])
    user_id = quote("org.couchdb.user:") + username
    res = s.put(
        "_users/"+user_id, data=json.dumps({
            "_id": user_id,
            "name": username,
            "roles": [],
            "type": "user",
            "password": password
        })
    )
    if res.status_code != 201:
        raise RuntimeError(
            "Failed to create user: " + res.content
        )

@cloud.command()
@click.option("--username", prompt=True, help="Username for the account")
@click.option(
    "--password", prompt=True, hide_input=True, help="Password for the account"
)
def login(username, password):
    """ Log in to the cloud server """
    config = Config()
    active_server = config["active_server"]
    s = CouchSession(active_server)
    s.log_in(username, password)
    config["servers"][active_server]["username"] = username
    config["servers"][active_server]["cookie"] = s.headers["Cookie"]

@cloud.command()
def logout():
    """ Log out of the cloud server """
    config = Config()
    active_server = config["active_server"]
    s = CouchSession(active_server)
    s.headers["Cookie"] = config["servers"][active_server]["cookie"]
    s.log_out()
    del config["servers"][active_server]

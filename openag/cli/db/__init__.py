import os
import json
import time
import click
from couchdb.http import urljoin

from openag import _design
from openag.couch import Server, ResourceNotFound
from openag.db_names import all_dbs
from .. import utils
from ..config import config
from .db_config import generate_config

@click.group()
def db():
    """ Manage the local CouchDB instance """

@db.command()
@click.option("--db_url", default="http://localhost:5984")
@click.option("--api_url")
def init(db_url, api_url):
    """
    Initialize the database server. Sets some configuration parameters on the
    server, creates the necessary databases for this project, pushes design
    documents into those databases, and sets up replication with the cloud
    server if one has already been selected.
    """
    old_db_url = config["local_server"]["url"]
    if old_db_url and old_db_url != db_url:
        raise click.ClickException(
            "Local database \"{}\" already initialized. Switching local "
            "databases is not currently supported".format(old_db_url)
        )

    db_config = generate_config(api_url)
    server = Server(db_url)

    # Configure the CouchDB instance itself
    config_items = []
    for section, values in db_config.items():
        for param, value in values.items():
            config_items.append((section, param, value))
    with click.progressbar(
        config_items, label="Applying CouchDB configuration",
        length=len(config_items)
    ) as _config_items:
        for section, param, value in _config_items:
            url = urljoin(server.resource.url, "_config", section, param)
            try:
                current_val = server.resource.session.request(
                    "GET", url
                )[2].read().strip()
            except ResourceNotFound:
                current_val = None
            desired_val = '"{}"'.format(value.replace('"', '\\"'))
            if current_val != desired_val:
                status = server.resource.session.request(
                    "PUT", url, body=desired_val
                )[0]
                # Unless there is some delay  between requests, CouchDB gets
                # sad for some reason
                if status != 200:
                    click.ClickException(
                        'Failed to set configuration parameter "{}": {}'.format(
                            param, res.content
                        )
                    )
                time.sleep(1)

    # Create all dbs on the server
    with click.progressbar(
        all_dbs, label="Creating databases", length=len(all_dbs)
    ) as _dbs:
        for db_name in _dbs:
            server.get_or_create(db_name)

    # Push design documents
    click.echo("Pushing design documents")
    design_path = os.path.dirname(_design.__file__)
    server.push_design_documents(design_path)

    # Set up replication
    if config["cloud_server"]["url"]:
        click.echo("Setting up replication with cloud server")
        utils.replicate_global_dbs(local_url=db_url)
        if config["cloud_server"]["farm_name"]:
            utils.replicate_per_farm_dbs(local_url=db_url)

    config["local_server"]["url"] = db_url

@db.command()
def deinit():
    """
    Detach from the local server.
    """
    utils.check_for_local_server()
    del config["local_server"]

@db.command()
def show():
    """
    Shows the URL of the current local server. Throws an error if no local
    server is selected
    """
    utils.check_for_local_server()
    click.echo("Using local server at \"{}\"".format(
        config["local_server"]["url"]
    ))

@db.command()
def clear():
    """
    Clear all data on the local server. Useful for debugging purposed.
    """
    utils.check_for_local_server()
    click.confirm(
        "Are you sure you want to do this? It will delete all of your data",
        abort=True
    )
    server = Server(config["local_server"]["url"])
    for db_name in all_dbs:
        del server[db_name]

@db.command()
@click.argument("fixture_file", type=click.File())
def load_fixture(fixture_file):
    """
    Populate the database from a JSON file. Reads the JSON file FIXTURE_FILE
    and uses it to populate the database. Fuxture files should consist of a
    dictionary mapping database names to arrays of objects to store in those
    databases.
    """
    utils.check_for_local_server()
    local_url = config["local_server"]["url"]
    server = Server(local_url)
    fixture = json.load(fixture_file)
    for db_name, _items in fixture.items():
        db = server[db_name]
        with click.progressbar(
            _items, label=db_name, length=len(_items)
        ) as items:
            for item in items:
                item_id = item["_id"]
                if item_id in db:
                    old_item = db[item_id]
                    item["_rev"] = old_item["_rev"]
                    if item == old_item:
                        continue
                db[item_id] = item

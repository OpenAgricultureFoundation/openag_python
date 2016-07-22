import os
import time
import click

from openag import _design
from openag.couchdb import Server
from openag.db_names import all_dbs
from ..utils import *
from ..config import Config
from .db_config import generate_config

@click.group()
def db():
    """ Manage the local CouchDB instance """
    pass

@db.command()
@click.option("--db_url", default="http://localhost:5984")
@click.option("--api_url", default="http://localhost:5000")
def init(db_url, api_url):
    """ Initialize the database """
    config = Config()
    db_config = generate_config(api_url)
    server = Server(db_url)

    old_db_url = config["local_server"]["url"]
    if old_db_url:
        raise click.ClickException(
            "Local database \"{}\" already initialized. Switching local "
            "databases is not currently supported".format(old_db_url)
        )

    # Configure the CouchDB instance itself
    for section, values in db_config.items():
        for param, value in values.items():
            url = "_config/{}/{}".format(section, param)
            current_val = server.get(url).content.strip()
            desired_val = '"{}"'.format(value.replace('"', '\\"'))
            if current_val != desired_val:
                res = server.put(url, data=desired_val)
                # Unless there is some delay  between requests, CouchDB gets
                # sad for some reason
                time.sleep(1)
                if not res.status_code == 200:
                    click.ClickException(
                        'Failed to set configuration parameter "{}": {}'.format(
                            param, res.content
                        )
                    )

    # Create all dbs on the server
    for db_name in all_dbs:
        server.get_or_create_db(db_name)

    # Push design documents
    design_path = os.path.dirname(_design.__file__)
    server.push_design_documents(design_path)

    # Set up replication
    if config["cloud_server"]["url"]:
        replicate_global_dbs(config, local_url=db_url)
        if config["cloud_server"]["farm_name"]:
            replicate_per_farm_dbs(config, local_url=db_url)

    config["local_server"]["url"] = db_url

@db.command()
@click.argument("fixture_file", type=click.File())
def load_fixture(fixture_file):
    """ Populate the database from a JSON file """
    fixtue = json.load(fixture_file)
    for db_name, items in fixture.items:
        pass

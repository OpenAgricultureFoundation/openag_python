from click import ClickException
from urllib import quote
from urlparse import urljoin, urlparse, ParseResult

from ..couchdb import Server
from ..db_names import global_dbs, per_farm_dbs

def check_for_cloud_server(config):
    if not config["cloud_server"]["url"]:
        raise ClickException(
            "No cloud server selected. Run `openag cloud init` to select one"
        )

def check_for_cloud_user(config):
    if not config["cloud_server"]["username"]:
        raise ClickException(
            "Not logged into cloud server. Run `openag cloud user register` "
            "to create a user account or `openag cloud user login` to log in "
            "with an existing account"
        )

def check_for_cloud_farm(config):
    if not config["cloud_server"]["farm_name"]:
        raise ClickException(
            "No farm selected. Run `openag cloud farm create` to create a "
            "farm, `openag cloud farm list` to see what farms you have access "
            "to, and `openag cloud farm select` to select a farm"
        )

def replicate_global_dbs(config, cloud_url=None, local_url=None):
    local_url = local_url or config["local_server"]["url"]
    cloud_url = cloud_url or config["cloud_server"]["url"]
    server = Server(local_url)
    for db_name in global_dbs:
        server.replicate(
            urljoin(cloud_url, db_name), db_name, continuous=True
        )

def replicate_per_farm_dbs(config, cloud_url=None, local_url=None, farm_name=None):
    cloud_url = cloud_url or config["cloud_server"]["url"]
    local_url = local_url or config["local_server"]["url"]
    farm_name = farm_name or config["cloud_server"]["farm_name"]
    username = config["cloud_server"]["username"]
    password = config["cloud_server"]["password"]

    # Add credentials to the cloud url
    parsed_cloud_url = urlparse(cloud_url)
    if not parsed_cloud_url.username:
        new_netloc = "{}:{}@{}".format(
            username, password, parsed_cloud_url.netloc
        )
    cloud_url = ParseResult(
        parsed_cloud_url.scheme, new_netloc, parsed_cloud_url.path,
        parsed_cloud_url.params, parsed_cloud_url.query,
        parsed_cloud_url.fragment
    ).geturl()

    server = Server(local_url)
    for db_name in per_farm_dbs:
        remote_db_name = "{}/{}/{}".format(username, farm_name, db_name)
        server.replicate(
            db_name, urljoin(cloud_url, quote(remote_db_name, "")),
            continuous=True
        )

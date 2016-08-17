from click import ClickException
from urllib import quote
from urlparse import urlparse, ParseResult
from couchdb.http import urljoin

from .config import config
from ..couch import Server
from ..db_names import global_dbs, per_farm_dbs

def check_for_local_server():
    """
    Raise an error if no local server is defined in the global configuration
    """
    if not config["local_server"]["url"]:
        raise ClickException(
            "No local server selected. Run `openag db init` to select one"
        )

def check_for_cloud_server():
    """
    Raise an error if no cloud server is defined in the global configuration
    """
    if not config["cloud_server"]["url"]:
        raise ClickException(
            "No cloud server selected. Run `openag cloud init` to select one"
        )

def check_for_cloud_user():
    """
    Raise an error if the user is not logged into their cloud server. Assumes
    there is a cloud server (i.e. check_for_cloud_server would succeed)
    """
    if not config["cloud_server"]["username"]:
        raise ClickException(
            "Not logged into cloud server. Run `openag cloud register` to "
            "create a user account or `openag cloud login` to log in with an "
            "existing account"
        )

def check_for_cloud_farm():
    """
    Raise an error if no farm is selected on the cloud server. Assumes there is
    a cloud server (i.e. check_for_cloud_server would succeed)
    """
    if not config["cloud_server"]["farm_name"]:
        raise ClickException(
            "No farm selected. Run `openag cloud farm create` to create a "
            "farm, `openag cloud farm list` to see what farms you have access "
            "to, and `openag cloud farm select` to select a farm"
        )

def replicate_global_dbs(cloud_url=None, local_url=None):
    """
    Set up replication of the global databases from the cloud server to the
    local server.

    :param str cloud_url: Used to override the cloud url from the global
    configuration in case the calling function is in the process of
    initializing the cloud server
    :param str local_url: Used to override the local url from the global
    configuration in case the calling function is in the process of
    initializing the local server
    """
    local_url = local_url or config["local_server"]["url"]
    cloud_url = cloud_url or config["cloud_server"]["url"]
    server = Server(local_url)
    for db_name in global_dbs:
        server.replicate(
            db_name, urljoin(cloud_url, db_name), db_name, continuous=True,
        )

def cancel_global_db_replication():
    """
    Cancel replication of the global databases from the cloud server to the
    local server.
    """
    local_url = config["local_server"]["url"]
    server = Server(local_url)
    for db_name in global_dbs:
        server.cancel_replication(db_name)

def replicate_per_farm_dbs(cloud_url=None, local_url=None, farm_name=None):
    """
    Sete up replication of the per-farm databases from the local server to the
    cloud server.

    :param str cloud_url: Used to override the cloud url from the global
    configuration in case the calling function is in the process of
    initializing the cloud server
    :param str local_url: Used to override the local url from the global
    configuration in case the calling function is in the process of
    initializing the local server
    :param str farm_name: Used to override the farm name from the global
    configuratino in case the calling function is in the process of
    initializing the farm
    """
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
            db_name, db_name, urljoin(cloud_url, remote_db_name),
            continuous=True
        )

def cancel_per_farm_db_replication():
    """
    Cancel replication of the per-farm databases from the local server to the
    cloud server.
    """
    cloud_url = config["cloud_server"]["url"]
    local_url = config["local_server"]["url"]
    server = Server(local_url)
    for db_name in per_farm_dbs:
        server.cancel_replication(db_name)

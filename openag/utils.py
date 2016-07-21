import click
import requests
from urlparse import urljoin

class CouchSession(requests.Session):
    """
    `requests.Session` subclass for interfacing with a CouchDB instance. It
    maintains state about the connection and provides convenience functions for
    user authentication.
    """
    def __init__(self, db_url):
        self.db_url = db_url
        super(CouchSession, self).__init__()

    def request(self, method, url, **kwargs):
        url = urljoin(self.db_url, url)
        return super(CouchSession, self).request(method, url, **kwargs)

    def log_in(self, username, password):
        """
        Logs in to the CouchDB instance with the credentials `username` and
        `password`
        """
        res = self.post(
            "_session", data={"name": username, "password": password}
        )
        if not res.status_code == 200:
            raise RuntimeError("Failed to log in to CouchDB: " + res.content)
        self.headers.update({
            "Cookie": res.headers["Set-Cookie"].split(';')[0]
        })

    def log_out(self):
        res = self.delete("_session")
        if res.status_code != 200:
            raise RuntimeError("Failed to log out of CouchDB: " + res.content)

    @classmethod
    def from_config(cls, config):
        active_server = config["active_server"]
        cookie = config["servers"][active_server]["cookie"]
        s = CouchSession(active_server)
        s.headers["Cookie"] = cookie
        if not s.get("_session").json()["userCtx"]["name"]:
            username = config["servers"][active_server]["username"]
            password = click.prompt("Password", hide_input=True)
            s.log_in(username, password)
            config["servers"][active_server]["cookie"] = s.headers["Cookie"]
        return s

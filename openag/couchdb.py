"""
This module consists of code for interacting with a CouchDB server instance.
"""
import os
import json
import requests
from urllib import quote
from urlparse import urljoin

class Database(object):
    """
    Instances of this class represent individual databases on a CouchDB
    instance.

    :param server: The Server instance to which this database belongs
    :param db_name: The name of this database
    """
    def __init__(self, server, db_name):
        self.server = server
        self.db_name = db_name
        self.docs = None

    def __contains__(self, doc_id):
        if not self.docs:
            self._fetch()
        return doc_id in self.docs

    def __iter__(self):
        if not self.docs:
            self._fetch()
        return iter(self.docs)

    def __getitem__(self, key):
        if not self.docs:
            self._fetch()
        return self.docs[key]

    def __setitem__(self, key, val):
        # Make sure the id is set on the val
        val["_id"] = key
        self.store(val)

    def __delitem__(self, key):
        self.delete(key)

    def _fetch(self):
        self.docs = {}
        res = self.server.get(
            "/".join([self.db_name, "_all_docs"]), params={
                "include_docs": True
            }
        ).json()
        for row in res["rows"]:
            self.docs[row["id"]] = row["doc"]

    def store(self, doc):
        doc_id = doc.get("_id", None)

        if doc_id:
            if doc_id in self:
                old_doc = self[doc_id]
                # Copy internal keys from the old document
                for k,v in old_doc.items():
                    if k.startswith("_"):
                        doc[k] = v
                # If the document hasn't changed, do nothing
                if doc == old_doc:
                    return
            res = self.server.put(
                "/".join([self.db_name, doc_id]), data=json.dumps(doc)
            )
            if res.status_code == 201:
                doc.update(res.json())
            else:
                raise RuntimeError(
                    "Failed to save document ({}): {}".format(
                        res.status_code, res.content
                    )
                )
        else:
            res = self.server.post(
                self.db_name, data=json.dumps(doc)
            )
            if not res.status_code == 201:
                raise RuntimeError(
                    "Failed to save document ({}): {}".format(
                        res.status_code, res.content
                    )
                )
            doc.update(res.json())
            doc_id = doc["_id"]

        self.docs[doc_id] = doc

    def delete(self, doc_id):
        res = self.server.delete("/".join([self.db_name, doc_id]))
        if res.status_code != 200:
            raise RuntimeError(
                "Failed to delete document ({}): {}".format(
                    res.status_code, res.content
                )
            )
        del self.docs[doc_id]

class Server(requests.Session):
    """
    Class that represents a single CouchDB server instance and provides
    functions for interfacing with that server
    """
    def __init__(self, url="http://localhost:5984"):
        self.url = url
        super(Server, self).__init__()
        self.db_names = set(self.get("_all_dbs").json())
        self.dbs = {}

    def __len__(self):
        return len(self.db_names)

    def __getitem__(self, db_name):
        if not db_name in self:
            raise ValueError("Database \"{}\" does not exist".format(db_name))
        if not db_name in self.dbs:
            self.dbs[db_name] = Database(self, db_name)
        return self.dbs[db_name]

    def __contains__(self, db_name):
        return db_name in self.db_names

    def request(self, method, url, **kwargs):
        url = urljoin(self.url, url)
        return super(Server, self).request(method, url, **kwargs)

    def replicate(self, source, target, continuous=False):
        if source in self["_replicator"]:
            return
        data = {
            "_id": source,
            "source": source,
            "target": target,
            "continuous": continuous
        }
        self["_replicator"][source] = data

    def cancel_replication(self, source):
        if source not in self["_replicator"]:
            return
        del self["_replicator"][source]

    def create_user(self, username, password):
        """
        Creates a user in the CouchDB instance with the username `username` and
        password `password`
        """
        user_id = quote("org.couchdb.user:")+username
        res = self.put(
            "_users/"+user_id, data=json.dumps({
                "_id": user_id,
                "name": username,
                "roles": [],
                "type": "user",
                "password": password,
                "farms": []
            })
        )
        if res.status_code == 409:
            raise RuntimeError(
                'The username "{}" is already taken'.format(username)
            )
        elif res.status_code != 201:
            raise RuntimeError(
                "Failed to create user ({}): {}".format(
                    res.status_code, res.content
                )
            )

    def get_user_info(self):
        """
        Returns the document representing the currently logged in user on the
        server
        """
        user_id = quote("org.couchdb.user:")+self.auth[0]
        return self.get("_users/"+user_id).json()

    def get_or_create_db(self, db_name):
        if not db_name in self:
            res = self.put(db_name)
            if not res.status_code == 201:
                raise RuntimeError(
                    'Failed to create database "{}"'.format(db_name)
                )
            self.db_names.add(db_name)
        return self[db_name]

    def push_design_documents(self, design_path):
        for db_name in os.listdir(design_path):
            if db_name.startswith("__") or db_name.startswith("."):
                continue
            db_path = os.path.join(design_path, db_name)
            doc = self._folder_to_dict(db_path)
            doc["_id"] = "_design/openag"
            self[db_name].store(doc)

    def log_in(self, username, password):
        """
        Logs in to the CouchDB instance with the credentials `username` and
        `password`
        """
        self.auth = (username, password)
        res = self.get("_session")
        if res.status_code != 200:
            raise RuntimeError(
                "Failed to authentication to CouchDB instance ({}): {}".format(
                    res.status_code, res.content
                )
            )
        return res.json()

    def log_out(self):
        """ Logs out of the CouchDB instance """
        pass

    def _folder_to_dict(self, path):
        """
        Recursively reads the files from the directory given by `path` and writes
        their contents to a nested dictionary, which is then returned.
        """
        res = {}
        for key in os.listdir(path):
            if key.startswith('.'):
                continue
            key_path = os.path.join(path, key)
            if os.path.isfile(key_path):
                val = open(key_path).read()
                key = key.split('.')[0]
                res[key] = val
            else:
                res[key] = self._folder_to_dict(key_path)
        return res


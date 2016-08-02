import json
import requests_mock

from openag.couchdb import Server

@requests_mock.Mocker()
def test_replicate(m):
    m.get("http://test.test:5984/_all_dbs", text=json.dumps(["_replicator"]))
    server = Server("http://test.test:5984")
    m.get(
        "http://test.test:5984/_replicator/_all_docs?include_docs=True",
        text=json.dumps({"rows": []})
    )
    m.put(
        "http://test.test:5984/_replicator/test_src", text="{}",
        status_code=201
    )
    server.replicate("test_src", "test_dest", continuous=True)
    m.delete("http://test.test:5984/_replicator/test_src", text="{}")
    server.cancel_replication("test_src")

@requests_mock.Mocker()
def test_failed_replication(m):
    m.get("http://test.test:5984/_all_dbs", text=json.dumps(["_replicator"]))
    server = Server("http://test.test:5984")
    m.get(
        "http://test.test:5984/_replicator/_all_docs?include_docs=True",
        text=json.dumps({"rows": []})
    )
    m.put(
        "http://test.test:5984/_replicator/test_src", status_code=400
    )
    try:
        server.replicate("test_src", "test_dest", continuous=True)
        assert False, "No error thrown on failed replication attempt"
    except RuntimeError:
        pass

@requests_mock.Mocker()
def test_failed_replication_cancel(m):
    m.get("http://test.test:5984/_all_dbs", text=json.dumps(["_replicator"]))
    server = Server("http://test.test:5984")
    m.get(
        "http://test.test:5984/_replicator/_all_docs?include_docs=True",
        text=json.dumps({"rows": [{"id": "test_src", "doc": {}}]})
    )
    m.delete(
        "http://test.test:5984/_replicator/test_src", status_code=400
    )
    try:
        server.cancel_replication("test_src")
        assert False, "No error thrown on failed replication cancellation"
    except RuntimeError:
        pass


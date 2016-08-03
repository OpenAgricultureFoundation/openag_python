import json
import requests_mock

from openag.couchdb import Server

@requests_mock.Mocker()
def test_iterate(m):
    m.get("http://test.test:5984/_all_dbs", text=json.dumps(["test"]))
    server = Server("http://test.test:5984")
    doc = {"_id": "test", "_rev": "a", "key": "val"}
    m.get(
        "http://test.test:5984/test/_all_docs?include_docs=True",
        text=json.dumps({
            "rows": [
                {"id": "test", "doc": doc}
            ]
        })
    )

    # Test __iter__
    assert list(server["test"]) == ["test"]

    # Clear the cache
    server["test"].docs = None

    # Test __getitem__
    assert server["test"]["test"] == doc

    # Test __setitem__ no change
    server["test"]["test"] = doc
    assert server["test"]["test"] == doc

    # Test __setitem__ update
    updated_doc = {"_id": "test", "key": "val2"}
    m.put("http://test.test:5984/test/test", text=json.dumps(updated_doc))
    server["test"]["test"] = updated_doc
    assert server["test"]["test"] == updated_doc

    # Test new docment
    new_doc = {"key": "val3"}
    m.post("http://test.test:5984/test", text=json.dumps({
        "_id": "test2", "key": "val3"
    }), status_code=201)
    server["test"].store(new_doc)
    assert list(server["test"]) == ["test", "test2"]

@requests_mock.Mocker()
def test_get_or_create_db(m):
    m.get("http://test.test:5984/_all_dbs", text=json.dumps([]))
    server = Server("http://test.test:5984")
    m.put("http://test.test:5984/test", status_code=201)
    assert "test" not in server
    server.get_or_create_db("test")
    assert "test" in server

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
    m.put("http://test.test:5984/_replicator/test_src", status_code=500)
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


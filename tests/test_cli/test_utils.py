import mock

from tests import mock_config

from openag.couch import Server
from openag.db_names import global_dbs
from openag.cli.utils import *

@mock_config({
    "cloud_server": {
        "url": "http://test.test:5984",
    },
    "local_server": {
        "url": "http://localhost:5984"
    }
})
@mock.patch.object(Server, "replicate")
def test_replicate_global_dbs(config, replicate):
    replicate_global_dbs()
    assert replicate.call_count == len(global_dbs)
    for db_name in global_dbs:
        remote_db_name = "http://test.test:5984/" + db_name
        replicate.assert_any_call(
            remote_db_name, db_name, continuous=True
        )

@mock_config({
    "cloud_server": {
        "url": "http://test.test:5984"
    },
    "local_server": {
        "url": "http://localhost:5984"
    }
})
@mock.patch.object(Server, "cancel_replication")
def test_cancel_global_db_replication(config, cancel_replication):
    cancel_global_db_replication()
    assert cancel_replication.call_count == len(global_dbs)
    for db_name in global_dbs:
        remote_db_name = "http://test.test:5984/" + db_name
        cancel_replication.assert_any_call(remote_db_name)

@mock_config({
    "cloud_server": {
        "url": "http://test.test:5984",
        "username": "test",
        "password": "test",
        "farm_name": "test"
    },
    "local_server": {
        "url": "http://localhost:5984"
    }
})
@mock.patch.object(Server, "replicate")
def test_replicate_per_farm_dbs(config, replicate):
    replicate_per_farm_dbs()
    assert replicate.call_count == len(per_farm_dbs)
    for db_name in per_farm_dbs:
        remote_db_name = "http://test:test@test.test:5984/"+quote("test/test/"+db_name,"")
        replicate.assert_any_call(db_name, remote_db_name, continuous=True)

@mock_config({
    "cloud_server": {
        "url": "http://test.test:5984",
        "username": "test",
        "password": "test",
        "farm_name": "test"
    },
    "local_server": {
        "url": "http://localhost:5984"
    }
})
@mock.patch.object(Server, "cancel_replication")
def test_cancel_per_farm_db_replication(config, cancel_replication):
    cancel_per_farm_db_replication()
    assert cancel_replication.call_count == len(per_farm_dbs)
    for db_name in per_farm_dbs:
        cancel_replication.assert_any_call(db_name)


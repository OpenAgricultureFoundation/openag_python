"""
Tests the ability to connect to and disconnect from a cloud server
"""
import json
import mock
from click.testing import CliRunner
import requests_mock

from tests import mock_config

from openag.db_names import global_dbs
from openag.couchdb import Server
from openag.cli.cloud import init, show, deinit

@mock_config({
    "cloud_server": {
        "url": None,
        "username": None,
        "password": None
    },
    "local_server": {
        "url": None
    }
})
@mock.patch.object(Server, "replicate")
def test_cloud_without_local_server(config, replicate):
    runner = CliRunner()

    # Show -- Should raise an error because there is no cloud server
    res = runner.invoke(show)
    assert res.exit_code, res.output

    # Deinit -- Should raise an error because there is no cloud server
    res = runner.invoke(deinit)
    assert res.exit_code, res.output

    # Init -- Should throw an error because the url is invalid
    res = runner.invoke(init, ["this is not a url"])
    assert res.exit_code, res.output

    # Init -- Should work but not replicate any DBs
    res = runner.invoke(init, ["http://test.test:5984"])
    assert res.exit_code == 0, res.exception or res.output
    assert replicate.call_count == 0

    # Show -- Should work
    res = runner.invoke(show)
    assert res.exit_code == 0, res.exception or res.output

    # Deinit -- Should work and not cancel any replications
    res = runner.invoke(deinit)
    assert res.exit_code == 0, res.exception or res.output
    assert replicate.call_count == 0

    # Show -- Should raise an error becuase there is no cloud server
    res = runner.invoke(show)
    assert res.exit_code, res.output

@mock.patch.object(Server, "replicate")
@mock.patch.object(Server, "cancel_replication")
@requests_mock.Mocker()
def test_cloud_with_local_server(cancel_replication, replicate, m):
    mock_config({
        "cloud_server": {
            "url": None,
            "username": None,
            "password": None,
            "farm_name": None
        },
        "local_server": {
            "url": "http://localhost:5984"
        }
    })
    m.get("http://localhost:5984/_all_dbs", text="[]")
    runner = CliRunner()

    # Show -- Should raise an error because there is no cloud server
    res = runner.invoke(show)
    assert res.exit_code, res.output

    # Deinit -- Should raise an error because there is no cloud server
    res = runner.invoke(deinit)
    assert res.exit_code, res.output

    # Init -- Should work but not replicate any DBs
    res = runner.invoke(init, ["http://test.test:5984"])
    assert res.exit_code == 0, res.exception or res.output
    assert replicate.call_count == len(global_dbs)
    replicate.reset_mock()

    # Init -- Should work because it should be idempotent
    res = runner.invoke(init, ["http://test.test:5984"])
    assert res.exit_code == 0, res.exception or res.output
    assert replicate.call_count == len(global_dbs)
    replicate.reset_mock()

    # Init -- Should throw an error because a different server is already
    # selected
    res = runner.invoke(init, ["http://test2.test2:5984"])
    assert res.exit_code, res.output
    assert replicate.call_count == 0

    # Show -- Should work
    res = runner.invoke(show)
    assert res.exit_code == 0, res.exception or res.output

    # Deinit -- Should work and not cancel any replications
    res = runner.invoke(deinit)
    assert res.exit_code == 0, res.exception or res.output
    assert cancel_replication.call_count == len(global_dbs)

    # Show -- Should raise an error becuase there is no cloud server
    res = runner.invoke(show)
    assert res.exit_code, res.output

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
@requests_mock.Mocker()
def test_full_cloud_deinit(config, m):
    runner = CliRunner()
    m.get("http://localhost:5984/_all_dbs", text=json.dumps(["_replicator"]))
    m.get(
        "http://localhost:5984/_replicator/_all_docs?include_docs=True",
        text=json.dumps({"rows": []})
    )

    res = runner.invoke(deinit)
    assert res.exit_code == 0, res.exception or res.output
    assert config["cloud_server"]["url"] is None
    assert config["cloud_server"]["username"] is None
    assert config["cloud_server"]["password"] is None
    assert config["cloud_server"]["farm_name"] is None

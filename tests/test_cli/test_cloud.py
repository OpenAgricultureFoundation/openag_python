"""
Tests the ability to connect to and disconnect from a cloud server
"""
import json
import mock
import httpretty
from click.testing import CliRunner

from tests import mock_config

from openag.db_names import global_dbs
from openag.couch import Server
from openag.cli.cloud import init, show, deinit

@mock_config({
    "cloud_server": {
        "url": None,
        "username": None,
        "password": None,
        "farm_name": None
    },
    "local_server": {
        "url": None
    }
})
@mock.patch("openag.cli.utils.replicate_global_dbs")
@mock.patch("openag.cli.utils.cancel_global_db_replication")
def test_cloud_without_local_server(
    config, cancel_global_db_replication, replicate_global_dbs
):
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
    assert replicate_global_dbs.call_count == 0

    # Show -- Should work
    res = runner.invoke(show)
    assert res.exit_code == 0, res.exception or res.output

    # Deinit -- Should work but not cancel replication of global DBs
    res = runner.invoke(deinit)
    assert res.exit_code == 0, res.exception or res.output
    assert cancel_global_db_replication.call_count == 0

    # Show -- Should raise an error becuase there is no cloud server
    res = runner.invoke(show)
    assert res.exit_code, res.output

@mock_config({
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
@mock.patch("openag.cli.utils.replicate_global_dbs")
@mock.patch("openag.cli.utils.cancel_global_db_replication")
def test_cloud_with_local_server(
    config, cancel_global_db_replication, replicate_global_dbs
):
    runner = CliRunner()

    # Show -- Should raise an error because there is no cloud server
    res = runner.invoke(show)
    assert res.exit_code, res.output

    # Deinit -- Should raise an error because there is no cloud server
    res = runner.invoke(deinit)
    assert res.exit_code, res.output

    # Init -- Should work and replicate all global dbs
    res = runner.invoke(init, ["http://test.test:5984"])
    assert res.exit_code == 0, res.exception or res.output
    assert replicate_global_dbs.call_count == 1
    replicate_global_dbs.reset_mock()

    # Init -- Should work because it should be idempotent
    res = runner.invoke(init, ["http://test.test:5984"])
    assert res.exit_code == 0, res.exception or res.output
    assert replicate_global_dbs.call_count == 1
    replicate_global_dbs.reset_mock()

    # Init -- Should throw an error because a different server is already
    # selected
    res = runner.invoke(init, ["http://test2.test2:5984"])
    assert res.exit_code, res.output

    # Show -- Should work
    res = runner.invoke(show)
    assert res.exit_code == 0, res.exception or res.output

    # Deinit -- Should work and cancel replication of global DBs
    res = runner.invoke(deinit)
    assert res.exit_code == 0, res.exception or res.output
    assert cancel_global_db_replication.call_count == 1

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
@mock.patch("openag.cli.utils.cancel_global_db_replication")
@mock.patch("openag.cli.utils.cancel_per_farm_db_replication")
def test_full_cloud_deinit(
    config, cancel_global_db_replication, cancel_per_farm_db_replication
):
    runner = CliRunner()

    res = runner.invoke(deinit)
    assert res.exit_code == 0, res.exception or res.output
    assert cancel_global_db_replication.call_count == 1
    assert cancel_per_farm_db_replication.call_count == 1
    assert config["cloud_server"]["url"] is None
    assert config["cloud_server"]["username"] is None
    assert config["cloud_server"]["password"] is None
    assert config["cloud_server"]["farm_name"] is None

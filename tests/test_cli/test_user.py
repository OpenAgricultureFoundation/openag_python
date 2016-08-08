"""
Tests the ability to log in to a cloud server
"""
import json
import mock
import httpretty
from click.testing import CliRunner

from tests import mock_config

from openag.couch import Server
from openag.db_names import per_farm_dbs
from openag.cli.cloud import show, register, login, logout

@mock_config({
    "cloud_server": {
        "url": None
    }
})
def test_user_without_cloud_server(config):
    runner = CliRunner()

    # Show -- Should raise an error because there is no cloud server
    res = runner.invoke(show)
    assert res.exit_code, res.output

    # Register -- Should raise an error because there is no cloud server
    res = runner.invoke(register, input="test\ntest\ntest\n")
    assert res.exit_code, res.output

    # Login -- Should raise an error because there is no cloud server
    res = runner.invoke(login, input="test\ntest\n")
    assert res.exit_code, res.output

    # Logout -- Should raise an error because there is no cloud server
    res = runner.invoke(logout)
    assert res.exit_code, res.output

@mock_config({
    "cloud_server": {
        "url": "http://test.test:5984",
        "username": None,
        "password": None,
        "farm_name": None
    }
})
@httpretty.activate
def test_user_with_cloud_server(config):
    runner = CliRunner()

    # Register -- Should work
    httpretty.register_uri(
        httpretty.HEAD, "http://test.test:5984/_users"
    )
    httpretty.register_uri(
        httpretty.PUT, "http://test.test:5984/_users/org.couchdb.user%3Atest",
        status=201
    )
    res = runner.invoke(register, input="test\ntest\ntest\n")
    assert res.exit_code == 0, res.exception or res.output

    # Login -- Should work
    httpretty.register_uri(
        httpretty.GET, "http://test.test:5984/_session"
    )
    res = runner.invoke(login, input="test\ntest\n")
    assert res.exit_code == 0, res.exception or res.output

    # Login -- Should throw an error because you're already logged in as a
    # different user
    res = runner.invoke(login, input="test2\ntest2\n")
    assert res.exit_code, res.output
    assert isinstance(res.exception, SystemExit)

    # Logout -- Should work
    res = runner.invoke(logout)
    assert res.exit_code == 0, res.exception or res.output

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
@mock.patch("openag.cli.utils.cancel_per_farm_db_replication")
def test_logout_with_farm(config, cancel_per_farm_db_replication):
    runner = CliRunner()

    # Logout -- Should get rid of the farm and cancel per-farm replication
    res = runner.invoke(logout)
    assert res.exit_code == 0, res.exception or res.output
    assert cancel_per_farm_db_replication.call_count == 1
    assert config["cloud_server"]["farm_name"] is None

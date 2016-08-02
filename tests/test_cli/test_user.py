"""
Tests the ability to log in to a cloud server
"""
import json
import mock
from click.testing import CliRunner
import requests_mock

from tests import mock_config

from openag.couchdb import Server
from openag.db_names import per_farm_dbs
from openag.cli.user import show, register, login, logout

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
@requests_mock.Mocker()
def test_user_with_cloud_server(config, m):
    runner = CliRunner()

    # Show -- Should raise an error because the user is not logged in
    res = runner.invoke(show)
    assert res.exit_code, res.output

    # Register -- Should work
    m.get("http://test.test:5984/_all_dbs", text="[]")
    m.put(
        "http://test.test:5984/_users/org.couchdb.user%3Atest",
        status_code=201, text="{}"
    )
    res = runner.invoke(register, input="test\ntest\ntest\n")
    assert res.exit_code == 0, res.exception or res.output

    # Show -- Should raise an error because the user is not logged in
    res = runner.invoke(show)
    assert res.exit_code, res.exception or res.output

    # Login -- Should work
    m.get("http://test.test:5984/_session", text="{}")
    res = runner.invoke(login, input="test\ntest\n")
    assert res.exit_code == 0, res.exception or res.output

    # Show -- Should work
    res = runner.invoke(show)
    assert res.exit_code == 0, res.exception or res.output

    # Logout -- Should work
    res = runner.invoke(logout)
    assert res.exit_code == 0, res.exception or res.output

    # Show -- Should raise an error because the user is not logged in
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
@mock.patch.object(Server, "cancel_replication")
@requests_mock.Mocker()
def test_logout_with_farm(config, cancel_replication, m):
    runner = CliRunner()
    m.get("http://localhost:5984/_all_dbs", text=json.dumps([]))

    # Logout -- Should get rid of the farm and cancel per-farm replication
    res = runner.invoke(logout)
    assert res.exit_code == 0, res.exception or res.output
    assert cancel_replication.call_count == len(per_farm_dbs)
    assert config["cloud_server"]["farm_name"] is None

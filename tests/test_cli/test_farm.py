"""
Tests the ability to set up mirroring with a cloud server
"""
import json
import mock
import httpretty

from click.testing import CliRunner

from tests import mock_config

from openag.couch import Server
from openag.db_names import per_farm_dbs
from openag.cli.farm import show, create, list, init, deinit

@mock_config({
    "cloud_server": {
        "url": None
    }
})
def test_farm_without_cloud_server(config):
    runner = CliRunner()

    # Show -- Should raise an error because there is no cloud server
    res = runner.invoke(show)
    assert res.exit_code, res.output

    # Create -- Should raise an error because there is no cloud server
    res = runner.invoke(create)
    assert res.exit_code, res.output

    # List -- Should raise an error because there is no cloud server
    res = runner.invoke(list)
    assert res.exit_code, res.output
    assert isinstance(res.exception, SystemExit)

    # Init -- Should raise an error because there is no cloud server
    res = runner.invoke(init)
    assert res.exit_code, res.output

    # Deinit -- Should raise an error because there is no cloud server
    res = runner.invoke(deinit)
    assert res.exit_code, res.output

@mock_config({
    "cloud_server": {
        "url": "http://test.test:5984",
        "username": None,
        "password": None,
        "farm_name": None
    }
})
def test_farm_without_user(config):
    runner = CliRunner()

    # Show -- Should raise an error because no farm is selected
    res = runner.invoke(show)
    assert res.exit_code, res.output

    # Create -- Should raise an error because the user is not logged in
    res = runner.invoke(create)
    assert res.exit_code, res.output

    # List -- Should raise an error because the user is not logged in
    res = runner.invoke(list)
    assert res.exit_code, res.output
    assert isinstance(res.exception, SystemExit)

    # Init -- Should raise an error becuase the user is not logged in
    res = runner.invoke(init)
    assert res.exit_code, res.output

    # Deinit -- Should raise an error because no farm is selected
    res = runner.invoke(deinit)
    assert res.exit_code, res.output

@mock_config({
    "cloud_server": {
        "url": "http://test.test:5984",
        "username": "test",
        "password": "test",
        "farm_name": None
    },
    "local_server": {
        "url": None
    }
})
@httpretty.activate
def test_farm_with_only_cloud_server(config):
    runner = CliRunner()

    # Show -- Should raise an error because no farm is selected
    res = runner.invoke(show)
    assert res.exit_code, res.output

    # List -- Should raise an error because there are no farms yet
    global current_farms
    current_farms = []
    httpretty.register_uri(
        httpretty.GET, "http://test.test:5984/_session"
    )
    httpretty.register_uri(
        httpretty.HEAD, "http://test.test:5984/_users"
    )
    def get_user_info(request, uri, headers):
        global current_farms
        res = json.dumps({
            "farms": current_farms
        })
        return 200, headers, res
    httpretty.register_uri(
        httpretty.GET, "http://test.test:5984/_users/org.couchdb.user%3Atest",
        content_type="application/json", body=get_user_info
    )
    res = runner.invoke(list)
    assert res.exit_code, res.output
    assert isinstance(res.exception, SystemExit)

    # Create -- Should work
    httpretty.register_uri(
        httpretty.POST, "http://test.test:5984/_openag/v0.1/register_farm"
    )
    res = runner.invoke(create, ["test"])
    assert res.exit_code == 0, res.exception or res.output
    current_farms.append("test")

    res = runner.invoke(list)
    assert res.exit_code == 0, res.exception or res.output
    assert res.output == "test\n", res.output

    # Show -- Should raise an error because no farm is selected
    res = runner.invoke(show)
    assert res.exit_code, res.output

    # Init -- Should work
    res = runner.invoke(init, ["test"])
    assert res.exit_code == 0, res.exception or res.output

    # Init -- Should throw an error because a farm is already selected
    res = runner.invoke(init, ["test2"])
    assert res.exit_code, res.output
    assert isinstance(res.exception, SystemExit)

    # Show -- Should work and output "test"
    res = runner.invoke(show)
    assert res.exit_code == 0, res.exception or res.output

    # List -- Should have an asterisk before "test"
    res = runner.invoke(list)
    assert res.output == "*test\n", res.exception or res.output

    # Deinit -- Should work
    res = runner.invoke(deinit)
    assert res.exit_code == 0, res.exception or res.output

    # Show -- Should raise an error because no farm is selected
    res = runner.invoke(show)
    assert res.exit_code, res.output

    # List -- Should work and output "test"
    res = runner.invoke(list)
    assert res.output == "test\n", res.exception or res.output

@mock_config({
    "cloud_server": {
        "url": "http://test.test:5984",
        "username": "test",
        "password": "test",
        "farm_name": None
    },
    "local_server": {
        "url": "http://localhost:5984"
    }
})
@mock.patch("openag.cli.utils.replicate_per_farm_dbs")
@mock.patch("openag.cli.utils.cancel_per_farm_db_replication")
@httpretty.activate
def test_farm_with_cloud_and_local_server(
    config, cancel_per_farm_db_replication, replicate_per_farm_dbs
):
    runner = CliRunner()

    # Init -- Should replicate per farm DBs
    res = runner.invoke(init, ["test"])
    assert res.exit_code == 0, res.exception or res.output
    assert replicate_per_farm_dbs.call_count == 1

    # Deinit -- Should cancel replication of per farm DBs
    res = runner.invoke(deinit)
    assert res.exit_code == 0, res.exception or res.output
    assert cancel_per_farm_db_replication.call_count == 1

"""
Tests the ability to set up mirroring with a cloud server
"""
import mock

from click.testing import CliRunner
import requests_mock

from tests import mock_config

from openag.couchdb import Server
from openag.db_names import per_farm_dbs
from openag.cli.cloud.farm import show, create, list, select, unselect

def test_farm_without_cloud_server():
    runner = CliRunner()
    mock_config({
        "cloud_server": {
            "url": None
        }
    })

    # Show -- Should raise an error because there is no cloud server
    assert runner.invoke(show).exit_code

    # Create -- Should raise an error because there is no cloud server
    assert runner.invoke(create).exit_code

    # List -- Should raise an error because there is no cloud server
    assert runner.invoke(list).exit_code

    # Select -- Should raise an error because there is no cloud server
    assert runner.invoke(select).exit_code

    # Remove -- Should raise an error because there is no cloud server
    assert runner.invoke(unselect).exit_code

def test_farm_without_user():
    runner = CliRunner()
    mock_config({
        "cloud_server": {
            "url": "http://test.test:5984",
            "username": None,
            "password": None,
            "farm_name": None
        }
    })

    # Show -- Should raise an error because no farm is selected
    assert runner.invoke(show).exit_code

    # Create -- Should raise an error because the user is not logged in
    assert runner.invoke(create).exit_code

    # List -- Should raise an error because the user is not logged in
    assert runner.invoke(list).exit_code

    # Select -- Should raise an error becuase the user is not logged in
    assert runner.invoke(select).exit_code

    # Remove -- Should raise an error because no farm is selected
    assert runner.invoke(unselect).exit_code

@requests_mock.Mocker()
def test_farm_with_only_cloud_server(m):
    runner = CliRunner()
    mock_config({
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

    # Show -- Should raise an error because no farm is selected
    assert runner.invoke(show).exit_code

    # List -- Should raise an error because there are no farms yet
    m.get("http://test.test:5984/_all_dbs", text="[]")
    m.get("http://test.test:5984/_session", text="{}")
    m.get("http://test.test:5984/_users/org.couchdb.user%3Atest", text="{}")
    assert runner.invoke(list).exit_code

    # Create -- Should work
    m.post("http://test.test:5984/_openag/v0.1/register_farm", text="{}")
    assert runner.invoke(create, ["test"]).exit_code == 0

    # List -- Should output "test"
    m.get(
        "http://test.test:5984/_users/org.couchdb.user%3Atest",
        text='{"farms": ["test"]}'
    )
    assert runner.invoke(list).output == "test\n"

    # Show -- Should raise an error because no farm is selected
    assert runner.invoke(show).exit_code

    # Select -- Should work
    assert runner.invoke(select, ["test"]).exit_code == 0

    # Show -- Should work and output "test"
    assert runner.invoke(show).exit_code == 0

    # List -- Should have an asterisk before "test"
    assert runner.invoke(list).output == "*test\n"

    # Unselect -- Should work
    assert runner.invoke(unselect).exit_code == 0

    # Show -- Should raise an error because no farm is selected
    assert runner.invoke(show).exit_code

    # List -- Should work and output "test"
    assert runner.invoke(list).output == "test\n"

@mock.patch.object(Server, "replicate")
@requests_mock.Mocker()
def test_farm_with_cloud_and_local_server(replicate, m):
    runner = CliRunner()
    mock_config({
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

    # Select -- Should replicate per farm DBs
    m.get("http://localhost:5984/_all_dbs", text="[]")
    assert runner.invoke(select, ["test"]).exit_code == 0
    assert replicate.call_count == len(per_farm_dbs)
    replicate.reset_mock()

    # Deselect -- Should cancel replication of per farm DBs
    assert runner.invoke(unselect).exit_code == 0
    assert replicate.call_count == len(per_farm_dbs)

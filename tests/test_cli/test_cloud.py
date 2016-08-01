"""
Tests the ability to connect to and disconnect from a cloud server
"""
import mock
from click.testing import CliRunner
import requests_mock

from tests import mock_config

from openag.db_names import global_dbs
from openag.couchdb import Server
from openag.cli.cloud import init, show, remove

@mock.patch.object(Server, "replicate")
def test_cloud_without_local_server(replicate):
    runner = CliRunner()
    mock_config({
        "cloud_server": {
            "url": None
        },
        "local_server": {
            "url": None
        }
    })

    # Show -- Should raise an error because there is no cloud server
    assert runner.invoke(show).exit_code

    # Remove -- Should raise an error because there is no cloud server
    result = runner.invoke(remove)
    assert result.exit_code

    # Init -- Should work but not replicate any DBs
    assert runner.invoke(init, ["http://test.test:5984"]).exit_code == 0
    assert replicate.call_count == 0

    # Show -- Should work
    assert runner.invoke(show).exit_code == 0

    # Remove -- Should work and not cancel any replications
    assert runner.invoke(remove).exit_code == 0
    assert replicate.call_count == 0

    # Show -- Should raise an error becuase there is no cloud server
    assert runner.invoke(show).exit_code

@mock.patch.object(Server, "replicate")
@requests_mock.Mocker()
def test_cloud_with_local_server(replicate, m):
    mock_config({
        "cloud_server": {
            "url": None,
            "farm_name": None
        },
        "local_server": {
            "url": "http://localhost:5984"
        }
    })
    m.get("http://localhost:5984/_all_dbs", text="[]")
    runner = CliRunner()

    # Show -- Should raise an error because there is no cloud server
    assert runner.invoke(show).exit_code

    # Remove -- Should raise an error because there is no cloud server
    result = runner.invoke(remove)
    assert result.exit_code

    # Init -- Should work but not replicate any DBs
    assert runner.invoke(init, ["http://test.test:5984"]).exit_code == 0
    assert replicate.call_count == len(global_dbs)
    replicate.reset_mock()

    # Init -- Should work because it should be idempotent
    assert runner.invoke(init, ["http://test.test:5984"]).exit_code == 0
    assert replicate.call_count == len(global_dbs)
    replicate.reset_mock()

    # Show -- Should work
    assert runner.invoke(show).exit_code == 0

    # Remove -- Should work and not cancel any replications
    assert runner.invoke(remove).exit_code == 0
    assert replicate.call_count == len(global_dbs)

    # Show -- Should raise an error becuase there is no cloud server
    assert runner.invoke(show).exit_code

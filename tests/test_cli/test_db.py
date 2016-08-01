"""
Tests interactions with the local database
"""
import json
import mock

from click.testing import CliRunner
import requests_mock

from tests import mock_config

from openag.couchdb import Server
from openag.db_names import all_dbs
from openag.cli.db import init, load_fixture

@mock.patch("openag.cli.db.generate_config")
@mock.patch.object(Server, "get_or_create_db")
@mock.patch.object(Server, "push_design_documents")
@requests_mock.Mocker()
def test_init_without_cloud_server(
    push_design_documents, get_or_create_db, generate_config, m
):
    runner = CliRunner()
    mock_config({
        "local_server": {
            "url": None
        },
        "cloud_server": {
            "url": None
        }
    })

    m.get("http://localhost:5984/_all_dbs", text=json.dumps(list(all_dbs)))
    generate_config.return_value = {"test": {"test": "test"}}
    m.get("http://localhost:5984/_config/test/test", text='""')
    m.put("http://localhost:5984/_config/test/test")
    assert runner.invoke(init).exit_code == 0
    assert push_design_documents.call_count == 1
    push_design_documents.reset_mock()

@mock.patch("openag.cli.db.generate_config")
@mock.patch.object(Server, "get_or_create_db")
@mock.patch.object(Server, "push_design_documents")
@mock.patch.object(Server, "replicate")
@requests_mock.Mocker()
def test_init_with_cloud_server(
    replicate, push_design_documents, get_or_create_db, generate_config, m
):
    runner = CliRunner()
    mock_config({
        "local_server": {
            "url": None
        } ,
        "cloud_server": {
            "url": "http://test.test:5984",
            "username": "test",
            "password": "test",
            "farm_name": "test"
        }
    })

    m.get(
        "http://localhost:5984/_all_dbs", text=json.dumps(
            list(all_dbs)+["_replicator"]
        )
    )
    generate_config.return_value = {"test": {"test": "test"}}
    m.get("http://localhost:5984/_config/test/test", text='""')
    m.put("http://localhost:5984/_config/test/test")
    assert runner.invoke(init).exit_code == 0
    assert push_design_documents.call_count == 1
    push_design_documents.reset_mock()

def test_load_fixture_without_local_server():
    runner = CliRunner()
    mock_config({
        "local_server": {
            "url": None
        }
    })

    assert runner.invoke(init).exit_code

@requests_mock.Mocker()
def test_load_fixture_with_local_server(m):
    runner = CliRunner()
    mock_config({
        "local_server": {
            "url": "http://localhost:5984"
        }
    })

    m.get("http://localhost:5984/_all_dbs", text=json.dumps(list(all_dbs)))
    with runner.isolated_filesystem():
        with open("fixture.json", "w+") as f:
            json.dump({
                "recipes": [
                    {
                        "_id": "test",
                        "format": "test",
                        "operations": ["test", "test"]
                    }
                ]
            }, f)
        m.get("http://localhost:5984/recipes/test", status_code=404)
        m.put("http://localhost:5984/recipes/test", status_code=201, text="{}")
        assert runner.invoke(load_fixture, ["fixture.json"]).exit_code == 0

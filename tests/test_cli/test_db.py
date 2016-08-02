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

@mock_config({
    "local_server": {
        "url": None
    },
    "cloud_server": {
        "url": None
    }
})
@mock.patch("openag.cli.db.generate_config")
@mock.patch.object(Server, "get_or_create_db")
@mock.patch.object(Server, "push_design_documents")
@mock.patch.object(Server, "replicate")
@requests_mock.Mocker()
def test_init_without_cloud_server(
    config, replicate, push_design_documents, get_or_create_db,
    generate_config, m
):
    runner = CliRunner()

    m.get("http://localhost:5984/_all_dbs", text=json.dumps(list(all_dbs)))
    generate_config.return_value = {"test": {"test": "test"}}
    m.get("http://localhost:5984/_config/test/test", text='""')
    m.put("http://localhost:5984/_config/test/test")

    # Init -- Should work and push the design documents but not replicate
    # anything
    res = runner.invoke(init)
    assert res.exit_code == 0, res.exception or res.output
    assert push_design_documents.call_count == 1
    push_design_documents.reset_mock()
    assert replicate.call_count == 0
    replicate.reset_mock()

    # Init -- Should throw an error because a different database is already
    # selected
    res = runner.invoke(init, ["--db_url", "http://test.test:5984"])
    assert res.exit_code, res.output

@mock_config({
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
@mock.patch("openag.cli.db.generate_config")
@mock.patch.object(Server, "get_or_create_db")
@mock.patch.object(Server, "push_design_documents")
@mock.patch.object(Server, "replicate")
@requests_mock.Mocker()
def test_init_with_cloud_server(
    config, replicate, push_design_documents, get_or_create_db,
    generate_config, m
):
    runner = CliRunner()

    m.get(
        "http://localhost:5984/_all_dbs", text=json.dumps(
            list(all_dbs)+["_replicator"]
        )
    )
    generate_config.return_value = {"test": {"test": "test"}}
    m.get("http://localhost:5984/_config/test/test", text='""')
    m.put("http://localhost:5984/_config/test/test")

    # Init -- Sould work, push the design documents, and replicate the DBs
    res = runner.invoke(init)
    assert res.exit_code == 0, res.exception or res.output
    assert push_design_documents.call_count == 1
    push_design_documents.reset_mock()
    assert replicate.call_count == len(all_dbs)
    replicate.reset_mock()

@mock_config({
    "local_server": {
        "url": None
    }
})
def test_load_fixture_without_local_server(config):
    runner = CliRunner()

    # Load_fixtue -- Should throw an error because there is no local server
    res = runner.invoke(load_fixture, ["test"])
    assert res.exit_code, res.output

@mock_config({
    "local_server": {
        "url": "http://localhost:5984"
    }
})
@requests_mock.Mocker()
def test_load_fixture_with_local_server(config, m):
    runner = CliRunner()

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
        m.get(
            "http://localhost:5984/recipes/_all_docs?include_docs=True",
            text='{"rows": []}'
        )
        m.put("http://localhost:5984/recipes/test", status_code=201, text="{}")

        # Load_fixture -- Should work
        res = runner.invoke(load_fixture, ["fixture.json"])
        assert res.exit_code == 0, res.exception or res.output

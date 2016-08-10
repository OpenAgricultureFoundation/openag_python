"""
Tests interactions with the local database
"""
import json
import mock
import httpretty

from click.testing import CliRunner

from tests import mock_config

from openag.couch import Server
from openag.db_names import all_dbs
from openag.cli.db import init, load_fixture, show

@mock_config({
    "local_server": {
        "url": None
    },
    "cloud_server": {
        "url": None
    }
})
@mock.patch("openag.cli.db.generate_config")
@mock.patch.object(Server, "get_or_create")
@mock.patch.object(Server, "push_design_documents")
@httpretty.activate
def test_init_without_cloud_server(
    config, push_design_documents, get_or_create, generate_config
):
    runner = CliRunner()

    generate_config.return_value = {"test": {"test": "test"}}
    httpretty.register_uri(
        httpretty.GET, "http://localhost:5984/_config/test/test",
        body='"test_val"'
    )
    httpretty.register_uri(
        httpretty.PUT, "http://localhost:5984/_config/test/test"
    )

    # Show -- Should throw an error because no local server is selected
    res = runner.invoke(show)
    assert res.exit_code, res.output

    # Init -- Should work and push the design documents but not replicate
    # anything
    res = runner.invoke(init)
    assert res.exit_code == 0, res.exception or res.output
    assert get_or_create.call_count == len(all_dbs)
    assert push_design_documents.call_count == 1
    push_design_documents.reset_mock()

    # Show -- Should work
    res = runner.invoke(show)
    assert res.exit_code == 0, res.exception or res.output

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
@mock.patch("openag.cli.utils.replicate_per_farm_dbs")
@mock.patch("openag.cli.utils.replicate_global_dbs")
@mock.patch("openag.cli.db.generate_config")
@mock.patch.object(Server, "get_or_create")
@mock.patch.object(Server, "push_design_documents")
def test_init_with_cloud_server(
    config, push_design_documents, get_or_create, generate_config,
    replicate_global_dbs, replicate_per_farm_dbs
):
    runner = CliRunner()

    generate_config.return_value = {}

    # Init -- Sould work, push the design documents, and replicate the DBs
    res = runner.invoke(init)
    assert res.exit_code == 0, res.exception or res.output
    assert push_design_documents.call_count == 1
    assert replicate_global_dbs.call_count == 1
    assert replicate_per_farm_dbs.call_count == 1

@mock_config({
    "local_server": {
        "url": None
    }
})
def test_load_fixture_without_local_server(config):
    runner = CliRunner()

    # Load_fixture -- Should throw an error because there is no local server
    with runner.isolated_filesystem():
        with open("fixture.json", "w+") as f:
            f.write("{}")
        res = runner.invoke(load_fixture, ["fixture.json"])
    assert res.exit_code, res.output

@mock_config({
    "local_server": {
        "url": "http://localhost:5984"
    }
})
@httpretty.activate
def test_load_fixture_with_local_server(config):
    runner = CliRunner()

    with runner.isolated_filesystem():
        global doc
        doc = {
            "_id": "test",
            "format": "test",
            "operations": ["test", "test"]
        }
        with open("fixture.json", "w+") as f:
            json.dump({
                "recipes": [doc]
            }, f)

        # Load_fixture -- Should work
        httpretty.register_uri(
            httpretty.HEAD, "http://localhost:5984/recipes"
        )
        def test_recipe_exists(request, uri, headers):
            global doc
            if "_rev" in doc:
                return 200, headers, ""
            else:
                return 404, headers, ""
        httpretty.register_uri(
            httpretty.HEAD, "http://localhost:5984/recipes/test",
            content_type="application/json", body=test_recipe_exists
        )
        def get_test_recipe(request, uri, headers):
            global doc
            if "_rev" in doc:
                return 200, headers, json.dumps(doc)
            else:
                return 404, headers, ""
        httpretty.register_uri(
            httpretty.GET, "http://localhost:5984/recipes/test",
            content_type="application/json", body=get_test_recipe
        )
        def create_test_recipe(request, uri, headers):
            global doc
            in_doc = json.loads(request.body)
            if "_rev" in doc:
                if "_rev" not in in_doc or in_doc["_rev"] != doc["_rev"]:
                    return 409, headers, json.dumps({
                        "error": "conflict",
                        "reason": "Document update conflict"
                    })
                else:
                    doc["_rev"] = doc["_rev"] = "a"
            else:
                doc["_rev"] = "a"
            return 200, headers, json.dumps({
                "id": doc["_id"], "rev": doc["_rev"]
            })
        httpretty.register_uri(
            httpretty.PUT, "http://localhost:5984/recipes/test",
            content_type="application/json", body=create_test_recipe
        )
        res = runner.invoke(load_fixture, ["fixture.json"])
        assert res.exit_code == 0, res.exception or res.output

        res = runner.invoke(load_fixture, ["fixture.json"])
        assert res.exit_code == 0, res.exception or res.output

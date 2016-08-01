"""
Tests the ability to log in to a cloud server
"""
from click.testing import CliRunner
import requests_mock

from tests import mock_config

from openag.cli.cloud.user import show, register, login, logout

def test_user_without_cloud_server():
    runner = CliRunner()
    mock_config({
        "cloud_server": {
            "url": None
        }
    })

    # Show -- Should raise an error because there is no cloud server
    assert runner.invoke(show).exit_code

    # Register -- Should raise an error because there is no cloud server
    assert runner.invoke(register, input="test\ntest\ntest\n").exit_code

    # Login -- Should raise an error because there is no cloud server
    assert runner.invoke(login, input="test\ntest\n").exit_code

    # Logout -- Should raise an error because there is no cloud server
    assert runner.invoke(logout).exit_code

@requests_mock.Mocker()
def test_user_with_cloud_server(m):
    runner = CliRunner()
    mock_config({
        "cloud_server": {
            "url": "http://test.test:5984",
            "username": None,
            "password": None
        }
    })

    # Show -- Should raise an error because the user is not logged in
    assert runner.invoke(show).exit_code

    # Register -- Should work
    m.get("http://test.test:5984/_all_dbs", text="[]")
    m.put(
        "http://test.test:5984/_users/org.couchdb.user%3Atest",
        status_code=201, text="{}"
    )
    assert runner.invoke(register, input="test\ntest\ntest\n").exit_code == 0

    # Show -- Should raise an error because the user is not logged in
    assert runner.invoke(show).exit_code

    # Login -- Should work
    m.get("http://test.test:5984/_session", text="{}")
    res = runner.invoke(login, input="test\ntest\n")

    # Show -- Should work
    assert runner.invoke(show).exit_code == 0

    # Logout -- Should work
    assert runner.invoke(logout).exit_code == 0

    # Show -- Should raise an error because the user is not logged in
    assert runner.invoke(show).exit_code

import os
import yaml

from ORStools.utils.configmanager import read_config

with open("ORStools/config.yml", "r+") as file:
    data = yaml.safe_load(file)


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    if data["providers"][0]["key"] == "":
        data["providers"][0]["key"] = os.environ.get("ORS_API_KEY")
        with open("ORStools/config.yml", "w") as file:
            yaml.dump(data, file)
    else:
        raise ValueError("API key is not empty.")


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    with open("ORStools/config.yml", "w") as file:
        if not data["providers"][0]["key"] == "":
            data['providers'][0]['key'] = ''  # fmt: skip
        yaml.dump(data, file)

    config = read_config()
    assert config["providers"][0]["key"] == ''  # fmt: skip

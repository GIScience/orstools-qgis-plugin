import os

from qgis.core import QgsSettings

from ORStools.ORStoolsPlugin import ORStools
from ORStools.utils.configmanager import read_config
from tests.utils.utilities import get_qgis_app

QGISAPP, CANVAS, IFACE, PARENT = get_qgis_app()

ORStools(IFACE).add_default_provider_to_settings()
s = QgsSettings()
data = s.value("ORStools/config")

def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    if data["providers"][0]["key"] == "":
        data["providers"][0]["key"] = os.environ.get("ORS_API_KEY")
        s.setValue("ORStools/config", data)
    else:
        raise ValueError("API key is not empty.")


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    if not data["providers"][0]["key"] == "":
        data['providers'][0]['key'] = ''  # fmt: skip
    s.setValue("ORStools/config", data)
    config = read_config()
    assert config["providers"][0]["key"] == ''  # fmt: skip

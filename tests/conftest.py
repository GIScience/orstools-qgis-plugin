import os

from qgis.core import QgsSettings

from ORStools.ORStoolsPlugin import ORStools
from tests.utils.utilities import get_qgis_app

def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    QGISAPP, CANVAS, IFACE, PARENT = get_qgis_app()

    ORStools(IFACE).add_default_provider_to_settings()
    s = QgsSettings()
    data = s.value("ORStools/config")

    if not os.environ.get("ORS_API_KEY"):
        raise ValueError(
            "No API key found in environment variables. Please set ORS_API_KEY environment variable to run tests."
        )
    data["providers"][0]["key"] = os.environ.get("ORS_API_KEY")
    s.setValue("ORStools/config", data)

from qgis.core import QgsMessageLog, Qgis

from ORStools import PLUGIN_NAME

def log(message, level_in=0):
    """uses QGIS inbuilt logger accessible through panel"""
    if level_in == 0:
        level = Qgis.Info
    elif level_in == 1:
        level = Qgis.Warning
    elif level_in == 2:
        level = Qgis.Critical
    else:
        level = Qgis.Info

    return QgsMessageLog.logMessage(message, PLUGIN_NAME.strip(), level)
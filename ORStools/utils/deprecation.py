# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
                              -------------------
        begin                : 2026-11-12
        git sha              : $Format:%H$
        copyright            : (C) 2026 by HeiGIT gGmbH
        email                : support@openrouteservice.heigit.org
 ***************************************************************************/

 This plugin provides access to openrouteservice API functionalities
 (https://openrouteservice.org), developed and
 maintained by the openrouteservice team of HeiGIT gGmbH, Germany. By using
 this plugin you agree to the ORS terms of service
 (https://openrouteservice.org/terms-of-service/).

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from . import configmanager
from qgis.PyQt.QtWidgets import QMessageBox
from ..proc import ENDPOINTS, DEFAULT_SETTINGS

class DeprecatedUrlDialog(QMessageBox):
    """Dialog informing the user that the configured URL is deprecated."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setIcon(QMessageBox.Icon.Warning)
        self.setWindowTitle(self.tr("ORS Tools: Deprecated URL"))

        self.setText(
            self.tr(
                "<b>ORSTools Plugin:</b> <br /><br />"
                "The configured ORS provider URL <tt>https://api.openrouteservice.org</tt> is <a href='https://ask.openrouteservice.org/t/deprecating-api-openrouteservice-org-in-favour-of-api-heigit-org/7912'>deprecated</a>.<br />"
                "Would you like to reset it to the new default URL <tt>https://api.heigit.org</tt>?"
            )
        )

        self.reset_button = self.addButton(self.tr("Reset URL"), QMessageBox.ButtonRole.AcceptRole)

        self.addButton(self.tr("Close"), QMessageBox.ButtonRole.RejectRole)


def url_dialog_reset_button(parent=None) -> bool:
    """Shows the deprecated URL dialog and returns bool."""

    url_dlg = DeprecatedUrlDialog(parent)
    url_dlg.exec()
    return url_dlg.clickedButton() == url_dlg.reset_button

def add_default_provider_to_settings():
    settings = configmanager.read_config()

    settings_keys = ["ENV_VARS", "base_url", "key", "name", "endpoints"]

    # Add any new settings here for backwards compatibility
    if settings:
        changed = False
        for i, prov in enumerate(settings["providers"]):
            if any([i not in prov for i in settings_keys]):
                changed = True
                # Add here, like the endpoints
                prov["endpoints"] = ENDPOINTS
                settings["providers"][i] = prov
        if changed:
            configmanager.write_config(settings)
    else:
        configmanager.write_config(DEFAULT_SETTINGS)

def url_is_deprecated() -> bool:
    settings = configmanager.read_config()

    if not settings:
        return False

    legacy_url = "https://api.openrouteservice.org"

    return any(legacy_url in provider["base_url"] for provider in settings["providers"])

def reset_provider_url():
    """Reset the first provider URL to the default URL."""

    settings = configmanager.read_config()

    if not settings:
        return

    default_url = DEFAULT_SETTINGS["providers"][0]["base_url"]
    legacy_url = "https://api.openrouteservice.org"

    for provider_config in settings.get("providers", []):
        if provider_config.get("base_url") == legacy_url:
            provider_config["base_url"] = default_url

    configmanager.write_config(settings)

def check_provider_url(parent=None):
    if url_is_deprecated():
        if url_dialog_reset_button(parent):
            reset_provider_url()

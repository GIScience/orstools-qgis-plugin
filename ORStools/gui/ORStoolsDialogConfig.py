# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
                              -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2021 by HeiGIT gGmbH
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

from qgis.gui import QgsCollapsibleGroupBox

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QMetaObject
from qgis.PyQt.QtWidgets import (
    QDialog,
    QInputDialog,
    QLineEdit,
    QDialogButtonBox,
)
from qgis.PyQt.QtGui import QIntValidator

from ORStools.utils import configmanager, gui
from .ORStoolsDialogConfigUI import Ui_ORStoolsDialogConfigBase
from ..proc import ENDPOINTS, DEFAULT_SETTINGS

CONFIG_WIDGET, _ = uic.loadUiType(gui.GuiUtils.get_ui_file_path('ORStoolsDialogConfigUI.ui'))

class ORStoolsDialogConfigMain(QDialog, CONFIG_WIDGET):
    """Builds provider config dialog."""

    def __init__(self, parent=None) -> None:
        """
        :param parent: Parent window for modality.
        :type parent: QDialog
        """
        QDialog.__init__(self, parent)

        self.setupUi(self)

        # Temp storage for config dict
        self.temp_config = configmanager.read_config()

        self._build_ui()
        self._collapse_boxes()

        self.provider_add.clicked.connect(self._add_provider)
        self.provider_remove.clicked.connect(self._remove_provider)

        # Change OK to Save in config window
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("Save"))

    def accept(self) -> None:
        """When the OK Button is clicked, in-memory temp_config is updated and written to settings"""

        collapsible_boxes = self.providers.findChildren(QgsCollapsibleGroupBox)
        collapsible_boxes = [
            i for i in collapsible_boxes if "_provider_endpoints" not in i.objectName()
        ]
        for idx, box in enumerate(collapsible_boxes):
            current_provider = self.temp_config["providers"][idx]

            current_provider["key"] = box.findChild(
                QtWidgets.QLineEdit, box.title() + "_key_text"
            ).text()

            current_provider["base_url"] = box.findChild(
                QtWidgets.QLineEdit, box.title() + "_base_url_text"
            ).text()

            timeout_input = box.findChild(QtWidgets.QLineEdit, box.title() + "_timeout_text")
            # https://doc.qt.io/qt-5/qvalidator.html#State-enum

            if timeout_input.validator().State() != 2:
                self._adjust_timeout_input(timeout_input)

            current_provider["timeout"] = int(timeout_input.text())

            endpoint_box = box.findChild(
                QgsCollapsibleGroupBox, f"{box.title()}_provider_endpoints"
            )
            current_provider["endpoints"] = {
                "directions": endpoint_box.findChild(
                    QtWidgets.QLineEdit, box.title() + "_directions_endpoint"
                ).text(),
                "isochrones": endpoint_box.findChild(
                    QtWidgets.QLineEdit, box.title() + "_isochrones_endpoint"
                ).text(),
                "matrix": endpoint_box.findChild(
                    QtWidgets.QLineEdit, box.title() + "_matrix_endpoint"
                ).text(),
                "optimization": endpoint_box.findChild(
                    QtWidgets.QLineEdit, box.title() + "_optimization_endpoint"
                ).text(),
                "export": endpoint_box.findChild(
                    QtWidgets.QLineEdit, box.title() + "_export_endpoint"
                ).text(),
                "snapping": endpoint_box.findChild(
                    QtWidgets.QLineEdit, box.title() + "_snapping_endpoint"
                ).text(),
            }

        configmanager.write_config(self.temp_config)
        self.close()

    @staticmethod
    def _adjust_timeout_input(input_line_edit: QLineEdit) -> None:
        """
        Corrects the value of the input to the top or bottom value of
        the specified range of the QIntValidator for the field.
        Default to a timeout of 60 seconds if no value is given.
        :param input_line_edit: QLineEdit object to adjust
        """
        val = input_line_edit.validator()
        text = input_line_edit.text()
        if not text:
            input_line_edit.setText("60")
        elif int(text) < val.bottom():
            input_line_edit.setText(str(val.bottom()))
        elif int(text) > val.top():
            input_line_edit.setText(str(val.top()))

    def _build_ui(self) -> None:
        """Builds the UI on dialog startup."""

        for provider_entry in self.temp_config["providers"]:
            self._add_box(
                provider_entry["name"],
                provider_entry["base_url"],
                provider_entry["key"],
                provider_entry["timeout"],
                provider_entry["endpoints"],
                new=False,
            )

        self.gridLayout.addWidget(self.providers, 0, 0, 1, 3)

        QMetaObject.connectSlotsByName(self)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def _add_provider(self) -> None:
        """Adds an empty provider box to be filled out by the user."""

        self._collapse_boxes()
        # Show quick user input dialog
        provider_name, ok = QInputDialog.getText(
            self, self.tr("New ORS provider"), self.tr("Enter a name for the provider")
        )
        if ok:
            self._add_box(provider_name, "http://localhost:8082/ors", "", 60, ENDPOINTS, new=True)

    def _remove_provider(self) -> None:
        """Remove list of providers from list."""

        providers = [provider["name"] for provider in self.temp_config["providers"]]

        provider, ok = QInputDialog.getItem(
            self,
            self.tr("Remove ORS provider"),
            self.tr("Choose provider to remove"),
            providers,
            0,
            False,
        )
        if ok:
            box_remove = self.providers.findChild(QgsCollapsibleGroupBox, provider)
            self.gridLayout.removeWidget(box_remove)
            box_remove.deleteLater()

            # delete from in-memory self.temp_config
            provider_id = providers.index(provider)
            del self.temp_config["providers"][provider_id]

    def _collapse_boxes(self) -> None:
        """Collapse all QgsCollapsibleGroupBoxes."""
        collapsible_boxes = self.providers.findChildren(QgsCollapsibleGroupBox)
        for box in collapsible_boxes:
            box.setCollapsed(True)

    def _add_box(
        self, name: str, url: str, key: str, timeout: int, endpoints: dict, new: bool = False
    ) -> None:
        """
        Adds a provider box to the QWidget layout and self.temp_config.
        """
        if new:
            self.temp_config["providers"].append(
                dict(name=name, base_url=url, key=key, timeout=timeout, endpoints=endpoints)
            )

        provider = QgsCollapsibleGroupBox(self.providers)
        provider.setObjectName(name)
        provider.setTitle(name)
        gridLayout_3 = QtWidgets.QGridLayout(provider)
        gridLayout_3.setObjectName(name + "_grid")

        # API Key section
        key_label = QtWidgets.QLabel(provider)
        key_label.setObjectName(name + "_key_label")
        key_label.setText(self.tr("API Key"))
        gridLayout_3.addWidget(key_label, 0, 0, 1, 1)

        key_text = QtWidgets.QLineEdit(provider)
        key_text.setObjectName(name + "_key_text")
        key_text.setText(key)
        gridLayout_3.addWidget(key_text, 1, 0, 1, 4)

        # Base URL section
        base_url_label = QtWidgets.QLabel(provider)
        base_url_label.setObjectName("base_url_label")
        base_url_label.setText(self.tr("Base URL"))
        gridLayout_3.addWidget(base_url_label, 2, 0, 1, 1)

        base_url_text = QtWidgets.QLineEdit(provider)
        base_url_text.setObjectName(name + "_base_url_text")
        base_url_text.setText(url)
        gridLayout_3.addWidget(base_url_text, 3, 0, 1, 4)

        # Timeout section
        timeout_label = QtWidgets.QLabel(provider)
        timeout_label.setObjectName("timeout_label")
        timeout_label.setText(self.tr("Request timeout in seconds (1 - 3600)"))
        gridLayout_3.addWidget(timeout_label, 4, 0, 1, 1)

        timeout_text = QtWidgets.QLineEdit(provider)
        timeout_text.setObjectName(name + "_timeout_text")
        timeout_text.setText(str(timeout))
        timeout_text.setValidator(QIntValidator(1, 3600, timeout_text))
        gridLayout_3.addWidget(timeout_text, 5, 0, 1, 4)

        # Service Endpoints section
        endpoint_box = QgsCollapsibleGroupBox(provider)
        endpoint_box.setObjectName(name + "_provider_endpoints")
        endpoint_box.setTitle(self.tr("Service Endpoints"))
        endpoint_layout = QtWidgets.QGridLayout(endpoint_box)
        gridLayout_3.addWidget(endpoint_box, 6, 0, 1, 4)

        row = 0
        for endpoint_name, endpoint_value in endpoints.items():
            endpoint_label = QtWidgets.QLabel(endpoint_box)
            endpoint_label.setText(self.tr(endpoint_name.capitalize()))
            endpoint_layout.addWidget(endpoint_label, row, 0, 1, 1)

            endpoint_lineedit = QtWidgets.QLineEdit(endpoint_box)
            endpoint_lineedit.setText(endpoint_value)
            endpoint_lineedit.setObjectName(f"{name}_{endpoint_name}_endpoint")

            endpoint_layout.addWidget(endpoint_lineedit, row, 1, 1, 3)

            row += 1

        # Add reset buttons at the bottom
        button_layout = QtWidgets.QHBoxLayout()

        reset_url_button = QtWidgets.QPushButton(self.tr("Reset URL"), provider)
        reset_url_button.setObjectName(name + "_reset_url_button")
        reset_url_button.clicked.connect(
            lambda _, t=base_url_text: t.setText(DEFAULT_SETTINGS["providers"][0]["base_url"])
        )
        button_layout.addWidget(reset_url_button)

        reset_endpoints_button = QtWidgets.QPushButton(self.tr("Reset Endpoints"), provider)
        reset_endpoints_button.setObjectName(name + "_reset_endpoints_button")
        reset_endpoints_button.clicked.connect(self._reset_endpoints)
        button_layout.addWidget(reset_endpoints_button)

        gridLayout_3.addLayout(button_layout, 7, 0, 1, 4)

        self.verticalLayout.addWidget(provider)
        provider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    def _reset_endpoints(self) -> None:
        """Resets the endpoints to their original values."""
        for line_edit_remove in self.providers.findChildren(QLineEdit):
            name = line_edit_remove.objectName()
            if name.endswith("endpoint"):
                endpoint_name = name.split("_")[1]
                endpoint_value = ENDPOINTS[endpoint_name]
                line_edit_remove.setText(endpoint_value)

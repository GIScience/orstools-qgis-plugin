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

from PyQt5 import QtWidgets
from PyQt5.QtCore import QMetaObject
from PyQt5.QtWidgets import QDialog, QInputDialog

from qgis.gui import QgsCollapsibleGroupBox

from .ORStoolsDialogConfigUI import Ui_ORStoolsDialogConfigBase
from ORStools.utils import configmanager


class ORStoolsDialogConfigMain(QDialog, Ui_ORStoolsDialogConfigBase):
    """Builds provider config dialog."""

    def __init__(self, parent=None):
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

    def accept(self):
        """When the OK Button is clicked, in-memory temp_config is updated and written to config.yml"""

        collapsible_boxes = self.providers.findChildren(QgsCollapsibleGroupBox)
        for idx, box in enumerate(collapsible_boxes):
            current_provider = self.temp_config['providers'][idx]
            current_provider['key'] = box.findChild(QtWidgets.QLineEdit, box.title() + "_key_text").text()
            current_provider['base_url'] = box.findChild(QtWidgets.QLineEdit, box.title() + "_base_url_text").text()

        configmanager.write_config(self.temp_config)
        self.close()

    def _build_ui(self):
        """Builds the UI on dialog startup."""

        for provider_entry in self.temp_config['providers']:
            self._add_box(provider_entry['name'],
                          provider_entry['base_url'],
                          provider_entry['key'],
                          new=False)

        self.gridLayout.addWidget(self.providers, 0, 0, 1, 3)

        QMetaObject.connectSlotsByName(self)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def _add_provider(self):
        """Adds an empty provider box to be filled out by the user."""

        self._collapse_boxes()
        # Show quick user input dialog
        provider_name, ok = QInputDialog.getText(self, "New ORS provider", "Enter a name for the provider")
        if ok:
            self._add_box(provider_name, 'https://', '', new=True)

    def _remove_provider(self):
        """Remove list of providers from list."""

        providers = [provider['name'] for provider in self.temp_config['providers']]

        provider, ok = QInputDialog.getItem(self,
                                            "Remove ORS provider",
                                            "Choose provider to remove",
                                            providers, 0, False)
        if ok:
            box_remove = self.providers.findChild(QgsCollapsibleGroupBox, provider)
            self.gridLayout.removeWidget(box_remove)
            box_remove.deleteLater()
            box_remove = None

            # delete from in-memory self.temp_config
            provider_id = providers.index(provider)
            del self.temp_config['providers'][provider_id]

    def _collapse_boxes(self):
        """Collapse all QgsCollapsibleGroupBoxes."""
        collapsible_boxes = self.providers.findChildren(QgsCollapsibleGroupBox)
        for box in collapsible_boxes:
            box.setCollapsed(True)

    def _add_box(self,
                 name,
                 url,
                 key,
                 new=False):
        """
        Adds a provider box to the QWidget layout and self.temp_config.

        :param name: provider name
        :type name: str

        :param url: provider's base url
        :type url: str

        :param key: user's API key
        :type key: str

        :param new: Specifies whether user wants to insert provider or the GUI is being built.
        :type new: boolean
        """
        if new:
            self.temp_config['providers'].append(
                dict(
                    name=name,
                    base_url=url,
                    key=key,
                )
            )

        provider = QgsCollapsibleGroupBox(self.providers)
        provider.setObjectName(name)
        provider.setTitle(name)
        gridLayout_3 = QtWidgets.QGridLayout(provider)
        gridLayout_3.setObjectName(name + '_grid')
        key_label = QtWidgets.QLabel(provider)
        key_label.setObjectName(name + '_key_label')
        key_label.setText('API Key')
        gridLayout_3.addWidget(key_label, 0, 0, 1, 1)
        base_url_text = QtWidgets.QLineEdit(provider)
        base_url_text.setObjectName(name + "_base_url_text")
        base_url_text.setText(url)
        gridLayout_3.addWidget(base_url_text, 3, 0, 1, 4)
        key_text = QtWidgets.QLineEdit(provider)
        key_text.setObjectName(name + "_key_text")
        key_text.setText(key)
        gridLayout_3.addWidget(key_text, 1, 0, 1, 4)
        base_url_label = QtWidgets.QLabel(provider)
        base_url_label.setObjectName("base_url_label")
        base_url_label.setText("Base URL")
        gridLayout_3.addWidget(base_url_label, 2, 0, 1, 1)
        self.verticalLayout.addWidget(provider)
        provider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

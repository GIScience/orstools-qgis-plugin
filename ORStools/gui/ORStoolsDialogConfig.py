# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
                              -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Nils Nolde
        email                : nils.nolde@gmail.com
 ***************************************************************************/

 This plugin provides access to the various APIs from OpenRouteService
 (https://openrouteservice.org), developed and
 maintained by GIScience team at University of Heidelberg, Germany. By using
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

from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QIcon

from .ORStoolsDialogConfigUI import Ui_ORStoolsDialogConfigBase
from ORStools.utils import configmanager


class ORStoolsDialogConfigMain(QDialog, Ui_ORStoolsDialogConfigBase):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        self.setupUi(self)
        self.ok_btn = self.buttonBox.Apply
        self.cancel_btn = self.buttonBox.Cancel

        self.CONFIG = configmanager.read_config()

        # Populate line widgets
        self.key_text.setText(self.CONFIG['api_key'])
        self.base_url_text.setText(self.CONFIG['base_url'])
        self.quota_spinbox.setValue(self.CONFIG['req_per_min'])

        # Set up connections
        # self.ok_btn.clicked.connect(self.accept())

    def accept(self):
        new_config = {'api_key': self.key_text.text(),
                      'base_url': self.base_url_text.text(),
                      'req_per_min': self.quota_spinbox.value()}

        configmanager.write_config_all(new_config)
        self.close()
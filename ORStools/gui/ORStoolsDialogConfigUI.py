# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ORStools/gui/ORStoolsDialogConfigUI.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ORStoolsDialogConfigBase(object):
    def setupUi(self, ORStoolsDialogConfigBase):
        ORStoolsDialogConfigBase.setObjectName("ORStoolsDialogConfigBase")
        ORStoolsDialogConfigBase.resize(345, 151)
        self.gridLayout = QtWidgets.QGridLayout(ORStoolsDialogConfigBase)
        self.gridLayout.setObjectName("gridLayout")
        self.base_url_label = QtWidgets.QLabel(ORStoolsDialogConfigBase)
        self.base_url_label.setObjectName("base_url_label")
        self.gridLayout.addWidget(self.base_url_label, 2, 0, 1, 1)
        self.key_label = QtWidgets.QLabel(ORStoolsDialogConfigBase)
        self.key_label.setObjectName("key_label")
        self.gridLayout.addWidget(self.key_label, 0, 0, 1, 1)
        self.base_url_text = QtWidgets.QLineEdit(ORStoolsDialogConfigBase)
        self.base_url_text.setObjectName("base_url_text")
        self.gridLayout.addWidget(self.base_url_text, 3, 0, 1, 2)
        self.key_text = QtWidgets.QLineEdit(ORStoolsDialogConfigBase)
        self.key_text.setObjectName("key_text")
        self.gridLayout.addWidget(self.key_text, 1, 0, 1, 2)
        self.buttonBox = QtWidgets.QDialogButtonBox(ORStoolsDialogConfigBase)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 6, 0, 1, 2)
        self.gridLayout.setColumnStretch(0, 4)

        self.retranslateUi(ORStoolsDialogConfigBase)
        self.buttonBox.accepted.connect(ORStoolsDialogConfigBase.accept)
        self.buttonBox.rejected.connect(ORStoolsDialogConfigBase.reject)
        QtCore.QMetaObject.connectSlotsByName(ORStoolsDialogConfigBase)

    def retranslateUi(self, ORStoolsDialogConfigBase):
        _translate = QtCore.QCoreApplication.translate
        ORStoolsDialogConfigBase.setWindowTitle(_translate("ORStoolsDialogConfigBase", "ORS Settings"))
        self.base_url_label.setText(_translate("ORStoolsDialogConfigBase", "Base URL"))
        self.key_label.setText(_translate("ORStoolsDialogConfigBase", "API key"))
        self.base_url_text.setText(_translate("ORStoolsDialogConfigBase", "https://api.openrouteservice.org"))


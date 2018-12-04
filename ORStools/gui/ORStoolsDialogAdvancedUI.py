# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ORStools/gui/ORStoolsDialogAdvancedUI.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ORStoolsDialogAdvancedBase(object):
    def setupUi(self, ORStoolsDialogAdvancedBase):
        ORStoolsDialogAdvancedBase.setObjectName("ORStoolsDialogAdvancedBase")
        ORStoolsDialogAdvancedBase.resize(400, 208)
        self.verticalLayout = QtWidgets.QVBoxLayout(ORStoolsDialogAdvancedBase)
        self.verticalLayout.setObjectName("verticalLayout")
        self.routing_avoid_group = QtWidgets.QGroupBox(ORStoolsDialogAdvancedBase)
        self.routing_avoid_group.setObjectName("routing_avoid_group")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.routing_avoid_group)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.routing_avoid_highways = QtWidgets.QCheckBox(self.routing_avoid_group)
        self.routing_avoid_highways.setObjectName("routing_avoid_highways")
        self.gridLayout_9.addWidget(self.routing_avoid_highways, 0, 0, 1, 1)
        self.routing_avoid_toll = QtWidgets.QCheckBox(self.routing_avoid_group)
        self.routing_avoid_toll.setObjectName("routing_avoid_toll")
        self.gridLayout_9.addWidget(self.routing_avoid_toll, 0, 1, 1, 1)
        self.routing_avoid_tunnels = QtWidgets.QCheckBox(self.routing_avoid_group)
        self.routing_avoid_tunnels.setObjectName("routing_avoid_tunnels")
        self.gridLayout_9.addWidget(self.routing_avoid_tunnels, 1, 0, 1, 1)
        self.routing_avoid_ferries = QtWidgets.QCheckBox(self.routing_avoid_group)
        self.routing_avoid_ferries.setObjectName("routing_avoid_ferries")
        self.gridLayout_9.addWidget(self.routing_avoid_ferries, 1, 1, 1, 1)
        self.routing_avoid_fords = QtWidgets.QCheckBox(self.routing_avoid_group)
        self.routing_avoid_fords.setObjectName("routing_avoid_fords")
        self.gridLayout_9.addWidget(self.routing_avoid_fords, 2, 0, 1, 1)
        self.routing_avoid_paved = QtWidgets.QCheckBox(self.routing_avoid_group)
        self.routing_avoid_paved.setObjectName("routing_avoid_paved")
        self.gridLayout_9.addWidget(self.routing_avoid_paved, 3, 0, 1, 1)
        self.routing_avoid_tracks = QtWidgets.QCheckBox(self.routing_avoid_group)
        self.routing_avoid_tracks.setObjectName("routing_avoid_tracks")
        self.gridLayout_9.addWidget(self.routing_avoid_tracks, 2, 1, 1, 1)
        self.routing_avoid_unpaved = QtWidgets.QCheckBox(self.routing_avoid_group)
        self.routing_avoid_unpaved.setObjectName("routing_avoid_unpaved")
        self.gridLayout_9.addWidget(self.routing_avoid_unpaved, 3, 1, 1, 1)
        self.verticalLayout.addWidget(self.routing_avoid_group)
        self.buttonBox = QtWidgets.QDialogButtonBox(ORStoolsDialogAdvancedBase)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ORStoolsDialogAdvancedBase)
        self.buttonBox.accepted.connect(ORStoolsDialogAdvancedBase.accept)
        self.buttonBox.rejected.connect(ORStoolsDialogAdvancedBase.reject)
        QtCore.QMetaObject.connectSlotsByName(ORStoolsDialogAdvancedBase)

    def retranslateUi(self, ORStoolsDialogAdvancedBase):
        _translate = QtCore.QCoreApplication.translate
        ORStoolsDialogAdvancedBase.setWindowTitle(_translate("ORStoolsDialogAdvancedBase", "Dialog"))
        self.routing_avoid_group.setTitle(_translate("ORStoolsDialogAdvancedBase", "Avoid features"))
        self.routing_avoid_highways.setText(_translate("ORStoolsDialogAdvancedBase", "highways"))
        self.routing_avoid_toll.setText(_translate("ORStoolsDialogAdvancedBase", "tollways"))
        self.routing_avoid_tunnels.setText(_translate("ORStoolsDialogAdvancedBase", "tunnels"))
        self.routing_avoid_ferries.setText(_translate("ORStoolsDialogAdvancedBase", "ferries"))
        self.routing_avoid_fords.setText(_translate("ORStoolsDialogAdvancedBase", "fords"))
        self.routing_avoid_paved.setText(_translate("ORStoolsDialogAdvancedBase", "pavedroads"))
        self.routing_avoid_tracks.setText(_translate("ORStoolsDialogAdvancedBase", "tracks"))
        self.routing_avoid_unpaved.setText(_translate("ORStoolsDialogAdvancedBase", "unpavedroads"))


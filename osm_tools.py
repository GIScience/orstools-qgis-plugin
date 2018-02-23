# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OSMtools
                                 A QGIS plugin
 falk
                              -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Nils Nolde
        email                : nils.nolde@gmail.com
 ***************************************************************************/
 
 This plugin provides access to the various APIs from OpenRouteService 
 (http://openrouteservice.readthedocs.io/en/1.0/api.html), developed and 
 maintained by GIScience team at University of Heidelberg, Germany. By using 
 this plugin you agree to the ORS terms of service
 (http://openrouteservice.readthedocs.io/en/1.0/tos.html#terms-of-service).
 
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os.path

from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication
from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QApplication

from OSMtools.dialog import OSMtoolsDialog
from . import isochrones, client, directions, exceptions

import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level = logging.INFO)

class OSMtools():
    """QGIS Plugin Implementation."""
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInt
    self.dlg.close()
#            self.unload()erface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'OSMtools_{}.qm'.format(locale))

        if os.path.exists(locale_path):
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if PYQT_VERSION_STR > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        self.toolbar = self.iface.addToolBar(u'OSMtools')
        self.toolbar.setObjectName(u'OSMtools')
        
        #custom __init__ declarations
        self.dlg = OSMtoolsDialog(self.iface)
        
        self.canvas = self.iface.mapCanvas()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
                
        
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return QCoreApplication.translate('OSMtools', message)

    
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = os.path.join(os.path.dirname(__file__),'icon.png')
        self.action = QAction(QIcon(icon_path),
                            self.tr(u'OSM Tools'), # tr text
                            self.iface.mainWindow() # parent
                            )
        self.iface.addPluginToMenu(u'&OSM Tools',
                                    self.action)
        self.iface.addToolBarIcon(self.action)
        self.action.triggered.connect(self.run)
        
    def unload(self):        
        QApplication.restoreOverrideCursor()
        self.iface.removePluginWebMenu(u"&OSM Tools", self.action)
        self.iface.removeToolBarIcon(self.action)
        del self.toolbar
        
        
    def run(self):
        """Run method that performs all the real work"""
        
        self.dlg.show()
        
        self.dlg._layerTreeChanged()
        # show the dialog
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            try:
                clt = client.Client(self.iface)
                if self.dlg.tabWidget.currentIndex() == 1:
                    iso = isochrones.isochrones(self.dlg, clt, self.iface)
                    iso.isochrones_calc()
                if self.dlg.tabWidget.currentIndex() == 0:
                    route = directions.directions(self.dlg, clt, self.iface)
                    route.directions_calc()
            except exceptions.Timeout:
                self.iface.messageBar().pushCritical('Time out',
                                                     'The connection exceeded the '
                                                     'timeout limit of 60 seconds')
            
            except (exceptions._OverQueryLimit,
                    exceptions.ApiError,
                    exceptions.TransportError,
                    exceptions._OverQueryLimit) as e:
                self.iface.messageBar().pushCritical("{}: ".format(type(e)),
                                                      "{}".format(str(e)))
            
            except Exception:
                raise
            finally:
                self.dlg.close()
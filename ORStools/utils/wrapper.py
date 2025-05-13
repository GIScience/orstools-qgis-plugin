# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
                              -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2025 by HeiGIT gGmbH
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

from qgis.PyQt.QtCore import QMetaType, QVariant
from qgis.core import QgsField, Qgis


def create_qgs_field(
    name: str, type_enum, length: int = 0, precision: int = 0, comment: str = "", subtype_enum=None
) -> QgsField:
    """
    Creates a QgsField instance compatible with the current QGIS version.

    Parameters:
        name (str): The name of the field.
        type_enum: The field type, either QMetaType.Type or QVariant.Type.
        length (int): The length of the field.
        precision (int): The precision of the field.
        comment (str): A comment for the field.
        subtype_enum: The subtype of the field, either QMetaType.Type or QVariant.Type.

    Returns:
        QgsField: An instance of QgsField configured appropriately.
    """
    if Qgis.versionInt() >= 33800:  # QGIS 3.38 or newer
        # Ensure type_enum is of type QMetaType.Type
        if isinstance(type_enum, QVariant):
            type_enum = QMetaType.Type(type_enum)
        if subtype_enum and isinstance(subtype_enum, QVariant):
            subtype_enum = QMetaType.Type(subtype_enum)
        return QgsField(
            name,
            type_enum,
            "",
            length,
            precision,
            comment,
            subtype_enum or QMetaType.Type.UnknownType,
        )
    else:
        # Ensure type_enum is of type QVariant.Type
        if isinstance(type_enum, QMetaType.Type):
            type_enum = QVariant.Type(type_enum)
        if subtype_enum and isinstance(subtype_enum, QMetaType.Type):
            subtype_enum = QVariant.Type(subtype_enum)
        return QgsField(
            name, type_enum, "", length, precision, comment, subtype_enum or QVariant.Invalid
        )

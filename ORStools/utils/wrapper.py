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
        author:              : Till Frankenbach
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

from typing import Union, Optional

from qgis.PyQt.QtCore import QMetaType, QVariant
from qgis.core import QgsField, Qgis


def create_field_qgis_3_38_plus(
    name: str,
    type_enum: Union[QMetaType.Type, QVariant],
    length: int,
    precision: int,
    comment: str,
    subtype_enum: Optional[Union[QMetaType.Type, QVariant]] = None,
) -> QgsField:
    """Create a QgsField for QGIS ≥ 3.38 using QMetaType.Type enums."""
    # Normalize QVariant → QMetaType.Type
    if isinstance(type_enum, QVariant):
        type_enum = QMetaType.Type(type_enum)
    if subtype_enum and isinstance(subtype_enum, QVariant):
        subtype_enum = QMetaType.Type(subtype_enum)
    return QgsField(
        name,
        type_enum,
        "",  # default type editor
        length,
        precision,
        comment,
        subtype_enum or QMetaType.Type.UnknownType,
    )


def create_field_legacy_qgis(
    name: str,
    type_enum: Union[QMetaType.Type, QVariant],
    length: int,
    precision: int,
    comment: str,
    subtype_enum: Optional[Union[QMetaType.Type, QVariant]] = None,
) -> QgsField:
    """Create a QgsField for QGIS < 3.38 using QVariant.Type enums."""
    # Normalize QMetaType.Type → QVariant.Type
    if isinstance(type_enum, QMetaType.Type):
        type_enum = QVariant.Type(type_enum)
    if subtype_enum and isinstance(subtype_enum, QMetaType.Type):
        subtype_enum = QVariant.Type(subtype_enum)
    return QgsField(
        name,
        type_enum,
        "",  # default type editor
        length,
        precision,
        comment,
        subtype_enum or QVariant.Invalid,
    )


def create_qgs_field(
    name: str, type_enum, length: int = 0, precision: int = 0, comment: str = "", subtype_enum=None
) -> QgsField:
    """
    Factory that picks the correct QgsField constructor
    based on the QGIS version.
    """
    if Qgis.versionInt() >= 33800:  # QGIS 3.38 or newer
        return create_field_qgis_3_38_plus(
            name, type_enum, length, precision, comment, subtype_enum
        )
    else:
        return create_field_legacy_qgis(name, type_enum, length, precision, comment, subtype_enum)

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

from typing import Optional, Any

from qgis.PyQt.QtCore import QMetaType, QVariant
from qgis.core import QgsField


def normalize_field_type(type_enum: Optional[Any]) -> Any:
    """
    Normalize field type enum based on Qt version.

    - Qt5: Uses QVariant.Type enums (has QVariant.Type attribute)
    - Qt6: Uses QMetaType.Type enums (no QVariant.Type attribute)
    """
    if type_enum is None:
        return _get_invalid_type()

    if hasattr(QVariant, "Type"):  # Qt5
        return QVariant.Type(type_enum) if isinstance(type_enum, int) else type_enum
    else:  # Qt6
        return QMetaType.Type(type_enum) if isinstance(type_enum, int) else type_enum


def _get_invalid_type() -> Any:
    """Get the appropriate invalid type enum based on Qt version."""
    if hasattr(QVariant, "Type"):  # Qt5
        return QVariant.Invalid  # or QVariant.Type(0) - they're equivalent
    else:  # Qt6
        return QMetaType.Type(0)


def create_qgs_field(
    name: str,
    type_enum: Any,
    length: int = 0,
    precision: int = 0,
    comment: str = "",
    subtype_enum: Optional[Any] = None,
) -> QgsField:
    """
    Factory that creates a QgsField with proper type handling
    based on the Qt version.

    - Qt5: Uses QVariant.Type enums and QVariant.Invalid for subtypes
    - Qt6: Uses QMetaType.Type enums
    """
    normalized_type = normalize_field_type(type_enum)
    normalized_subtype = normalize_field_type(subtype_enum)  # Use same function

    return QgsField(
        name,
        normalized_type,
        "",  # type name (empty string for default)
        length,
        precision,
        comment,
        normalized_subtype,
    )

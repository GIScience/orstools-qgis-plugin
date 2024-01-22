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
import json
import os

from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
import tempfile

from ORStools.common import client, directions_core
from ORStools.gui import directions_gui
from ORStools.utils import configmanager, logger, exceptions

from shapely import LineString, Point
import matplotlib.pyplot as plt


class Elevation:
    def __init__(self, dlg):
        self.abs_distances = None
        self.total_dist = None
        self.dlg = dlg
        self.pixmap = None
        self.interval = 100
        self.route = None

        self.base()
        self.make_image()

    def base(self):
        basepath = os.path.dirname(__file__)

        # add ors svg path
        my_new_path = os.path.join(basepath, "img/svg")
        svg_paths = QSettings().value("svg/searchPathsForSVG")
        if my_new_path not in svg_paths:
            svg_paths.append(my_new_path)
            QSettings().setValue("svg/searchPathsForSVG", svg_paths)

        provider_id = self.dlg.provider_combo.currentIndex()
        provider = configmanager.read_config()["providers"][provider_id]

        # if there are not enough coordinates, do nothing
        if self.dlg.routing_fromline_list.count() in [0, 1]:
            return

        # if no API key is present, when ORS is selected, throw an error message
        if not provider["key"] and provider["base_url"].startswith(
            "https://api.openrouteservice.org"
        ):
            QMessageBox.critical(
                self.dlg,
                "Missing API key",
                """
                Did you forget to set an <b>API key</b> for openrouteservice?<br><br>

                If you don't have an API key, please visit https://openrouteservice.org/sign-up to get one. <br><br> 
                Then enter the API key for openrouteservice provider in Web ► ORS Tools ► Provider Settings or the 
                settings symbol in the main ORS Tools GUI, next to the provider dropdown.""",
            )
            return

        agent = "QGIS_ORStoolsDialog"
        clnt = client.Client(provider, agent)
        clnt_msg = ""

        directions = directions_gui.Directions(self.dlg)
        params = None
        try:
            params = directions.get_parameters()
            if self.dlg.optimization_group.isChecked():
                QMessageBox.warning(
                    self.dlg,
                    "Not available:",
                    "Elevation profile not available for optimization",
                )
                return
            else:
                params["coordinates"] = directions.get_request_line_feature()
                profile = self.dlg.routing_travel_combo.currentText()
                # abort on empty avoid polygons layer
                if (
                    "options" in params
                    and "avoid_polygons" in params["options"]
                    and params["options"]["avoid_polygons"] == {}
                ):
                    QMessageBox.warning(
                        self.dlg,
                        "Empty layer",
                        """
The specified avoid polygon(s) layer does not contain any features.
Please add polygons to the layer or uncheck avoid polygons.
                        """,
                    )
                    msg = "The request has been aborted!"
                    logger.log(msg, 0)
                    self.dlg.debug_text.setText(msg)
                    return
                response = clnt.request(
                    "/v2/directions/" + profile + "/geojson", {}, post_json=params
                )
                feat = directions_core.get_output_feature_directions(
                    response, profile, params["preference"], directions.options
                )

            geom = feat.geometry()
            points = geom.asPolyline()
            line = LineString(points)

            self.total_dist = response["features"][0]["properties"]["summary"]["distance"]
            self.route = line

            total_length = self.route.length
            coordinates = list(self.route.coords)
            rel_distances = [
                Point(coord1).distance(Point(coord2)) / total_length
                for coord1, coord2 in zip(coordinates[:-1], coordinates[1:])
            ]

            # Initialize an empty list to store the cumulative sums
            cumulative_sums = []

            # Variable to keep track of the running sum
            running_sum = 0
            original_list = [i * self.total_dist for i in rel_distances]

            # Iterate through the original list
            for num in original_list:
                # Add the current number to the running sum
                running_sum += num
                # Append the running sum to the cumulative_sums list
                cumulative_sums.append(running_sum)

            abs_distances = [0] + cumulative_sums
            self.abs_distances = [i / 1000 for i in abs_distances]

            self.elevations = directions_core.get_output_coordinate_elevations(response)

            # Update quota; handled in client module after successful request
            # if provider.get('ENV_VARS'):
            #     self.dlg.quota_text.setText(self.get_quota(provider) + ' calls')
        except exceptions.Timeout:
            msg = "The connection has timed out!"
            logger.log(msg, 2)
            self.dlg.debug_text.setText(msg)
            return

        except (exceptions.ApiError, exceptions.InvalidKey, exceptions.GenericServerError) as e:
            logger.log(f"{e.__class__.__name__}: {str(e)}", 2)
            clnt_msg += f"<b>{e.__class__.__name__}</b>: ({str(e)})<br>"
            raise

        except Exception as e:
            logger.log(f"{e.__class__.__name__}: {str(e)}", 2)
            clnt_msg += f"<b>{e.__class__.__name__}</b>: {str(e)}<br>"
            raise

        finally:
            # Set URL in debug window
            if params:
                clnt_msg += f'<a href="{clnt.url}">{clnt.url}</a><br>Parameters:<br>{json.dumps(params, indent=2)}'
            self.dlg.debug_text.setHtml(clnt_msg)

    def make_image(self):
        """
        Make image from get_profile() output.
        """
        if self.abs_distances and self.elevations:
            fig, ax = plt.subplots()
            ax.plot(self.abs_distances, self.elevations, linestyle="-")
            ax.fill_between(self.abs_distances, self.elevations, 0, alpha=0.1)
            ax.grid()
            ax.set_xlabel("Distance [km]")
            ax.set_ylabel("Elevation [m]")

            temp_dir = tempfile.mkdtemp(prefix="ORS_qgis_plugin_")
            temp_image_path = os.path.join(temp_dir, "elevation_profile.jpg")
            fig.savefig(temp_image_path, dpi=100)

            label = self.dlg.label_elevation_profile
            pixmap = QPixmap(temp_image_path)
            label.setPixmap(pixmap)
            # label.setFixedSize(300, 200)
            label.setScaledContents(True)

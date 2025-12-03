import json
from datetime import datetime

from qgis.core import (
    QgsVectorLayer,
)

from qgis.PyQt.QtWidgets import QMessageBox

from ORStools.common import (
    client,
    directions_core,
)
from ORStools.gui import directions_gui
from ORStools.utils import exceptions, logger, configmanager

from qgis.PyQt.QtCore import QCoreApplication


def route_as_layer(dlg):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    layer_name = f"Route_ORS_{timestamp}"
    layer_out = QgsVectorLayer("LineString?crs=EPSG:4326", layer_name, "memory")
    layer_out.dataProvider().addAttributes(directions_core.get_fields())
    layer_out.updateFields()

    provider_id = dlg.provider_combo.currentIndex()
    provider = configmanager.read_config()["providers"][provider_id]

    # if no API key is present, when ORS is selected, throw an error message
    if not provider["key"] and provider["base_url"].startswith("https://api.openrouteservice.org"):
        QMessageBox.critical(
            dlg,
            tr("Missing API key"),
            tr("""
            Did you forget to set an <b>API key</b> for openrouteservice?<br><br>

            If you don't have an API key, please visit https://openrouteservice.org/sign-up to get one. <br><br> 
            Then enter the API key for openrouteservice provider in Web ► ORS Tools ► Provider Settings or the 
            settings symbol in the main ORS Tools GUI, next to the provider dropdown."""),
        )
        return False

    agent = "QGIS_ORStoolsDialog"
    clnt = client.Client(provider, agent)
    clnt_msg = ""

    directions = directions_gui.Directions(dlg)
    params = None
    try:
        params = directions.get_parameters()
        if dlg.optimization_group.isChecked():
            if len(params["jobs"]) <= 1:  # Start/end locations don't count as job
                QMessageBox.critical(
                    dlg,
                    tr("Wrong number of waypoints"),
                    tr("""At least 3 or 4 waypoints are needed to perform routing optimization. 

Remember, the first and last location are not part of the optimization.
                    """),
                )
                return
            response = clnt.fetch_with_retry("/optimization", {}, post_json=params)
            feat = directions_core.get_output_features_optimization(
                response, params["vehicles"][0]["profile"]
            )
        else:
            params["coordinates"] = directions.get_request_line_feature()
            profile = dlg.routing_travel_combo.currentText()
            # abort on empty avoid polygons layer
            if (
                "options" in params
                and "avoid_polygons" in params["options"]
                and params["options"]["avoid_polygons"] == {}
            ):
                QMessageBox.warning(
                    dlg,
                    tr("Empty layer"),
                    tr("""
The specified avoid polygon(s) layer does not contain any features.
Please add polygons to the layer or uncheck avoid polygons.
                    """),
                )
                msg = "The request has been aborted!"
                logger.log(msg, 0)
                dlg.debug_text.setText(msg)
                return
            response = clnt.fetch_with_retry(
                "/v2/directions/" + profile + "/geojson", {}, post_json=params
            )
            feat = directions_core.get_output_feature_directions(
                response, profile, params["preference"], directions.options
            )

        layer_out.dataProvider().addFeature(feat)

        layer_out.updateExtents()

        return layer_out

        # Update quota; handled in client module after successful request
        # if provider.get('ENV_VARS'):
        #     self.dlg.quota_text.setText(self.get_quota(provider) + ' calls')
    except exceptions.Timeout:
        msg = "The connection has timed out!"
        logger.log(msg, 2)
        dlg.debug_text.setText(msg)
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
        dlg.debug_text.setHtml(clnt_msg)


def tr(string: str) -> str:
    return QCoreApplication.translate("ORStoolsDialogMain", string)

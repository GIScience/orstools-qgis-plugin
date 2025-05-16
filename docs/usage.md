# General Usage

## Main Plugin

The standard GUI is launched either from the `Web` toolbar or the `Web` menu:

![ORS Tools GUI](https://github.com/GIScience/orstools-qgis-plugin/blob/main/docs/wiki/img/wiki_orstools_01.png)

You'll find a shortcut to the configuration settings and the wiki here. Also, it will show you your available requests for the current period of time (usually one day) as soon as you made the first request in the current QGIS session.

### Parameters

You can use all available profiles from openrouteservice, including **wheelchair** (only available for Europe), for the `fastest` or `shortest` route. In the `Advanced` dialog you can set avoidables to be considered during route finding.

### Input features

As input, either map start and locations directly from the map canvas by clicking the `green plus button` buttons and choosing a location in the map canvas, or use Point layers to route from/to. Batch operations involving whole layers are better performed using the [Processing tool](#routing-processing). The `Unique ID` fields let you specify the ID's being used to identify the output features, enabling joining of output and input layers.

If you're using a layer for start and end locations, you can choose the mode. `Row by row` will route from each row in the start layer to the corresponding row in the destination layer. `All-by-All` will route each feature of the start layer to each feature of the destination layer, basically performing a matrix calculation. Use this option with care. In case you don't need the output geometries, but you're only interested in a table of the distance and/or duration, consider using the [Matrix API](#matrix-processing).

### Output features

For each operation a `LineString` layer will be output, which contains the following properties:

- `DIST_KM`: the calculated route distance in kilometers
- `DURATION_H`: the calculated route duration in hours
- `PROFILE`: the transportation mode being used
- `AVOID_TYPE`: a pipe (|) separated list avoidables
- `FROM_ID`: the values of the ID field used in the `From` layer
- `TO_ID`: the values of the ID field used in the `End` layer

## Processing Algorithms


## Directions
- [Directions from 1 Point-Layer](https://github.com/Merydian/orstools-wiki-test/wiki/directions_from_points_1_layer)
<img src="/img/directions_from_points_1_layer_preview.png" alt="Toolbox">
<img src="/img/directions_from_points_1_layer_toolbox.png" alt="Toolbox">

- [Directions from 1 Polyline-Layer](https://github.com/Merydian/orstools-wiki-test/wiki/directions_from_polylines_layer)
<img src="/img/directions_from_polylines_layer_preview.png" alt="Toolbox">
<img src="/img/directions_from_polylines_layer_toolbox.png" alt="Toolbox">

- [Directions from 2 Point-Layers](https://github.com/Merydian/orstools-wiki-test/wiki/directions_from_points_2_layers)
<img src="/img/directions_from_points_2_layers_preview.png" alt="Toolbox">
<img src="/img/directions_from_points_2_layers_toolbox.png" alt="Toolbox">

## Isochrones
- [Isochrones from Point](https://github.com/Merydian/orstools-wiki-test/wiki/isochrones_from_point)
<img src="/img/isochrones_from_point_preview.png" alt="Toolbox">
<img src="/img/isochrones_from_point_toolbox.png" alt="Toolbox">

- [Isochrones from Point-Layer](https://github.com/Merydian/orstools-wiki-test/wiki/isochrones_from_layer)
<img src="/img/isochrones_from_layer_preview.png" alt="Toolbox">
<img src="/img/isochrones_from_layer_toolbox.png" alt="Toolbox">

## Matrix
- [Matrix from Layers](https://github.com/Merydian/orstools-wiki-test/wiki/matrix_from_layers)
<img src="/img/matrix_from_layers_preview.png" alt="Toolbox">
<img src="/img/matrix_from_layers_toolbox.png" alt="Toolbox">

# Matrix from Layers
This algorithm returns a duration and distance matrix for multiple source and destination points.

<img src="/wiki/img/matrix_from_layers_toolbox.png" alt="Toolbox">

## Parameters

### Provider
First, you'll have to [sign-up](https://openrouteservice.org/sign-up) and register your API key in your [dashboard](https://openrouteservice.org/dev/#/home).

In the configuration window (`Web` > `ORS Tools` > `Configuration`) you have set up the API key, which will be saved locally in a configuration file and will automatically be used across all tools. Here you can also set the base URL in case you're using a self-hosted ORS version and the requests per minute you're allocated (usually set to 40).

![ORS Tools configuration](/wiki/img/wiki_orstools_config.png)


<details>
<summary>Get your API Key from Openrouteservice.org by signing up and going to your dashboard.</summary>
<br>

[![How To: Api Key](http://img.youtube.com/vi/Rsxl_0IUSFM/0.jpg)](http://www.youtube.com/watch?v=Rsxl_0IUSFM?start=145 "ORSTools 1.2 for Routing, Isochrones and Travel Time in QGIS")

</details>

### Travel Mode
Select mode of travel.

<details>
<summary>Options</summary>
<br>
<ul>
 <li>driving-car</li>
 <li>driving-hgv</li>
 <li>cycling-regular</li>
 <li>cycling-road</li>
 <li>cycling-mountain</li>
 <li>cycling-electric</li>
 <li>foot-walking</li>
 <li>foot-hiking</li>
 <li>wheelchair</li>
</ul>
</details>

A detailed description of this can be viewed [here](https://giscience.github.io/openrouteservice/technical-details/travel-speeds/#travel-time-calculation)

### Input Start Point Layer
Point layer which serves as the starting points of the matrix which will be generated. Only Point layers are allowed, not MultiPoint.

### Start ID Field
Select a field that will be appended to the output matrix layer, to later be able to [join](https://docs.qgis.org/3.34/en/docs/user_manual/working_with_vector/joins_relations.html) it with the input start points of the matrix.

### Input End Point Layer
Point layer which serves as the ending points of the matrix which will be generated. Only Point layers are allowed, not MultiPoint.

### Start ID Field
Select a field that will be appended to the output matrix layer, to later be able to [join](https://docs.qgis.org/3.34/en/docs/user_manual/working_with_vector/joins_relations.html) it with the input end points of the matrix.

### Matrix(Output)
Specify a path, where the matrix layer will be saved. Leaving this empty will result in a temporary layer. 

## Advanced Parameters
These are optional parameters you can use to avoid certain areas.

### Features to Avoid
You can make your isochrones avoid particular features. Specify them here.

<details>
<summary>Options</summary>
<br>
<ul>
  <li>Highways</li>
  <li>Tollways</li>
  <li>Ferries</li>
  <li>Fords</li>
  <li>Steps</li>
</ul>
</details>
<br>

### Types of borders to avoid
Specify which type of border crossing to avoid.

<details>
<summary>Options</summary>
<br>
<ul>
  <li>all</li>
  <li>controlled</li>
</ul>
</details>
<br>

### Comma-separated list of ids of countries to avoid
List of countries to exclude from isochrones with driving-* profiles. Can be used together with 'avoid_borders': 'controlled'. [ 11, 193 ] would exclude Austria and Switzerland. List of countries and application examples can be found [here](https://giscience.github.io/openrouteservice/technical-details/country-list). Also, ISO standard country codes cna be used in place of the numerical ids, for example, DE or DEU for Germany.

### Polygons to avoid
You can make your isochrones avoid particular polygons from your layers. Specify them here.
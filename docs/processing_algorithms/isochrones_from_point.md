# Isochrones from Point-Layer
This algorithm returns service/reachability areas for multiple locations and time/distance ranges.

<img src="/wiki/img/isochrones_from_point_toolbox.png" alt="Toolbox">

## Parameters

### Provider
Select the [openrouteservice provider](../general/provider_settings.md) you want to use.

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

A detailed description of this can be viewed [here](https://giscience.github.io/openrouteservice/technical-details/travel-speeds/#travel-time-calculation)s

### Input Point from map canvas
Click the `...` button and choose a point on the map canvas that will serve as the isochrone center. 

### Dimension
Select wether ranges should be calculated based on time or distance.

<details>
<summary>Options</summary>
<br>
<ul>
 <li>time</li>
 <li>distance</li>
</ul>
</details>
<br>

### Comma-separated ranges
Specify the ranges that should be calculated. Based on your selection in `Dimension` this will be either in minutes or meters as units.

### Location type
Specify wether the points should be treated as a starting point or a destination. Start treats the location(s) as starting point, destination as goal.

<details>
<summary>Options</summary>
<br>
<ul>
 <li>start</li>
 <li>destination</li>
</ul>
</details>
<br>

### Isochrones(Output)
Specify a path, where the layer will be saved. Leaving this empty will result in a temporary layer. 

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

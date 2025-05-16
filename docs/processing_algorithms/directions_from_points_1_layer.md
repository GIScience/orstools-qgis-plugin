# Directions from 1 Point-Layer
This algorithm calculates optimal routes for (Multi)Point layers. 

<img src="/img/directions_from_points_1_layer_toolbox.png" alt="Toolbox">

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
<br>

A detailed description of this can be viewed [here](https://giscience.github.io/openrouteservice/technical-details/travel-speeds/#travel-time-calculation)

### Input Layer
Choose a Point or MultiPoint layer as Input.

### Layer ID Field
These Values will transfer to the output layer and can be used to join layers or group features afterwards.

### Sort Points
Before running the algorithm points are sorted by the values of this field (Be aware of the field type! Text fields will be sorted as 1,13,2,D,a,x)

### Travel preference
Dictates the cost. For longer routes don't use Shortest Path.

<details>
<summary>Options</summary>
<br>
<ul>
 <li>fastest</li>
 <li>shortest</li>
 <li>recommended</li>
</ul>
</details>
<br>

[comment]: <> (Gibt's hiervon irgenwo Erklärungen, die man beifügen oder verlinken könnte?)

### Traveling Salesman
You can optionally perform a [Traveling Salesman Optimization](https://en.wikipedia.org/Travelling_salesman_problem) on the waypoints of each (Multi)Point feature. Enabling Traveling Salesman will erase all other advanced configuration and assume the preference to be fastest.

<details>
<summary>Examples</summary>
<br>
<h4>Traveling Salesman Problem: Round trip</h4>
<img src="/img/tsp_round_trip.png" alt="Traveling Salesman Problem: Round trip">
<h4>Traveling Salesman Problem: fix start point</h4>
<img src="/img/tsp_fix_start_point.png" alt="Traveling Salesman Problem: fix start point">
<h4>Traveling Salesman Problem: fix end point</h4>
<img src="/img/tsp_fix_end_point.png" alt="Traveling Salesman Problem: fix end point">
<h4>Traveling Salesman Problem: fix start and end points</h4>
<img src="/img/tsp_fix_start_and_end_points.png" alt="Traveling Salesman Problem: fix start and end points">
</details>

### Directions(Output)
Specify a path, where the layer will be saved. Leaving this empty will result in a temporary layer. 

## Advanced Parameters
These are optional parameters you can use to avoid certain areas.

### Features to Avoid
You can make your route avoid particular features. Specify them here.

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
List of countries to exclude from route with driving-* profiles. Can be used together with 'avoid_borders': 'controlled'. [ 11, 193 ] would exclude Austria and Switzerland. List of countries and application examples can be found [here](https://giscience.github.io/openrouteservice/technical-details/country-list). Also, ISO standard country codes cna be used in place of the numerical ids, for example, DE or DEU for Germany.

### Polygons to avoid
You can make your route avoid particular polygons from your layers. Specify them here.

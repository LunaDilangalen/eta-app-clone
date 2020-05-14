import json
from haversine import haversine, Unit

with open("routes/ikot_route.json", "r") as readFile:
    routeData = json.load(readFile)

coordinates = routeData['features'][0]['geometry']['coordinates']
numberOfCoordinates = len(coordinates)

# in m/s
initial_speed = 8.333
# in seconds
initial_time_traveled = 22

route = []

for i in range(0, numberOfCoordinates):
    segment = {}
    geojson_line = {}
    start_coordinates = coordinates[i]

    if i < numberOfCoordinates-1:
        end_coordinates = coordinates[i+1]
    elif i == numberOfCoordinates-1:
        end_coordinates = coordinates[0]

    h_a = start_coordinates.copy()
    h_b = end_coordinates.copy()
    h_a.reverse()
    h_b.reverse()
    distance = haversine(h_a, h_b, unit=Unit.METERS)
    geojson_line.update([("type", "LineString"), ("coordinates", [start_coordinates, end_coordinates])])
    midpoint = {
    "type": "Point",
    "coordinates": [(start_coordinates[0]+end_coordinates[0])/2.0, (start_coordinates[1]+end_coordinates[1])/2.0]
    }
    segment.update([("segment_id", i), ("segment", geojson_line), ("midpoint", midpoint), ("length", distance), ("speed", initial_speed), ("travel_time", initial_time_traveled)])
    route.append(segment)
    print(start_coordinates, '->', end_coordinates, ' : ', distance)


print('number of segments: ', len(route))
routeDump = json.dumps(route)
# print(test)
with open("ikot_route_test.geojson", "w") as output:
     json.dump(route, output)

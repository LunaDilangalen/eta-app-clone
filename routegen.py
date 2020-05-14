import json
from haversine import haversine, Unit

with open("routes/ikot_route.json", "r") as readFile:
    routeData = json.load(readFile)

# print('~', len(route_data['features'][0]['geometry']['coordinates'])/2, 'segments')
# for i in range(len(route_data['features'][0]['geometry']['coordinates'])):
#     print(route_data['features'][0]['geometry']['coordinates'][i])

coordinates = routeData['features'][0]['geometry']['coordinates']
numberOfCoordinates = len(coordinates)

route = []
for i in range(0, numberOfCoordinates):
    if i < numberOfCoordinates-1:
        # print(coordinates[i], coordinates[i+1])
        segment = {}
        geojson_line = {}
        start_coordinates = [coordinates[i][1], coordinates[i][0]]
        end_coordinates = [coordinates[i+1][1], coordinates[i+1][0]]
        midpoint = ((start_coordinates[0]+end_coordinates[0])/2.0, (start_coordinates[1]+end_coordinates[1])/2.0)
        distance = haversine(start_coordinates, end_coordinates, unit=Unit.METERS)
        avgspeed = 8.333
        # new_segment = segment(start = start_coordinates, end = end_coordinates, length = distance, avgspeed = avgspeed)
        geojson_line.update([("type", "LineString"), ("coordinates", [start_coordinates, end_coordinates])])
        segment.update([("segment_id", i), ("segment", geojson_line), ("midpoint", midpoint), ("length", distance), ("speed", avgspeed)])
        route.append(segment)
        print(start_coordinates, '->', end_coordinates, ' : ', distance)
    elif i == numberOfCoordinates-1:
        segment = {}
        geojson_line = {}
        start_coordinates = [coordinates[i][1], coordinates[i][0]]
        end_coordinates = [coordinates[0][1], coordinates[0][0]]
        midpoint = ((start_coordinates[0]+end_coordinates[0])/2.0, (start_coordinates[1]+end_coordinates[1])/2.0)
        distance = haversine(start_coordinates, end_coordinates, unit=Unit.METERS)
        avgspeed = 8.333
        # new_segment = segment(start = start_coordinates, end = end_coordinates, length = distance, avgspeed = avgspeed)
        geojson_line.update([("type", "LineString"), ("coordinates", [start_coordinates, end_coordinates])])
        segment.update([("segment_id", i), ("segment", geojson_line), ("midpoint", midpoint), ("length", distance), ("speed", avgspeed)])
        route.append(segment)
        print(start_coordinates, '->', end_coordinates, ' : ', distance)


print('number of segments: ', len(route))
routeDump = json.dumps(route)
# print(test)
with open("ikot_route_test.json", "w") as output:
     json.dump(route, output)

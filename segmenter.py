import datetime, time, sqlite3, pytz, random, os, json
from haversine import haversine, Unit
from segment import segment

d = datetime.datetime.strptime("2019-02-24T05:00:01.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")

lowbound = 0.1
highbound = 1.0

raw_route_data = open("datasets/drive.csv", "r") #replace this with whatever .csv file you want to parse

lines_from_source = raw_route_data.readlines()
still_at_header  = True

##this section parses the csv
parsed = []
for line in lines_from_source:
    # counter+=1
    if still_at_header:
        still_at_header = False

    else:
        j = line.split(",")
        to_append = (float(j[0]), float(j[1]), float(j[2]))
        #print(to_append)
        parsed.append(to_append)

bounds_satisfied = False
maxlines = 0
startpoint = 0

# selects coordinates that are within the bounds (lowbound, highbound)
while not bounds_satisfied:
    for i in range(startpoint, len(parsed)):
        if(i < len(parsed) - 1):
            current_coordinates = (parsed[i][1], parsed[i][2])
            next_coordinates = (parsed[i+1][1], parsed[i+1][2])
            distance = haversine(current_coordinates, next_coordinates)

            if distance > 0:
                startpoint = i
                # print("[%f, %f] -> [%f, %f] = %f" %(parsed[i][1], parsed[i][2], parsed[i+1][1], parsed[i+1][2], distance))
                if distance > highbound: #if distance too long, insert a new point
                    #print("ins"+str(i))
                    inserted_time = (parsed[i][0]+parsed[i+1][0])/2.0
                    inserted_lat = (parsed[i][1]+parsed[i+1][1])/2.0
                    inserted_lon = (parsed[i][2]+parsed[i+1][2])/2.0
                    tuple_to_insert = (inserted_time,inserted_lat,inserted_lon)
                    parsed.insert(i,tuple_to_insert)
                    break
                elif distance < lowbound: #distance too short, delete a point
                    #print("del"+str(i))
                    del parsed[i + 1]
                    break
            elif distance <= 0:
                del parsed[i+1]
                break

        if i == len(parsed)-1:
            bounds_satisfied = True

# add the first coordinates to the end of the list to ensure that it is a cycle
parsed.append(parsed[0])

route = []
for i in range(len(parsed)):
    if(i < len(parsed) - 1):
        segment = {}
        geojson_line = {}
        start_coordinates = [parsed[i][1], parsed[i][2]]    # (longitude, latitude) conforms to geoJSON format
        end_coordinates = [parsed[i+1][1], parsed[i+1][2]]  # (longitude, latitude) conforms to geoJSON format
        midpoint = ((start_coordinates[0]+end_coordinates[0])/2.0, (start_coordinates[1]+end_coordinates[1])/2.0)
        distance = haversine(start_coordinates, end_coordinates)
        avgspeed = 0
        print("[%f, %f] -> [%f, %f] = %f" %(parsed[i][1], parsed[i][2], parsed[i+1][1], parsed[i+1][2], distance))
        # new_segment = segment(start = start_coordinates, end = end_coordinates, length = distance, avgspeed = avgspeed)
        geojson_line.update([("type", "LineString"), ("coordinates", [start_coordinates, end_coordinates])])
        segment.update([("segment_id", i), ("segment", geojson_line), ("midpoint", midpoint), ("length", distance), ("speed", avgspeed)])
        route.append(segment)
        # segments.append(new_segment_for_csv)


# output = open("segmented_route.csv","w")
# for line in segments:
#     # output.write(str(line).strip("(").strip(")")+"\n")
#     output.write(str(line)+"\n")
# output.close()

test = json.dumps(route)
print(test)
with open("route_test.json", "w") as output:
     json.dump(route, output)
# print(len(segments))

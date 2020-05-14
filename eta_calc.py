from threading import Thread
from haversine import haversine
import urllib3
import json
import pandas as pd
import numpy as np
import datetime
import time
import pytz
from math import floor, ceil
from statistics import mean

# Attempt 1: Simply calculating the distance of the moving car to the destination
# Attempt 2:
## Using the segmented 'route', find the segment where the moving car is and where the destination is.
## Calculate the distance of the moving car from the destination 'indirectly' by summing up the distances of the segments in between the moving car and the destination

def calculateDistanceOfSegments(route, start_segment, end_segment):
    total_distance = 0.0
    start = start_segment
    end = end_segment + 1
    # if end > len(route):
    #     end = 0
    while start != end:
        if(start > len(route)-1):     # resets the counter
            start = 0
        # print(route[start]["segment_id"])
        total_distance = total_distance + route[start]["length"]
        start+=1
    return total_distance


# load the segmentroute JSON file
with open("route_test.json", "r") as read_file:
    route_data = json.load(read_file)

test = calculateDistanceOfSegments(route_data, 0, 41)
print(test)



# 'dripping' part
csv_data = open("datasets/drive.csv", "r")
lines = csv_data.readlines()
read  = False
location = []

for k in lines:
    if read == False:
        read = True
    else:
        j = k.split(",")
        unx = (datetime.datetime.fromtimestamp(int(j[0]) // 1000) - datetime.datetime(1970,1,1)).total_seconds()
        to_append = (unx, float(j[1]), float(j[2]), float(j[3])) # time, latitude, longitude, speed
        location.append(to_append)

for k in range(0,len(location)):
    if k < len(location)-1:
        delay = float(location[k+1][0])-float(location[k][0])
        if delay <= 0:
            del location[k+1]

# random destination target
destination = (14.65216416,121.06229386)

# calculate the distance of the destination point to the midpoint of all segments
# 'snap' the point to the segment with the minimum distance wrt to it.
segment_distances = []
for segment in route_data:
    distance = haversine(destination, segment["midpoint"])
    segment_distances.append(distance)

destination_segment = segment_distances.index(min(segment_distances))

car_snapped = False
distance_from_dest = 9999

k = 0

speed = []

while distance_from_dest > 0:
    u = datetime.datetime.utcnow()
    u = u.replace(tzinfo=pytz.utc)
    if location[k][3]!="":
        current_coordinates = (location[k][1], location[k][2])

        # determine which segment is the car nearest to
        segment_distances = []
        for segment in route_data:
            distance = haversine(current_coordinates, segment["midpoint"])*1000
            segment_distances.append(distance)

        car_segment = segment_distances.index(min(segment_distances))
        print('min distance from segment [%d]' %(car_segment) ,min(segment_distances))

        # calculate the total distance from the car's current segment to the destination's segment
        distance_from_dest = calculateDistanceOfSegments(route_data, car_segment, destination_segment)*1000
        # distance_from_dest = haversine(current_coordinates, destination)*1000.0 # this is in KM

        # calculate for the average speed by getting the mean of all the speed a car has sustained so far
        current_speed = location[k][3]
        speed.append(current_speed)
        ave_speed = mean(speed)

        eta = ceil((distance_from_dest/ave_speed)/60.0)
        print(distance_from_dest, " m left", "will arrive in ", eta, " mins")
    if k < len(location)-1:
        delay = float(location[k+1][0])-float(location[k][0])
        # time.sleep(delay/4.0)
    k+=1

print("destination_segment: ", destination_segment)

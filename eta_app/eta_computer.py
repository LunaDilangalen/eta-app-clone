from . import compute_eta
import datetime as dt
from . import helper

# VSDs that are 5 minutes old or more are not considered
DEFAULT_ZOMBIE_TIMEDELTA = dt.timedelta(minutes=5) # refoactor timedelta to config.py

# Returns [(eta, vehicle)]
# order: increasing eta.
# There is a problem. Zombie vehicles are still on MongoDB.
# This assumes vehicles are not in zombie mode
# zombie mode - vehicles who have reported data but never seen again in quite a while
#     (no reported data in the last 5 or more minutes)
#     i.e. vehicle is stalling in segment 0 for 10 minutes because
#          engine failure, waiting for riders.
#     THIS IS HANDLED BY zombie_threshhold_timedelta
# returns [ (Vehicle, Segments, total_travel_time) ]
def generic_eta(app, destination_lon_lat, max_number_of_puvs=3, consider_destination_segment=False, route_direction="increasing", zombie_threshhold_timedelta=DEFAULT_ZOMBIE_TIMEDELTA):
    lon, lat = destination_lon_lat[0], destination_lon_lat[1]
    normal_format_destination = (lat,lon)
    destination_segment_id = compute_eta.locate_segment(coordinates=normal_format_destination)
    destination_segment = app.models.Segment.objects(segment_id=destination_segment_id).first()
    if destination_segment is None:
        raise Exception("identify_puv_nearest_destination: Can't find the dst segment. Is MongoDB empty?")
    else:
        vehicle_segments_total_travel_time_array = get_vehicle_eta_total_travel_time_from_dest_segment(app, destination_segment, max_number_of_puvs, consider_destination_segment, route_direction, zombie_threshhold_timedelta)
        return vehicle_segments_total_travel_time_array


# Go one loop around the route, depending on the route_direction, finding vehicles along the way, adding up the travel_time incurred, and the segments_to_travel.
# <route_direction> = "increasing"/"decreasing"
# "increasing" |--> go backwards by decreasing cursor_segment_id
# "decreasing" |--> go backwards by increasing cursor_segment_id
# returns [ (Vehicle, Segments, total_travel_time) ]
# returns an array and the relevant segments with it.
def get_vehicle_eta_total_travel_time_from_dest_segment(app, destination_segment, max_number_of_puvs, consider_destination_segment, route_direction, zombie_threshhold_timedelta):
    cursor_segment_id = destination_segment.segment_id
    cursor_segment_id = move_segment_backwards(app, cursor_segment_id, route_direction)
    vehicle_segments_total_travel_time_array = []
    vehicles = []
    cumulative_segments_to_cross = []
    cumulative_travel_time = 0

    if consider_destination_segment:
        cumulative_segments_to_cross.append(destination_segment)
        cumulative_travel_time += destination_segment.running_average_travel_time
        sorted_vehicles = sort_vehicles_by_farthest_in_segment(_temp_vehicles, route_direction)

        for v, distance, closeness in sorted_vehicles:
            if zombie_threshhold_timedelta is None:
                vehicle_segments_total_travel_time_array.append( (v,cumulative_segments_to_cross, cumulative_travel_time + (cursor_segment.running_average_travel_time * closeness)) )
            elif (zombie_threshhold_timedelta is not None) and ((v.vehicle_datetime + zombie_threshhold_timedelta) > dt.datetime.now()):
                vehicle_segments_total_travel_time_array.append( (v,cumulative_segments_to_cross, cumulative_travel_time + (cursor_segment.running_average_travel_time * closeness)) )


    while (cursor_segment_id != destination_segment.segment_id) and (len(vehicle_segments_total_travel_time_array) < max_number_of_puvs):
        cursor_segment = app.models.Segment.objects(segment_id=cursor_segment_id).first()

        if cursor_segment is None:
            raise Exception("get_vehicle_eta_total_travel_time_from_dest_segment: While iterating through segments, found a null segment. Is MongoDB empty? Or segments are not numbered consecutively?")
        else:

            _temp_vehicles = cursor_segment.vehicles.copy()
            sorted_vehicles = sort_vehicles_by_farthest_in_segment(_temp_vehicles, route_direction)

            cumulative_segments_to_cross.append(cursor_segment)

            for v, distance, closeness in sorted_vehicles:
                if zombie_threshhold_timedelta is None:
                    vehicle_segments_total_travel_time_array.append( (v,cumulative_segments_to_cross, cumulative_travel_time + (cursor_segment.running_average_travel_time * closeness)) )
                elif (zombie_threshhold_timedelta is not None) and ((v.vehicle_datetime + zombie_threshhold_timedelta) > dt.datetime.now()):
                    vehicle_segments_total_travel_time_array.append( (v,cumulative_segments_to_cross, cumulative_travel_time + (cursor_segment.running_average_travel_time * closeness)) )

            cumulative_travel_time += cursor_segment.running_average_travel_time

            cursor_segment_id = move_segment_backwards(app, cursor_segment_id, route_direction)

    return vehicle_segments_total_travel_time_array[0:max_number_of_puvs]

# Moves the cursor segment id, loop around the route if needed
# Note that it can go from:
#   start -> end
#   OR
#   end -> start
# <route_direction> = "increasing"/"decreasing"
# "increasing" |--> go backwards by decreasing cursor_segment_id
# "decreasing" |--> go backwards by increasing cursor_segment_id
def move_segment_backwards(app, cursor_segment_id, route_direction):
    start_segment_id = 0
    end_segment_id = app.models.Segment.objects.order_by('-segment_id').first().segment_id

    if route_direction == "increasing":
        cursor_segment_id -= 1
        if start_segment_id > cursor_segment_id:
            return end_segment_id
        else:
            return cursor_segment_id
    elif route_direction == "decreasing":
        cursor_segment_id += 1
        if cursor_segment_id > end_segment_id:
            return start_segment_id
        else:
            return cursor_segment_id
    else:
        raise Exception("identify_puv_nearest_destination: <route_direction> can only be 'increasing' or 'decreasing'.")



# If multiple vehicles in the segment (fine-grained algorithm):
# - TWO WAYS TO SOLVE:
#   1.  sort by earliest arriver; VSD pushes the latest to arrive in the segment (last to arrive) (because of push__vehicles)
#   2.  sort by farthest in segment

# 1 - sort by the earliest arriver - lacking timedelta difference, still have same ETA
def sort_vehicles_by_earliest_arriver(vehicles_array):
    return_array = vehicles_array.copy()
    return_array.reverse()
    return return_array

# 2 - sort by farthest in distance
# sort by vehicles closest to the endpoint. Assuming the second coordinate (increasing) in the LineStringField is the endpoint.
# returns [ (vehicle_1, distance_1, closeness_1), ..., (vehicle_n, distance_n, closeness_n) ]
def sort_vehicles_by_farthest_in_segment(vehicles_array, route_direction):
    return_array = []
    for v in vehicles_array:
        endpoint = 0
        if route_direction == "increasing":
            endpoint = v.segment.segment['coordinates'][1]
        else:
            endpoint = v.segment.segment['coordinates'][0]
        distance = helper.get_distance_from_two_geojson_points(endpoint, v.vehicle_location['coordinates'])
        closeness = ((v.segment.length - distance) / v.segment.length)
        # If closeness < 0 || distance > segment_length, debug.
        if closeness < 0:
            print("closeness: {}, segment: {}, vehicle: {}, loc: {}".format(closeness, cursor_segment_id, v.vehicle_id, v.vehicle_location['coordinates']))
        return_array.append((v, distance, closeness))
    return_array.sort(key=lambda x: x[1])

    return return_array

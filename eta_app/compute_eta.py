from threading import Thread
from haversine import haversine
import pandas as pd
import numpy as np
import datetime, urllib3, json, time, pytz, requests, csv, os
from math import floor, ceil
from statistics import mean
from . import helper


# with open("route_test.json", "r") as read_file:
with open(os.path.join(os.getcwd(),"ikot_route_test.json"), "r") as read_file:
    route_data = json.load(read_file)

# returns the index of the of the route segment nearest to the given location coordinates
# Sean - should refactor this to use app.models (MongoEngine) and use bounding box query
# Sean - use lon,lat too
def locate_segment(coordinates, route = route_data):
    # locate the segment where the point is nearest to
    segment_distances = []
    latlon = (coordinates[1], coordinates[0])
    for segment in route_data:
        distance = haversine(latlon, segment["midpoint"])
        segment_distances.append(distance)
    car_segment = segment_distances.index(min(segment_distances))

    # print(car_segment)
    return car_segment

# does what locate_segment does using route/segment models in database
def new_locate_segment(app, coordinates):
    route = app.models.Segment.objects.all();
    segment_distances = []

    for segment in route:
        midpoint_lonlat = segment.midpoint['coordinates']
        midpoint_latlon = (midpoint_lonlat[1], midpoint_lonlat[0])
        distance = haversine(coordinates, midpoint_latlon)
        segment_distances.append(distance)
        # print(segment.segment_id, ':', midpoint_lonlat, ':', distance)

    nearest_segment = segment_distances.index(min(segment_distances))
    # print('nearest segment: ', nearest_segment)
    return nearest_segment

# returns the total distance covered from the start segment to the destination segment
def compute_total_distance(route, start_segment, end_segment):
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

# computes for the average speed for all segments
# iterates through all of the route segments
# requests for recent car data near all segments and computes for the average speed of the segment based on the speed of nearby cars
def update_all_segments_speeds(config, route=route_data):
    # iterate through the route segments
    i = 0
    while True:
        if config['ENV'] == 'development':
            print('Updating', len(route), 'segments.')
        _debug_old_segment_speeds = []
        _debug_new_segment_speeds = []
        _debug_number_of_updated_segments_with_remote_data = 0

        for segment in route:
            midpoint_latitude = segment["midpoint"][0]
            midpoint_longitude = segment["midpoint"][1]
            seg_radius = segment["length"] / 2.0
            old_speed = segment['speed']
            if config['ENV'] == 'development':
                _debug_old_segment_speeds.append(old_speed)

            # fetch data of cars near the segment
            parsed = helper.fetch_latest_area_data(midpoint_latitude, midpoint_longitude, 15, seg_radius, config)

            # get the average speed of all the cars in the segment
            # in case there are no cars found assume legal speed limit as minimum speed
            # try fix 1: always add/append 8.333 to speed list before getting mean to ensure non-zero value
            # problem, case where there are a lot of cars that have 0 speed, do we assume that the segment is not conjested?
            new_speed = 8.333
            if len(parsed) > 0:
                if config['ENV'] == 'development':
                    _debug_number_of_updated_segments_with_remote_data+=1
                    print("update_all_segments_speeds: found {} new datapoints!".format(len(parsed)))

                speeds_in_segment = [8.333]     # should assure that speed of segment doesnt go to 0
                for l in parsed:
                    speeds_in_segment.append(l['speed'])

                new_speed = mean(speeds_in_segment)

                # logging population mechanism & analyze
                # compare TRUE speed vs REPORTED speed
                if len(parsed) == 1:
                    with open("metrics/population_mechanism_logs.csv", "a") as logs:
                        logs.write("{},{},{},{},{}\n".format(segment['segment_id'],new_speed,parsed[0]['datetime']['$date'],parsed[0]['geojson']['coordinates'][0],parsed[0]['geojson']['coordinates'][1]))

            # always do EWMA step regardless if there are cars or none
            if config['SEGMENT_UPDATE_SCHEME'] == 'basic':
                # EWMA step
                new_speed = recompute_with_EWMA(old_speed,new_speed,config['EWMA_ALPHA'])

            # only do EWMA step when there are no cars on a segment
            elif config['SEGMENT_UPDATE_SCHEME'] == 'dual':
                if len(parsed) <= 0:
                    new_speed = recompute_with_EWMA(old_speed,new_speed,config['EWMA_ALPHA'])

            # Log segment speed changes with the CSV line format:
            # <segment_id>,<old_speed>,<new_speed>,<datetime>
            with open("metrics/segment_changes.csv", "a") as segment_log:
                segment_log.write("{},{},{},{}\n".format(segment['segment_id'], segment['speed'], new_speed, datetime.datetime.now()))
            # save the new speed
            segment['speed'] = new_speed

            if config['ENV'] == 'development':
                _debug_new_segment_speeds.append(new_speed)


        # for debugging
        if config['ENV'] == 'development':
            print('old segment speeds')
            print(["{:.3f}".format(x) for x in _debug_old_segment_speeds])
            print('new segment speeds')
            print(["{:.3f}".format(x) for x in _debug_new_segment_speeds])
            print()
            print("update_all_segments_speeds: Updated {} segments with new data.".format(_debug_number_of_updated_segments_with_remote_data))

        # print('---- Saving Changes ----')
        with open("ikot_route_test.json", "w") as write_file:
            json.dump(route, write_file)
        # print('---- Update Done ----')
        time.sleep(config['FREQUENCY']) # parametrize this

# Computes for the total time to traverse the series of segments from the current location of a car to the destination
# time-to-traverse segment_i = length of segment_i / average speed of segment_i
# total_time_to_traverse = sum(time-to-traverse segment_i) for i = 0,...,n with n: number of segments
# 02/23/20: Add logging capabilities - need to log the relevance of each segment
def compute_eta(car_seg, dest_seg, route=route_data):
    # for logging segment relevance
    segment_relevance_logs = []
    segment_relevance_log = ['-']*(len(route)+1)
    segment_relevance_log[0] = str(datetime.datetime.now())

    total_time_to_traverse = 0.0
    total_distance = compute_total_distance(route, car_seg, dest_seg)

    if(total_distance > 0):
        start = car_seg
        end = dest_seg + 1
        if end > len(route):
            end = 0
        # iterate through the remaining segments from car to destination
        # print('---- Start Computing ETA ----')
        while start != end:
            if(start > len(route)-1):
                start = 0

            # get the length of the segment
            segment_length = route[start]["length"]
            # get the speed of the segment
            segment_speed = route[start]['speed']
            segment_relevance_log[start+1] = "%.4f" %(segment_speed)
            # compute time to traverse the segment

            # if segment_speed <= 0:
            #     segment_speed = 1 # 1m/s

            segment_time_to_traverse = float(segment_length/segment_speed)
            total_time_to_traverse += segment_time_to_traverse

            start+=1
        # print('---- Computing ETA Done ----')

        # for logging segment relevance
        segment_relevance_logs.append(segment_relevance_log)
        print('SEGMENT RELEVANCE (%d)' %(len(segment_relevance_log)), segment_relevance_log)
        with open("metrics/segment_relevance_logs.csv", "a") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(segment_relevance_logs)


    return ceil(total_time_to_traverse/60.0)
def new_compute_eta(car_seg, dest_seg, app):
    route_segments = app.models.Segment.objects.all()
    # create a list of relevant segments
    start = car_seg
    end = dest_seg + 1
    relevant_segments = []

    while start != end:
        if start > len(route_segments)-1:
            start = 0
        relevant_segments.append(start)
        start += 1

    print('Relevant Segments:', relevant_segments)

    # for logging relevant segments' travel time
    segment_relevance_logs = []
    segment_relevance_log = ['-']*(len(route_segments)+1)
    segment_relevance_log[0] = str(datetime.datetime.now())

    total_time_to_traverse = 0
    for segment in route_segments:
        if segment.segment_id in relevant_segments:
            segment_relevance_log[segment.segment_id+1] = segment.running_average_travel_time
            total_time_to_traverse += segment.running_average_travel_time


    # for logging segment relevance
    segment_relevance_logs.append(segment_relevance_log)
    print('SEGMENT RELEVANCE (%d)' %(len(segment_relevance_log)), segment_relevance_log)
    with open("metrics/segment_relevance_logs.csv", "a") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(segment_relevance_logs)

    return ceil(total_time_to_traverse/60.0)

def initialize_to_zero(route=route_data):
    print('---- Starting initialize_to_zero task ----')
    for segment in route:
        previous_speed = segment['speed']
        # segment['speed'] = 0.0
        segment['speed'] = 8.333      # initialized to 8.333 m/s to emulate opening up of segments
        print('segment id: ', segment['segment_id'], ' previous speed: ', previous_speed, ' new speed: ', segment['speed'])
    print('---- Saving Changes ----')
    with open("ikot_route_test.json", "w") as write_file:
        # route_data = json.load(read_file)
        json.dump(route_data, write_file)
    print('---- Initialization Done ----')



def recompute_with_EWMA(previous_data, current_data, ewma_alpha, debug=False):
    new_data = ''
    if type(previous_data) == 'array' and len(previous_data) == len(current_data) and len(previous_data) > 0:
        new_data = [ewma_alpha * c + (1 - ewma_alpha) * l for l,c in zip(previous_data,current_data)]
    elif type(previous_data) == type(current_data) and type(previous_data) == type(0):
        new_data = ewma_alpha * current_data + (1 - ewma_alpha) * previous_data

    if new_data == '':
        raise Exception('recompute_with_EWMA: input arrays are incompatible.')
    else:
        return new_data

def is_recent(data, recency):
    print(data['datetime']['$date'])

def identify_nearest_puv():
    # for testing
    lat = 14.64887259
    lon = 121.06900107
    destination = (lon, lat)

    destination_segment = locate_segment(coordinates = destination)
    print('Destination Segment: ', destination_segment)

    # read route data
    with open("ikot_route_test.json", "r") as read_file:
        route = json.load(read_file)

    # store information in the following lists
    PUV_id = []
    segment_id = []
    datetime = []
    location = []
    segs_before_dest = []

    # query all segments
    for segment in route:
        # use midpoint as reference
        midpoint_latitude = segment["midpoint"][0]
        midpoint_longitude = segment["midpoint"][1]
        seg_length = segment["length"]
        # fetch data of cars near the segment
        NIMPA_URL = 'https://nimpala.me'
        NIMPA_CREDENTIALS = ('root', 'root')
        # Sean - not using &time=[seconds_elapsed] URL parameter.
        rest_operation = '/latest_area?lat={}&lon={}&time={}&radius={}'.format(str(midpoint_latitude), str(midpoint_longitude), 15, seg_length)
        complete_URL = NIMPA_URL + rest_operation
        # print('--- SENDING REQUEST TO:', complete_URL,' ----')
        response = requests.get(complete_URL, auth=NIMPA_CREDENTIALS)
        # print(response)

        # parse the fetched data
        data = 0
        try:
            data = response.json()
        except Exception as e:
            pass
        data = response.text
        print(data)
        parsed = json.loads(data)

        # iterate through lists of PUV data
        if len(parsed) > 0:
            for PUV_data in parsed:
                PUV_id.append(PUV_data['vehicle_id'])
                segment_id.append(segment['segment_id'])
                datetime.append(PUV_data['datetime']['$date'])
                location.append(PUV_data['geojson']['coordinates'])

                # compute distance wrt destination segment
                segment_distance = destination_segment - segment['segment_id']
                if segment_distance < 0:
                    segment_distance = len(route) + segment_distance

                segs_before_dest.append(segment_distance)


    # convert PUV information dict to pandas DataFrame
    PUV_info_dict = {'PUV_id':PUV_id, 'segment_id':segment_id, 'datetime':datetime, 'location':location, 'segs_before_dest':segs_before_dest}
    PUV_df = pd.DataFrame.from_dict(PUV_info_dict)

    PUVs_to_compute_eta = []
    if len(PUV_df) > 0:
        # group by PUV_id, sort by datetime
        df_by_PUV_id = PUV_df.groupby('PUV_id', as_index=False) \
               .apply(lambda x: x.nlargest(1, columns=['datetime'])) \
               .reset_index(level=1, drop=1)
               # .reset_index()
        # df_by_PUV_id = PUV_df.groupby('PUV_id').apply(pd.DataFrame.sort_values, 'datetime')
        # df_by_PUV_id = PUV_df.groupby('PUV_id').apply(lambda x: x.sort_values(['datetime'])).reset_index(drop=True)

        # print(df_by_PUV_id.loc[0])
        # for name in df_by_PUV_id.index:
        #     print(name)
        #     print('segment: ', df_by_PUV_id['segment_id'].loc[name])
        #     print('location: ', df_by_PUV_id['location'].loc[name])
        #     print('no. of segments before dest: ', df_by_PUV_id['segs_before_dest'].loc[name])
        # print(df_by_PUV_id.head())

        # create new dataframe from aggregated groups
        df_by_PUV_id.index.name = None
        df_by_PUV_id.columns = ['PUV_id', 'segment_id', 'datetime', 'location', 'segs_before_dest']

        top_puvs = df_by_PUV_id.sort_values('segs_before_dest').reset_index(drop=1).head(3)
        PUVs_to_compute_eta = top_puvs['PUV_id'].tolist()
        locs_to_vizualize = top_puvs['location'].tolist()
        print(top_puvs['location'].tolist())

    return PUVs_to_compute_eta


def update_segment(app, segment_id):
    segment = app.models.Segment.objects(segment_id=segment_id).first()
    if segment is None:
        raise Exception("update_segment: unable to find Segment with segment_id <{}>".format(segment_id))
    else:
        # latest_area_data fetches data of unique vehicles in the area
        latest_area_data = helper.fetch_latest_area_data(
            latitude=segment.midpoint['coordinates'][1],
            longitude=segment.midpoint['coordinates'][0],
            time=15,
            radius=segment.length / 2,
            config = app.config
        )

        # Preprocess data in attempting to remove ghosting
        # Ghosting - TWO or MORE latest_area_data have the same vehicle with each other.
        # From NIMPA: vehicles are unique with respect to this data.
        for vehicle_location in latest_area_data:
            vehicle_segment_data = app.models.VehicleSegmentData.objects(vehicle_id=vehicle_location['vehicle_id']).first()

            # vehicle is not yet in database.
            # --> REGISTER it in the database and MAP it to segment.
            if vehicle_segment_data is None:
                vehicle_segment_data = app.models.VehicleSegmentData(
                    vehicle_id=vehicle_location['vehicle_id'],
                    vehicle_datetime=datetime.datetime.fromtimestamp(int(vehicle_location['datetime']['$date']) / 1000),
                    vehicle_location=vehicle_location['geojson'],
                    vehicle_segment_speed=vehicle_location['speed'],
                    segment=segment
                )

                vehicle_segment_data.save()
                vehicle_segment_data.reload()

                segment.update(push__vehicles=vehicle_segment_data)

            # vehicle is ALREADY in database.
            # --> Update the database so that its segment is also updated.
            # --> Update this segment and the past segments
            else:
                new_vehicle_location_datetime = datetime.datetime.fromtimestamp(int(vehicle_location['datetime']['$date']) / 1000)
                old_vehicle_location_datetime = vehicle_segment_data.vehicle_datetime

                if new_vehicle_location_datetime > old_vehicle_location_datetime:
                    previous_segment = vehicle_segment_data.segment

                    vehicle_segment_data.update(
                        vehicle_datetime=new_vehicle_location_datetime,
                        vehicle_location=vehicle_location['geojson'],
                        vehicle_segment_speed=vehicle_location['speed'],
                        segment=segment
                    )

                    vehicle_segment_data.reload()

                    previous_segment.update(pull__vehicles=vehicle_segment_data)
                    segment.update(push__vehicles=vehicle_segment_data)

                    segments_traveled = segment.segment_id - previous_segment.segment_id

                    if segments_traveled > 0:
                        travel_time_per_segment = (new_vehicle_location_datetime - old_vehicle_location_datetime).total_seconds() / segments_traveled
                        segments_to_update = app.models.Segment.objects.all().filter(segment_id__gte=previous_segment.segment_id,segment_id__lt=segment.segment_id)
                        for segment_to_update in segments_to_update:
                            if app.config['SEGMENT_UPDATE_SCHEME'] == 'basic':
                                new_running_average_travel_time = mean([segment_to_update.running_travel_time, travel_time_per_segment])
                                segment_to_update.update(running_average_travel_time=new_running_average_travel_time)

                            # EWMA in going back to 'steady state'
                            elif app.config['SEGMENT_UPDATE_SCHEME'] == 'dual':
                                segment_to_update.update(running_average_travel_time=travel_time_per_segment)


def update_all_segments_time(app):
    for segment in app.models.Segment.objects.all():
        update_segment(app,segment.segment_id)

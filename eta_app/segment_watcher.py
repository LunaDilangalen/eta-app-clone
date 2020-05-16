# from . import models
import models
import mongoengine as me

from threading import Thread
from haversine import haversine
import pandas as pd
import numpy as np
import datetime, urllib3, json, time, pytz, requests, csv, os, time
from math import floor, ceil
from statistics import mean
import helper
from pathlib import Path

config = {
'EWMA_ALPHA': 0.05,
'FREQUENCY': 1,
'NIMPA_URL': 'https://nimpala.me',
'NIMPA_CREDENTIALS': ('root', 'root'),
'SEGMENT_UPDATE_SCHEME': 'dual',
'CELERY_BROKER_URL': 'redis://localhost:6379',
'CELERY_RESULT_BACKEND': 'redis://localhost:6379',
'TIMEZONE': 'Asia/Manila',
'MONGODB_HOST':'localhost',
'MONGODB_PORT':27017,
'MONGODB_DB_NAME': 'eta_app',
'MONGODB_SEGMENT_COLLECTION': 'segments',
'MONGODB_VEHICLE_COLLECTION': 'vehicles',
'MONGOENGINE_DB_ALIAS': 'default',
'JSON_ROUTE_DATA': 'ikot_route_test.geojson',
'ZOMBIE_THRESHOLD_TIMEDELTA': 5
}

# configure timezone
os.environ['TZ'] = "Asia/Manila"

me_connection = me.register_connection(db=config['MONGODB_DB_NAME'], alias=config['MONGOENGINE_DB_ALIAS'])

models = models.init_models(config)

current_folder = Path(os.getcwd())
outer_folder = current_folder.parent
update_segment_folder = Path(str(outer_folder), "metrics/data/network_computation/update_segment")


# Updates a Segment (given seg_id) in the database from traffic data in NIMPA
# Flow:
# 1. fetch the desired Segment
# 2. fetch the traffic data from NIMPA
# 3. Iterate through the traffic data and update the Segment accordingly
# 4. returns None
def update_segment(segment_id):
    start_time = time.perf_counter()

    segment = models.Segment.objects(segment_id=segment_id).first()
    if segment is None:
        raise Exception("update_segment: unable to find Segment with segment_id <{}>".format(segment_id))
    else:
        # latest_area_data fetches data of unique vehicles in the area
        _network_time_start = time.perf_counter()

        latest_area_data = helper.fetch_latest_area_data(
            latitude=segment.midpoint['coordinates'][1],
            longitude=segment.midpoint['coordinates'][0],
            time=15,
            radius=segment.length / 2,
            config = config
        )

        _network_time_end = time.perf_counter()
        with open(Path(str(update_segment_folder),"network.csv"), "a") as log_file:
            log_file.write("{},{},{},{},{},{}\n".format(_network_time_end - _network_time_start, segment_id, (segment.length / 2), 15, models.VehicleSegmentData.objects.count(),models.Segment.objects.count()))

        # Initialize zombie_threshhold_timedelta
        zombie_threshhold_timedelta = datetime.timedelta(minutes=config['ZOMBIE_THRESHOLD_TIMEDELTA'])

        # Preprocess data in attempting to remove ghosting
        # Ghosting - TWO or MORE latest_area_data have the same vehicle with each other.
        # From NIMPA: vehicles are unique with respect to this data.
        for vehicle_location in latest_area_data:
            # O(V) lookup
            vehicle_segment_data = models.VehicleSegmentData.objects(vehicle_id=vehicle_location['vehicle_id']).first()
            new_vehicle_location_datetime = datetime.datetime.strptime(vehicle_location['datetime'],"%Y,%m,%d,%H,%M,%S,%f")

            # vehicle is not yet in database.
            # --> REGISTER it in the database and MAP it to segment.
            if vehicle_segment_data is None:
                vehicle_segment_data = models.VehicleSegmentData(
                    vehicle_id=vehicle_location['vehicle_id'],
                    vehicle_datetime=new_vehicle_location_datetime,
                    vehicle_location=vehicle_location['geojson'],
                    vehicle_segment_speed=vehicle_location['speed'],
                    segment=segment
                )

                vehicle_segment_data.save()
                vehicle_segment_data.reload()

                segment.update(push__vehicles=vehicle_segment_data)

            # vehicle is ALREADY in database.
            # It will not take in ghosted data - (same datetime. - What if same lat,lon but diff segments?)
            # --> Update the database so that its segment is also updated.
            # --> Update this segment and the past segments
            else:
                old_vehicle_location_datetime = vehicle_segment_data.vehicle_datetime
                previous_segment = vehicle_segment_data.segment
                segments_traveled = segment.segment_id - previous_segment.segment_id

                # print(new_vehicle_location_datetime, old_vehicle_location_datetime, new_vehicle_location_datetime-old_vehicle_location_datetime, zombie_threshhold_timedelta)

                if segments_traveled < 0:
                    segments_traveled = len(models.Segment.objects.all()) + segments_traveled

                if new_vehicle_location_datetime > old_vehicle_location_datetime and segments_traveled > 0:
                    vehicle_segment_data.update(
                        vehicle_datetime=new_vehicle_location_datetime,
                        vehicle_location=vehicle_location['geojson'],
                        vehicle_segment_speed=vehicle_location['speed'],
                        segment=segment
                    )
                    vehicle_segment_data.reload()
                    previous_segment.update(pull__vehicles=vehicle_segment_data)
                    segment.update(push__vehicles=vehicle_segment_data)

                    if new_vehicle_location_datetime - old_vehicle_location_datetime < zombie_threshhold_timedelta:
                        travel_time_per_segment = (new_vehicle_location_datetime - old_vehicle_location_datetime).total_seconds() / segments_traveled
                        segments_to_update = models.Segment.objects.all().filter(segment_id__gte=previous_segment.segment_id,segment_id__lt=segment.segment_id)
                        for segment_to_update in segments_to_update:
                            if config['SEGMENT_UPDATE_SCHEME'] == 'basic':
                                new_running_average_travel_time = mean([segment_to_update.running_average_travel_time, travel_time_per_segment])
                                segment_to_update.update(running_average_travel_time=new_running_average_travel_time)

                            # EWMA in going back to 'steady state'
                            elif config['SEGMENT_UPDATE_SCHEME'] == 'dual':
                                segment_to_update.update(running_average_travel_time=travel_time_per_segment)

        end_time = time.perf_counter()
        with open(Path(str(update_segment_folder),"total.csv"), "a") as log_file:
            log_file.write("{},{},{},{},{},{}\n".format(end_time - start_time, segment_id, (segment.length / 2), 15, len(latest_area_data), models.VehicleSegmentData.objects.count(),models.Segment.objects.count()))

def update_all_segments_time():
    for segment in models.Segment.objects.all():
        update_segment(segment.segment_id)

def debug(counter):
    # print(' ---- UPDATE %d ---- ' %(counter))
    TTT = []
    for segment in models.Segment.objects.all():
        TTT.append(segment.running_average_travel_time)
    # print(TTT)

def continuous_update():
    update_count = 1
    while True:
        update_all_segments_time()
        debug(update_count)
        update_count += 1
        # time.sleep(config['FREQUENCY'])

def main():
    continuous_update()

if __name__ == '__main__':
    main()

from haversine import haversine, Unit
import pandas, requests

# returns the distance between two points in meters.
def get_distance_from_two_geojson_points(point1, point2):
    return haversine((point1[1], point1[0]),(point2[1], point2[0]),unit=Unit.METERS)

# returns {segment_id: latest_location_data}
def map_vehicle_to_segment(latest_area_data, route_data):
    df = generate_dataframe_from_latest_area_data(latest_area_data)
    df.sort_values(by=['datetime'],ascending=False, inplace=True)
    grouped = df.groupby('vehicle_id')
    for vehicle_id, group in grouped:
        latest_location_vehicle = group.head(1)
        for segment in route_data:
            pass


def generate_dataframe_from_latest_area_data(latest_area_data):
    data_dict = {'vehicle_id': [], 'datetime': [], 'latitude': [], 'longitude': [], 'speed': []}
    for d in latest_area_data:
        data_dict['vehicle_id'].append(d['vehicle_id'])
        data_dict['speed'].append(d['speed'])
        data_dict['datetime'].append(d['datetime']['$date'])
        data_dict['latitude'].append(d['geojson']['coordinates'][1])
        data_dict['longitude'].append(d['geojson']['coordinates'][0])
    return pandas.DataFrame.from_dict(data_dict)


# From NIMPA: vehicles are unique with respect to this data.
def fetch_latest_area_data(latitude,longitude,time,radius,config):
    rest_operation = '/latest_area?lat={}&lon={}&time={}&radius={}'.format(latitude, longitude, time, radius)
    complete_URL = config['NIMPA_URL'] + rest_operation
    # print('--- SENDING REQUEST TO:', complete_URL,' ----')

    # TODO:
    # record avg round travel time
    # average round travel time
    # with open("metrics/data/latest_area_requests.csv", "a") as target_file:
    #     target_file.write("\n".format())
    response = requests.get(complete_URL, auth=config['NIMPA_CREDENTIALS'])
    # with open("metrics/data/latest_area_requests.csv", "a") as target_file:
    #     target_file.write("\n".format())

    # parse the fetched data
    data = 0
    try:
        data = response.json()
    except Exception as e:
        data = response.text
    return data

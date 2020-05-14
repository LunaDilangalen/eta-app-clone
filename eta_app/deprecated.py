with open("ikot_route_test.json", "r") as read_file:
    route_data = json.load(read_file)

# deprecated
def compute_speed_of_segments(car_seg, dest_seg, config, route=route_data):

    # fetch data of cars near each segment, get the average speed of the segment based on the speed of all nearby cars
    # return list of average speeds for all segments
    total_distance = compute_total_distance(route, car_seg, dest_seg)
    total_time_to_traverse = 0.0
    speeds = []
    if(total_distance > 0):
        start = car_seg
        end = dest_seg + 1
        if end > len(route):
            end = 0
        # iterate through the segments
        while start != end:
            if(start > len(route)-1):
                start = 0

            # get the length of the segment
            segment_length = route[start]["length"]

            # fetch data of cars near the segment
            midpoint_lat = route[start]["midpoint"][0]
            midpoint_lon = route[start]["midpoint"][1]
            auth_credentials = ('root', 'root')
            URL = config['NIMPA_URL']
            rest_operation = '/latest_area?lat=%s&lon=%s&time=%s' %(str(midpoint_lat), str(midpoint_lon), 60)
            complete_URL = URL + rest_operation
            # print('---SENDING REQUEST TO:', complete_URL)
            response = requests.get(complete_URL, auth=auth_credentials)

            data = 0
            try:
                data = response.json()
            except Exception as e:
                pass
            data = response.text
            parsed = json.loads(data)

            # get the average speeds on all segments needed to traverse
            # print('Found cars: %d in segment %d' %(len(parsed), start))
            if len(parsed) > 0:
                speed = []
                for l in parsed:
                    speed.append(l["locations"][0]['speed'])
                # print('average speed of segment %d: %f' %(start, mean(speed)))
                # print('speeds on segments: ', speed)
                segment_average_speed = mean(speed)
            else:
                if len(speeds) > 0:
                    segment_average_speed = mean(speeds)
                else:
                    segment_average_speed = 8.333   # assumes speed limit as the minimum speed

            speeds.append(segment_average_speed)

            # calculate time to traverse of the segment
            # need to fix: how to handle zero segment_average_speed
            if segment_average_speed <= 0:
                segment_time_to_traverse = 999999 # lol
            else:
                segment_time_to_traverse = float(segment_length/segment_average_speed)

            total_time_to_traverse += segment_time_to_traverse

            start+=1
            # time.sleep(2)
        print('speeds on segments: ', speeds)
    return ceil(total_time_to_traverse/60)

import sys, datetime, time, pytz, random, requests, argparse

# Written originally by Miguel Sesdeydoro with Wilson Tan.

# Updated 11/10/2019 by Sean Ryan Chan.

# Usage:
#   $  python sean_dripper_geoJSON.py csv_filename [-u URL] [-i id]

parser = argparse.ArgumentParser(description='Simulate sending locational data to the NIMPA server.')
parser.add_argument('csv_filename', type=str, help='Name of the CSV file containing a GPS trace.')
parser.add_argument('-u', dest='URL', default='localhost:5000', help='URL of the NIMPA server. (default: localhost:5000)')
parser.add_argument('-i', dest='random_id', default=random.randint(1,1000), help='ID of the vehicle/object. (default: Random integer between 1-1000.)')
parser.add_argument('-p', dest='HTTP_protocol', default='http', help='Use http or https. (default: http')
parser.add_argument('--username', dest='username', default='root', help='username of your NIMPA account. (default: root)')
parser.add_argument('--password', dest='password', default='root', help='password of your NIMPA account. (default: root)')


rest_operation = '/eta'

args = parser.parse_args()
auth_credentials = (args.username, args.password)
csv_filename_handle = open(args.csv_filename)
URL = args.URL
random_id = args.random_id
HTTP_protocol = args.HTTP_protocol

complete_URL = HTTP_protocol + '://' +URL + rest_operation

csv_file = csv_filename_handle.readlines()
read = False
valz = []

for k in csv_file:
    if read == False:
        read = True
    else:
        j = k.split(',')
        unx = (datetime.datetime.fromtimestamp(int(j[0]) // 1000) - datetime.datetime(1970,1,1)).total_seconds()
        valz.append((unx,j[1],j[2],j[6]))

start = False
for k in range(0,len(valz)):
    if k < len(valz)-1:
        delay = float(valz[k+1][0])-float(valz[k][0])
    if delay < 0:
        del valz[k+1]

for k in range(0,len(valz)):
    u = datetime.datetime.utcnow()
    u = u.replace(tzinfo=pytz.utc)
    if valz[k][3]!="":
        data_json = {
        'vehicle_id': random_id,
        'datetime': str(datetime.datetime.now()),
        'geojson': {
            'type': 'Point',
            'coordinates': [float(valz[k][2]),float(valz[k][1])]
        },
        "speed":float(valz[k][3])
        }
        print('---SENDING REQUEST TO:', complete_URL)
        print(data_json)
        requests.post(complete_URL, json=data_json, auth=auth_credentials)
    if k < len(valz)-1:
        delay = float(valz[k+1][0])-float(valz[k][0])
        time.sleep(delay)

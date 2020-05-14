import datetime as dt


EWMA_ALPHA = 0.05   # make the decay slower or,
FREQUENCY = 2   # update less
NIMPA_URL = 'https://nimpala.me'
NIMPA_CREDENTIALS = ('root', 'root')
SEGMENT_UPDATE_SCHEME = 'dual'


# Affects task_scheduler.py
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
TIMEZONE = 'Asia/Manila'


# MongoDB and MongoEngine
MONGODB_HOST='localhost'
MONGODB_PORT=27017
MONGODB_DB_NAME = 'eta_app'
MONGODB_SEGMENT_COLLECTION = 'segments'
MONGODB_VEHICLE_COLLECTION = 'vehicles'
MONGOENGINE_DB_ALIAS = 'default'

JSON_ROUTE_DATA = 'ikot_route_test.geojson'


# eta_computer
ROUTE_DIRECTION = "increasing"
CONSIDER_DESTINATION_SEGMENT = False
DEFAULT_MAX_NUMBER_OF_PUVS = 3
DEFAULT_ZOMBIE_TIMEDELTA = dt.timedelta(minutes=5)

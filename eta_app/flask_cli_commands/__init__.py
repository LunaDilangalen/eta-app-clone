from . import seed_segment_db
from . import clean_segment_db
from . import clean_vehicle_db
from . import init_performance_logs

# 3 commands
# 1. seed Segment MongoDB collection
# 2. clean Segment MongoDB Collection
# 2. clean VehicleSegmentData MongoDB Collection

def init_commands(app, mongoengine_models):
    seed_segment_db.init_command(app, mongoengine_models)
    clean_segment_db.init_command(app, mongoengine_models)
    clean_vehicle_db.init_command(app, mongoengine_models)
    init_performance_logs.init_command(app, mongoengine_models)

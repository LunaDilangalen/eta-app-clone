from . import segment
from . import vehicle_segment_data

class MongoengineModels(object):
    """This is an object that holds different MongoEngine.Document classes."""

    def __init__(self, config):
        super(MongoengineModels, self).__init__()

        # See ./segment.py
        self.Segment = segment.init_segment_model(config)

        # See ./vehicle_segment_data.py
        self.VehicleSegmentData = vehicle_segment_data.init_vehicle_segment_data_model(config)

def init_models(config):
    return MongoengineModels(config)

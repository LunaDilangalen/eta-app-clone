import mongoengine as me

def init_vehicle_segment_data_model(config):

    class VehicleSegmentData(me.Document):
        # vehicle data is tied to segment
        vehicle_id = me.IntField(null=True)
        vehicle_datetime = me.ComplexDateTimeField()
        vehicle_location = me.PointField()
        vehicle_segment_speed = me.FloatField()
        vehicle_segment_travel_time = me.FloatField()

        segment = me.ReferenceField('Segment')
        meta = {
            'collection': config['MONGODB_VEHICLE_COLLECTION'],
            'indexes':
            [
                'vehicle_datetime',
                {
                "fields": ['vehicle_id'],
                "unique": True,
                "partialFilterExpression": {
                    "vehicle_id": {"$type": "int"}
                    }
                }
            ]
        }
    return VehicleSegmentData

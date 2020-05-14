import mongoengine as me

def init_segment_model(config):

    class Segment(me.Document):
        segment_id = me.IntField(unique=True)
        label = me.StringField()
        length = me.FloatField()
        segment = me.LineStringField() # GeoJSON LineString.
        midpoint = me.PointField() # GeoJSON PointField.
        vehicles = me.ListField(me.ReferenceField('VehicleSegmentData'))
        running_average_speed = me.FloatField()
        running_average_travel_time = me.FloatField()
        last_updated = me.ComplexDateTimeField()


        meta = {'collection': config['MONGODB_SEGMENT_COLLECTION'],
                'indexes': ['segment_id', 'last_updated']}

    return Segment

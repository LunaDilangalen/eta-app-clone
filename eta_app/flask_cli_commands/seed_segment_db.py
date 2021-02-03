import click, json, os

def init_command(app, mongoengine_models):

    @app.cli.command("seed-segment-db")
    @click.argument("file")
    def seed_segment_db(file):
        print('----- seeding route data into DB -----') # for logging
        if file == 'ikot':
            file = os.path.join(os.getcwd(), app.config['JSON_ROUTE_DATA'])
        with open(file) as json_route_data:
            segments = json.load(json_route_data)
            for segment in segments:
                if app.models.Segment.objects(segment_id=segment['segment_id']).first() is None:
                    new_segment = app.models.Segment(
                        segment_id=segment['segment_id'],
                        running_average_speed = segment['speed'],
                        running_average_travel_time = segment['travel_time'],
                        length = segment['length'],
                        segment = segment['segment'],
                        midpoint = segment['midpoint']
                        )
                    new_segment.save()

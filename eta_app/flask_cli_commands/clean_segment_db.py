import click

def init_command(app, mongoengine_models):
    @app.cli.command("clean-segment-db")
    def clean_segment_db():
        app.models.Segment.objects.all().delete()

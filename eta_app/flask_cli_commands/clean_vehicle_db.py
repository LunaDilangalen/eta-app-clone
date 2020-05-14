import click

def init_command(app, mongoengine_models):
    @app.cli.command("clean-vehicle-db")
    def clean_vehicle_db():
        app.models.VehicleSegmentData.objects.all().delete()

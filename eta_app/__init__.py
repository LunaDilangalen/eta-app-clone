from flask import Flask, render_template, request, jsonify
# from flask_apscheduler import APScheduler

import requests, threading, json, os, subprocess, time

from . import compute_eta
from . import eta_computer


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Configuration
    # loads config from instance/config.py
    app.config.from_pyfile('config.py')


    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    # MODELS ---------
    import mongoengine as me
    from . import models
    app.models = models.init_models(app.config)
    app.me_connection = me.register_connection(db=app.config['MONGODB_DB_NAME'], alias=app.config['MONGOENGINE_DB_ALIAS'])
    app.me = me
    # ---------------
    # CLI COMMANDS --
    from . import flask_cli_commands
    flask_cli_commands.init_commands(app, app.models)
    # -----------
    # INSTANIATE THE ETA COMPUTER
    # original_working_directory = os.getcwd()
    # TODO:
    # put eta_computer in its own module folder... |-->
    # os.chdir(__name__)
    # subprocess.run(["python", "eta_computer.py"])
    # os.chdir(original_working_directory)
    # -----------


    @app.route('/generic_eta')
    def generic_eta():
        start_time = time.perf_counter()

        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))

        max_number_of_puvs = app.config['DEFAULT_MAX_NUMBER_OF_PUVS']
        if request.args.get('puvs') is not None:
            max_number_of_puvs = int(request.args.get('puvs'))

        destination = (lon, lat)
        normal_format_destination = (lat,lon)
        vehicle_segments_total_travel_time_array = eta_computer.generic_eta(app, destination,
        max_number_of_puvs=max_number_of_puvs,
        consider_destination_segment=app.config['CONSIDER_DESTINATION_SEGMENT'],
        route_direction=app.config['ROUTE_DIRECTION'],
        zombie_threshhold_timedelta=app.config['DEFAULT_ZOMBIE_TIMEDELTA']
        )

        # eta_seconds == 0 will not really evaluate to True --> should implement a tolerance check.
        visual_array = [ (vehicle, segments, "Vehicle has arrived!") if eta_seconds == 0 else (vehicle, segments, eta_seconds) for vehicle, segments, eta_seconds in vehicle_segments_total_travel_time_array]
        destination_segment_id = compute_eta.new_locate_segment(app, normal_format_destination)

        end_time = time.perf_counter()
        with open(os.path.join(os.getcwd(),"metrics/data/network_computation/generic_eta/computation.csv"), "a") as log_file:
            log_file.write("{},{},{},{}\n".format(end_time - start_time, max_number_of_puvs, app.models.Segment.objects.count(), app.models.VehicleSegmentData.objects.count()))

        return render_template('generic_eta.html', vehicle_segments_total_travel_time_array=visual_array, destination_segment_id=destination_segment_id)

    @app.route('/generic_eta.json')
    def generic_eta_json():
        start_time = time.perf_counter()

        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))

        max_number_of_puvs = app.config['DEFAULT_MAX_NUMBER_OF_PUVS']
        if request.args.get('puvs') is not None:
            max_number_of_puvs = int(request.args.get('puvs'))

        destination = (lon, lat)
        normal_format_destination = (lat,lon)
        vehicle_segments_total_travel_time_array = eta_computer.generic_eta(app, destination,
        max_number_of_puvs=max_number_of_puvs,
        consider_destination_segment=app.config['CONSIDER_DESTINATION_SEGMENT'],
        route_direction=app.config['ROUTE_DIRECTION'],
        zombie_threshhold_timedelta=app.config['DEFAULT_ZOMBIE_TIMEDELTA']
        )

        destination_segment_id = compute_eta.new_locate_segment(app, normal_format_destination)

        end_time = time.perf_counter()
        with open(os.path.join(os.getcwd(),"metrics/data/network_computation/generic_eta/computation.csv"), "a") as log_file:
            log_file.write("{},{},{},{}\n".format(end_time - start_time, max_number_of_puvs, app.models.Segment.objects.count(), app.models.VehicleSegmentData.objects.count()))

        ret_json = []
        for vehicle, segments, eta_seconds in vehicle_segments_total_travel_time_array:
            ret_json.append({
            "eta_seconds": eta_seconds,
            "vehicle": {
                "id": vehicle.vehicle_id,
                "location": vehicle.vehicle_location,
                "segment": vehicle.segment.segment_id
            },
            "segments_to_cross": len(segments)
            })
        return jsonify(ret_json)


    @app.route('/eta_visual')
    def eta_visual():
        # from client get destination coordinates
        # call identify_nearest_puv() when client requests for eta of nearest PUVs
        # compute for ETA of top 3 PUVs
        #
        top3_puv_ids = compute_eta.identify_nearest_puv()
        base_url = app.config['NIMPA_URL']
        rest_operation = '/latest_location?id='
        complete_URL = base_url + rest_operation + str(top3_puv_ids[2])
        return render_template('eta_visual.html', ids=top3_puv_ids, json_url_resource3=complete_URL)

    @app.route('/new_locate_segment')
    def new_locate_segment():
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        coordinates = (lat, lon)
        print('HELLO')
        compute_eta.new_locate_segment(app, coordinates)

        return render_template('index.html')
    return app

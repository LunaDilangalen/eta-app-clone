import click, os, shutil

def init_command(app, mongoengine_models):
    @app.cli.command("init-perf-logs")
    def init_performance_logs():
        # check folders
        app_directory = os.getcwd()
        logs_root_folder = os.path.join(os.path.join(app_directory, 'metrics/data/'))
        # print('Root: ', logs_root_folder)   # for instance logs
        print('----- initializing performance logs -----')  # for instance logs
        if os.path.isdir(logs_root_folder) is False:
            os.mkdir(logs_root_folder)

        network_computation_folder = os.path.join(logs_root_folder, 'network_computation')
        if os.path.isdir(network_computation_folder) is False:
            os.mkdir(network_computation_folder)

        generic_eta_folder = os.path.join(network_computation_folder,'generic_eta')
        if os.path.isdir(generic_eta_folder) is False:
            os.mkdir(generic_eta_folder)

        update_segment_folder = os.path.join(network_computation_folder,'update_segment')
        if os.path.isdir(update_segment_folder) is False:
            os.mkdir(update_segment_folder)



        # check files, create and write headers if neccessary
        filename = os.path.join(generic_eta_folder,'computation.csv')
        if os.path.isfile(filename) is False:
            with open(filename, "a") as file:
                file.write("time,max_number_of_puvs,number_of_segments,number_of_vehicles\n")

        from_file = open(filename)
        line = from_file.readline()
        line = "time,max_number_of_puvs,number_of_segments,number_of_vehicles\n"
        to_file = open(filename,mode="w")
        to_file.write(line)
        shutil.copyfileobj(from_file, to_file)

        filename = os.path.join(update_segment_folder,'network.csv')
        if os.path.isfile(filename) is False:
            with open(filename, "a") as file:
                file.write("time,segment_id,radius_parameter,time_elapsed_parameter,number_of_vehicles,number_of_segments\n")

        from_file = open(filename)
        line = from_file.readline()
        line = "time,segment_id,radius_parameter,time_elapsed_parameter,number_of_vehicles,number_of_segments\n"
        to_file = open(filename,mode="w")
        to_file.write(line)
        shutil.copyfileobj(from_file, to_file)

        filename = os.path.join(update_segment_folder,'total.csv')
        if os.path.isfile(filename) is False:
            with open(filename, "a") as file:
                file.write("time,segment_id,radius_parameter,time_elapsed_parameter,number_of_locations_received,number_of_vehicles,number_of_segments\n")

        from_file = open(filename)
        line = from_file.readline()
        line = "time,segment_id,radius_parameter,time_elapsed_parameter,number_of_locations_received,number_of_vehicles,number_of_segments\n"
        to_file = open(filename,mode="w")
        to_file.write(line)
        shutil.copyfileobj(from_file, to_file)

        filename = os.path.join(update_segment_folder,'computation.csv')
        if os.path.isfile(filename) is False:
            with open(filename, "a") as file:
                file.write("time,segment_id,radius_parameter,time_elapsed_parameter,number_of_locations_received,number_of_vehicles,number_of_segments\n")

        from_file = open(filename)
        line = from_file.readline()
        line = "time,segment_id,radius_parameter,time_elapsed_parameter,number_of_locations_received,number_of_vehicles,number_of_segments\n"
        to_file = open(filename,mode="w")
        to_file.write(line)
        shutil.copyfileobj(from_file, to_file)

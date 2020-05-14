import pandas, datetime, geopandas, json, haversine, pytz
import matplotlib.pyplot as plt
import matplotlib.dates as md
import numpy as np
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)
import os

local_tz = pytz.timezone('Asia/Manila')

def prepare_eta_graph(csv_data_file="metrics/eta_logs.csv", title='ETA Graph'):
    # initialize figure on GLOBAL pyplot instance.
    fig = plt.figure()
    plt.title(title)

    # get data.
    df = pandas.read_csv(csv_data_file, header=None, names=['datetime', 'eta_mins'])
    df['datetime'] = pandas.to_datetime(df['datetime'])
    df['eta_mins'] = pandas.to_numeric(df['eta_mins'])
    x = df['datetime']
    y = df['eta_mins']
    plt.plot(x,y, '-')
    ax=plt.gca()

    time_series_format = md.DateFormatter('%I:%M:%S %p')
    ax.xaxis.set_major_formatter(time_series_format)
    ax.set_xlabel('Time')
    ax.set_ylabel('ETA in minutes')
    ax.set_ylim(ymin=0)

    # float_formatter = "{:.2f}".format
    # for i,j in zip(x,y):
    #     ax.annotate(float_formatter(j),xy=(i,j), xytext=(5,5), textcoords='offset points')
    make_major_minor_ticks_and_grid(plt,ax)


def prepare_error_graph(csv_data_file="metrics/eta_logs.csv", arrival_time='Assume', title='Error Graph', patong=False):
    default_arrival_time_acacia_dcs = datetime.timedelta(minutes=15)
    fig = plt.figure()
    plt.title(title)
    ax=plt.gca()
    _y_label = ''
    # if multiple datafiles
    if type(csv_data_file) == type([]):
        if patong:
            pass
            # NOT WORKING
            # possible_x =[]
            # y_arrays = []
            # for data_file in csv_data_file:
            #     x, y, end_time = get_xy_and_end_time(data_file,arrival_time)
            #     possible_x.append(x)
            #     y_arrays.append(y)
            #
            # max =0
            # for datetime_array in possible_x:
            #     if len(datetime_array) > max:
            #         max = len(datetime_array)
            #
            # ind = np.arange(max)
            # for i, y in enumerate(y_arrays):
            #     ax.plot(ind, y,'-', label=csv_data_file[i])

        else:
            for data_file in csv_data_file:
                x, y, end_time = get_xy_and_end_time(data_file,arrival_time)
                plt.plot(x,y,'-', label='Arrival ' + end_time.strftime('%I:%M'))

            _y_label = 'Differences from their true arrival times in minutes'
    # if single
    elif type(csv_data_file) == type(''):
        x, y, end_time = get_xy_and_end_time(csv_data_file,arrival_time)
        plt.plot(x,y,'-')
        _y_label = 'Difference from true arrival time ' + end_time.strftime('%I:%M:%S %p') + ' in minutes'

    time_series_format = md.DateFormatter('%I:%M %p')
    ax.xaxis.set_major_formatter(time_series_format)
    ax.set_xlabel('Time')
    ax.set_ylabel(_y_label)
    ax.set_ylim(ymin=0)
    make_major_minor_ticks_and_grid(plt, ax)

# does not know any relevant segments wrt. computation
def prepare_segment_evolution_graph(csv_data_file="metrics/segment_changes.csv", title="Segment Evolution Graph"):
    fig = plt.figure()
    plt.title(title)
    df = pandas.read_csv(csv_data_file, header=None, names=['segment_id', 'old_speed', 'new_speed', 'datetime'])
    df['datetime'] = pandas.to_datetime(df['datetime'])
    df['segment_id'] = pandas.to_numeric(df['segment_id'])
    df['old_speed'] = pandas.to_numeric(df['old_speed'])
    df['new_speed'] = pandas.to_numeric(df['new_speed'])
    ax=plt.gca()
    for i, g in df.groupby('segment_id'):
        g.plot(x='datetime', y='new_speed', ax=ax, label="Seg. {}".format(i))

    ax.set_xlabel('Time')
    ax.set_ylabel('Segment speed (m/s)')
    make_major_minor_ticks_and_grid(plt,ax)


def prepare_population_mechanism_graph(csv_data_file="metrics/population_mechanism_logs.csv", title="Population mechanism graph"):

    df = pandas.read_csv(csv_data_file, header=None, names=['segment_id', 'reported_speed', 'datetime', 'longitude', 'latitude'])
    # cross reference with ikot_route_test.json' segment_distances
    # compute a ground_truth speed per segment

    df['datetime'] = df['datetime'].apply(lambda x: datetime.datetime.fromtimestamp(x / 1000) )
    df['segment_id'] = pandas.to_numeric(df['segment_id'])
    df['reported_speed'] = pandas.to_numeric(df['reported_speed'])
    df['longitude'] = pandas.to_numeric(df['longitude'])
    df['latitude'] = pandas.to_numeric(df['latitude'])
    # CONSIDER consider ikot_route_test.json
    gdf = geopandas.GeoDataFrame(df,crs="epsg:4326", geometry=geopandas.points_from_xy(df.longitude, df.latitude))
    df.sort_values(by=['datetime'], inplace=True, ascending=True)
    grouped = df.groupby(['segment_id'])
    avg_reported_speeds = grouped['reported_speed'].aggregate('mean')

    route_data = 0
    with open('ikot_route_test.json') as json_file:
        route_data  = json.load(json_file)

    # Non geopandas implementation
    df_walkthrough = grouped.agg(lambda x: x.iloc[0]).sort_values(by=['datetime'],ascending=True).reset_index()
    walk_rows,walk_cols = df_walkthrough.shape
    data_dict={'segment_id': [], 'reported_speed': [], 'true_speed': []}
    for index, row in df_walkthrough.iterrows():
        if index == walk_rows-1 or index == 0:
            pass
        else:
            next_row = df_walkthrough.iloc[index+1]
            if next_row['datetime'] != row['datetime']:
                # expressed in meters
                distance = route_data[row['segment_id']]['length']
                # expressed in seconds
                time = abs((next_row['datetime'] - row['datetime']).total_seconds())
                # thus, expressed in m / s
                true_speed = distance/time
                data_dict['segment_id'].append(row['segment_id'])
                data_dict['reported_speed'].append(avg_reported_speeds[row['segment_id']])
                data_dict['true_speed'].append(true_speed)

    final_df = pandas.DataFrame.from_dict(data_dict)

    w = 0.3
    fig, ax = plt.subplots()
    ind = np.arange(len(data_dict['segment_id']))
    true_speed_bar = ax.bar(ind, data_dict['true_speed'], width=w, color='g', align='center', label='true_speed')
    reported_speed_bar= ax.bar(ind + w, data_dict['reported_speed'], width=w, color='r', align='center', label='reported_speed')
    ax.set_title(title)
    ax.set_xticks(ind + w / 2)
    ax.yaxis.set_minor_locator(AutoMinorLocator(5))
    ax.set_xticklabels(data_dict['segment_id'])
    ax.legend((true_speed_bar[0],reported_speed_bar[0]), ('true_speed', 'reported_speed'))
    ax.set_xlabel('Segment ID')
    ax.set_ylabel('Speed in m/s')
    ax.autoscale_view()

    fig, ax = plt.subplots()
    errors = [abs(x-y) for x,y in zip(data_dict['true_speed'],data_dict['reported_speed'])]
    error_bar = ax.bar(ind, errors, width=w, color='r', align='center', label='errors')
    # error_mean = ax.plot([ind[0], ind[-1]], [np.mean(errors), np.mean(errors)], "k--")
    error_mean = ax.axhline(np.mean(errors), color='b', label='error_mean')
    ax.yaxis.set_minor_locator(AutoMinorLocator(5))
    ax.set_title('Error from true_speed and reported_speed')
    ax.set_xticks(ind + w / 2)
    # ax.legend((error_bar[0]), ('Error mean of {:.3f}'.format(np.mean(errors))))
    ax.set_xticklabels(data_dict['segment_id'])
    ax.set_xlabel('Segment ID')
    ax.set_ylabel('Error speed in m/s')
    # make_major_minor_ticks_and_grid(plt,ax)


def show_graphs():
    # display figures associated with GLOBAL pyplot instance.
    plt.show()

def generate_graphs(csv_data_file="metrics/eta_logs.csv"):
    prepare_eta_graph(csv_data_file)
    prepare_error_graph(csv_data_file)
    show_graphs()


# Helper function
def make_major_minor_ticks_and_grid(plt, ax, x_ticks=True, y_ticks=True):
    ax.tick_params(which='both', width=2)
    ax.tick_params(which='major', length=7)
    ax.tick_params(which='minor', length=4)
    # Show the major grid lines with dark grey lines
    plt.grid(b=True, which='major', color='#666666', linestyle='-')
    # Show the minor grid lines with very faint and almost transparent grey lines
    plt.minorticks_on()
    plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)

def get_xy_and_end_time(data_file, arrival_time):
    data = pandas.read_csv(data_file, header=None, names=['datetime', 'eta_mins'])
    data['datetime'] = pandas.to_datetime(data['datetime'])
    data['eta_mins'] = pandas.to_numeric(data['eta_mins'])
    x = data['datetime']
    y = []
    rows,cols = data.shape
    end_time = 0
    if arrival_time == 'Assume':
        # assume that the last point is the end_time.
        end_time = x[rows-1]

        # compute y for each eta_prediction.
        for index,row in data.iterrows():
            current_time = row['datetime']
            eta_mins = row['eta_mins']
            proposed_end_time = current_time + datetime.timedelta(minutes=eta_mins)
            timedelta = proposed_end_time - end_time
            error = abs(timedelta.total_seconds()) / 60
            y.append(error)
    elif type(arrival_time) != datetime.datetime:
        raise Exception('prepare_error_graph: arrival_time must be of type <datetime>')
    else:
        for eta in data['eta_mins']:
            proposed_end_time = start_time + datetime.timedelta(minutes=eta)
            timedelta = proposed_end_time - arrival_time
            error = abs(timedelta.total_seconds()) / 60
            y.append(error)

    return x, y, end_time

def geojson_haversine(geojson_tuple_a, geojson_tuple_b, haversine, **kwargs):
    flipped_a = geojson_tuple_a[1], geojson_tuple_a[0]
    flipped_b = geojson_tuple_b[1], geojson_tuple_b[0]
    return haversine(flipped_a,flipped_b, **kwargs)


#
# PERFORMANCE GRAPHS
# Note: all relevant csv files have been updated to have headers

def prepare_performance_graph(csv_data_file, independent_variables, dependent_variable='time'):
    if len(independent_variables) <= 0 and type([]) != independent_variables:
        raise Exception("Not allowed!")

    df = pandas.read_csv(csv_data_file, header=0)
    filename = os.path.basename(csv_data_file)
    foldername = os.path.split(os.path.split(csv_data_file)[0])[1]

    # multidimensional
    ax = df.groupby(independent_variables)[dependent_variable].mean().plot.bar()
    ax.set_ylabel('Time in seconds')
    ax.set_title('Computation delay of ' + foldername + '/' + filename)

    fig = ax.figure
    bars = ax.containers[0]
    # hover annotation style
    # https://stackoverflow.com/questions/50560525/how-to-annotate-the-values-of-x-and-y-while-hovering-mouse-over-the-bar-graph/50560826#50560826
    annot = ax.annotate("", xy=(0,0), xytext=(-20,20),textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="black", ec="b", lw=2),
                    arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    def update_annot(bar):
        x = bar.get_x()+bar.get_width()/2.
        y = bar.get_y()+bar.get_height()
        annot.xy = (x,y)
        text = "({:.3g} s)".format(y)
        annot.set_text(text)
        annot.get_bbox_patch().set_alpha(0.4)


    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            for bar in bars:
                cont, ind = bar.contains(event)
                if cont:
                    update_annot(bar)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return
        if vis:
            annot.set_visible(False)
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)

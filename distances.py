from argparse import ArgumentParser
from os import environ
from os.path import join

import geopy
import requests
from invisibleroads_macros.disk import make_folder
from pandas import DataFrame

from load_lines import load_unique_lines


def run(target_folder, origins_path, destinations_path, mode):
    """
        make a table that ranks from least total time to most
    """
    # set up results paths
    results_path = join(target_folder, 'results.csv')
    rankings_path = join(target_folder, 'rankings.csv')
    log_path = join(target_folder, 'log_results.txt')
    geomap_path = join(target_folder, 'geomap.csv')

    origins = load_unique_lines(origins_path)
    destinations = load_unique_lines(destinations_path)

    distances = get_distance_matrix(origins, destinations, mode)

    # TODO: Check status of each output -> result.rows[i].elements[i].status
    origins, destinations = (distances['origin_addresses'],
                             distances['destination_addresses'])
    origin_to_destination_stats = zip(origins, distances['rows'])

    geomap_table = get_geotable(origins, destinations)
    geomap_table.to_csv(geomap_path, index=False)
    duration_results, rankings = get_results(origin_to_destination_stats,
                                             destinations)
    # Output results
    log = [origin + ': ' + str(total_time) for
           origin, total_time in rankings]
    log = "\n".join(log)
    with open(log_path, 'w') as f:
        f.write(log)
    columns = ['Lodging Name', 'Destination', 'Duration']
    results_table = DataFrame(duration_results, columns=columns)
    results_table.to_csv(results_path, index=False)

    columns = ['Lodging Name', 'Total Time']
    rankings_table = DataFrame(rankings, columns=columns)
    rankings_table.to_csv(rankings_path, index=False)

    # Required print statement for crosscompute
    print("points_geotable_path = {0}".format(geomap_path))
    print("rankings_table_path = {0}".format(rankings_path))
    print("results_table_path = {0}".format(results_path))
    print("results_text_path = {0}".format(log_path))
    return (geomap_table, rankings_table)


def get_results(origin_stats, destinations):
    data = []
    rankings = []
    for lodging_name, lodging_stats in origin_stats:
        # get duration to each destination from current lodging
        sum_times = 0
        for destination, destination_info in zip(
                destinations, lodging_stats['elements']):
            dest_time = destination_info['duration']['value']
            sum_times += dest_time
            data.append((lodging_name, destination, dest_time))
        rankings.append((lodging_name, sum_times))
    rankings = sorted(rankings, key=(lambda time: time[1]))
    return (data, rankings)


def get_distance_matrix(origins, destinations, mode):
    # Use google's distancematrix api
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?"
    url_params = {"origins": "|".join(origins),
                  "mode": mode,
                  "destinations": "|".join(destinations),
                  "language": "en-EN",
                  "units": "imperial",
                  "key": 'AIzaSyBhNXrJJKvAj6-h5ceUe769JM-u4olg6Jo'}
    response = requests.get(url, params=url_params).json()
    for r in response['rows']:
        for e in r['elements']:
            print e['duration']['value']
    return response


def get_geotable(origins, destinations):
    google_geo = geopy.GoogleV3()
    coordinates = [(address,
                    google_geo.geocode(address).latitude,
                    google_geo.geocode(address).longitude,
                    'red',
                    '20') for address in origins]
    coordinates.extend([(address,
                         google_geo.geocode(address).latitude,
                         google_geo.geocode(address).longitude,
                         'blue',
                         '10') for address in destinations])
    geomap_table = DataFrame(coordinates, columns=['name',
                                                   'latitude',
                                                   'longitude',
                                                   'fill color',
                                                   'radius in pixels'])
    return geomap_table


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--target_folder', nargs='?', default='results',
                        type=make_folder, metavar='FOLDER')
    parser.add_argument('--origins', '-O',
                        type=str, metavar='PATH', required=True)
    parser.add_argument('--destinations', '-D',
                        type=str, metavar='PATH', required=True)
    parser.add_argument('--mode', '-M',
                        type=str, metavar='PATH', default='driving',
                        choices=['driving', 'walking', 'cycling'])
    args = parser.parse_args()
    run(args.target_folder,
        args.origins,
        args.destinations,
        args.mode)

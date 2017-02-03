from argparse import ArgumentParser
from os import environ
from os.path import join

import geopy
import requests
from invisibleroads_macros.disk import make_folder
from pandas import DataFrame


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
    origins, destinations = (response['origin_addresses'],
                             response['destination_addresses'])
    distances = []
    for o, rows in zip(origins, response['rows']):
        dest_distances = []
        s = 0
        for d, r in zip(destinations, rows['elements']):
            dest_distances.append((d, r))
            duration = r['duration']['value']
            s += duration
        distances.append({'name': o, 'total': s, 'distances': dest_distances})
    return distances


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
    geomap = DataFrame(coordinates, columns=['name',
                                             'latitude',
                                             'longitude',
                                             'fill color',
                                             'radius in pixels'])
    return geomap


def load_unique_lines(source_path):
    if not source_path:
        return []
    with open(source_path, 'r') as f:
        lines = list(set((x.strip(', ;\n') for x in f)))
    return sorted(filter(lambda x: x, lines))


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
    origins = load_unique_lines(args.origins)
    destinations = load_unique_lines(args.destinations)
    distances = get_distance_matrix(origins, destinations, args.mode)
    rankings = [(d['name'], d['total']) for d in distances]
    rankings = sorted(rankings, key=(lambda x: x[1]))
    duration_results = []
    for d in distances:
        for dest_dist in d['distances']:
            duration_results.append((d['name'], dest_dist[0], dest_dist[1]['duration']['value']))

    target_folder = args.target_folder

    geomap_path = join(target_folder, 'geomap.csv')
    geomap_table = get_geotable(origins, destinations)
    geomap_table.to_csv(geomap_path, index=False)

    results_path = join(target_folder, 'results.csv')
    columns = ['Lodging Name', 'Destination', 'Duration']
    results_table = DataFrame(duration_results, columns=columns)
    results_table.to_csv(results_path, index=False)

    rankings_path = join(target_folder, 'rankings.csv')
    columns = ['Lodging Name', 'Total Time']
    rankings_table = DataFrame(rankings, columns=columns)
    rankings_table.to_csv(rankings_path, index=False)

    # Required print statement for crosscompute
    print("points_geotable_path = {0}".format(geomap_path))
    print("rankings_table_path = {0}".format(rankings_path))
    print("results_table_path = {0}".format(results_path))

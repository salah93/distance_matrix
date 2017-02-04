from argparse import ArgumentParser
from os import environ
from os.path import join

import geopy
import numpy as np
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
                  "key": environ['DISTANCE_KEY']}
    response = requests.get(url, params=url_params).json()
    # get lat, lng from request
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
        distances.append({'name': o,
                          'total': '%d minute(s)' % (s / 60),
                          'distances': dest_distances})
    return distances


def get_geotable(origins_sorted_by_rank, destinations):
    google_geo = geopy.GoogleV3()
    minimum_pixel_size, max_pixel_size = 10, 50
    sizes = np.linspace(minimum_pixel_size,
                        max_pixel_size,
                        len(origins_sorted_by_rank))[::-1]
    origins_color = 'red'
    destinations_color = 'blue'
    destinations_pixel_size = 10
    coordinates = [(address,
                    google_geo.geocode(address).latitude,
                    google_geo.geocode(address).longitude,
                    origins_color,
                    str(size)) for address, size in zip(origins_sorted_by_rank,
                                                        sizes)]
    coordinates.extend([(address,
                         google_geo.geocode(address).latitude,
                         google_geo.geocode(address).longitude,
                         destinations_color,
                         str(destinations_pixel_size))
                        for address in destinations])
    return DataFrame(coordinates, columns=['name',
                                           'latitude',
                                           'longitude',
                                           'fill color',
                                           'radius in pixels'])


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
            duration_results.append((d['name'],
                                     dest_dist[0],
                                     dest_dist[1]['duration']['text']))

    target_folder = args.target_folder

    geomap_path = join(target_folder, 'geomap.csv')
    try:
        geomap_table = get_geotable([origin[0] for origin in rankings],
                                    destinations)
        geomap_table.to_csv(geomap_path, index=False)
        print("points_geotable_path = {0}".format(geomap_path))
    except geopy.exc.GeocoderTimedOut as e:
        print("geomap geocode timeout error: %s" % e.message)

    results_path = join(target_folder, 'results.csv')
    columns = ['Lodging Name', 'Destination', 'Duration']
    results_table = DataFrame(duration_results, columns=columns)
    results_table.to_csv(results_path, index=False)

    rankings_path = join(target_folder, 'rankings.csv')
    columns = ['Lodging Name', 'Total Time']
    rankings_table = DataFrame(rankings, columns=columns)
    rankings_table.to_csv(rankings_path, index=False)

    # Required print statement for crosscompute
    print("rankings_table_path = {0}".format(rankings_path))
    print("results_table_path = {0}".format(results_path))

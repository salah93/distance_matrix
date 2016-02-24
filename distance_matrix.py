import geopy
import json
import urllib
from argparse import ArgumentParser
from invisibleroads_macros.disk import make_folder
from os.path import join
from pandas import DataFrame

# make a table that ranks from least total time to most listing only 
#   lodgings and total time in addition to existing table
def run(target_folder, origins_path, destinations_path, mode):
    results_path = join(target_folder, 'results.csv')
    rankings_path = join(target_folder, 'rankings.csv')
    log_path = join(target_folder, 'log_results.txt')
    geomap_path = join(target_folder, 'geomap.csv')

    origins = load_unique_lines(origins_path)
    destinations = load_unique_lines(destinations_path)

    # Use google's distancematrix api
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?"
    url_params = {"origins": "|".join(origins),
            "mode": mode,
            "destinations": "|".join(destinations),
            "language": "en-EN",
            "units": "imperial"}
    url += urllib.urlencode(url_params)
    url_output = urllib.urlopen(url)
    json_result = json.load(url_output)

    # TODO: Check status of each output -> result.rows[i].elements[i].status
    origin_addresses = json_result['origin_addresses']
    destination_addresses = json_result['destination_addresses']
    origin_to_destination_stats = zip(origin_addresses, json_result['rows'])
    
    google_geo = geopy.GoogleV3()
    coordinates = [google_geo.geocode(address) 
            for address in origin_addresses]
    coordinates.extend([google_geo.geocode(address)
            for address in destination_addresses])
    fillcolor = ['red' for i in origin_addresses]
    fillcolor.extend(['blue' for i in destination_addresses])
    radius_in_pixels = [20 for i in coordinates]
    names = [name for name in origin_addresses]
    names.extend([name for name in destination_addresses])
    
    geomap_df = DataFrame()
    geomap_df['name'] = names
    geomap_df['latitude'] = [coord.latitude for coord in coordinates]
    geomap_df['longitude'] = [coord.longitude for coord in coordinates]
    geomap_df['fill color'] = fillcolor
    geomap_df['radius in pixels'] = radius_in_pixels
    geomap_df.to_csv(geomap_path, index=False)

    duration_results = []
    log = []
    for lodging_name, lodging_info in origin_to_destination_stats:
        # get duration to each destination from current lodging
        curr_time = [destination['duration']['value']
            for destination in lodging_info['elements']]
        total_duration = sum(curr_time)
        curr_time.append(total_duration)

        # Rank lodgings by minimum total_duration
        for i, old_lodging_and_time in enumerate(duration_results):
            old_time = old_lodging_and_time[1]
            # total_duration is located at end of each list
            if curr_time[-1] < old_time[-1]:
                duration_results.insert(i, (lodging_name, curr_time))
                break
        else:
            duration_results.append((lodging_name, curr_time))

    # Output results
    log.append("Rankings:")
    log.extend([str((origin, time[-1])) for origin, time in duration_results])
    log_output = "\n".join(log)
    print(log_output)
    with open(log_path, 'w') as f:
        f.write(log_output)
    destination_addresses.append('TOTAL')
    results_table = DataFrame.from_items(duration_results)
    results_table.index = destination_addresses
    results_table.to_csv(results_path)

    rankings_table = DataFrame(index=[x[0] for x in duration_results])
    rankings_table['total time'] = [x[1][-1] for x in duration_results]
    rankings_table.to_csv(rankings_path)

    # Required print statement for crosscompute
    print("results_table_path = {0}".format(results_path))
    print("rankings_table_path = {0}".format(rankings_path))
    print("results_text_path = {0}".format(log_path))
    print("points_geotable_path = {0}".format(geomap_path))

def load_unique_lines(source_path):
    if not source_path:
        return []
    source_text = open(source_path, 'r').read().strip()
    lines = set(
        [normalize_line(x) for x in source_text.splitlines()])
    return sorted([x for x in lines if x])

def normalize_line(x):
    x = x.rstrip(',;')
    return x.strip()

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--target_folder', nargs='?', default='results',
            type=make_folder, metavar='FOLDER')
    parser.add_argument('--origins_text_path', '-O',
            type=str, metavar='PATH', required=True)
    parser.add_argument('--destinations_text_path', '-D',
            type=str, metavar='PATH', required=True)
    parser.add_argument('--mode_text_path', '-M',
            type=str, metavar='PATH', default='driving',
            choices=['driving', 'walking', 'cycling'])
    args = parser.parse_args()
    run(
        args.target_folder,
        args.origins_text_path,
        args.destinations_text_path,
        args.mode_text_path)

import json
import urllib
from argparse import ArgumentParser
from invisibleroads_macros.disk import make_folder
from os.path import join
from pandas import DataFrame

def run(target_folder, origins_path, destinations_path, mode):
    log_path = join(target_folder, 'log_results.txt')
    csv_path = join(target_folder, 'results.csv')

    origins = load_unique_lines(origins_path)
    destinations = load_unique_lines(destinations_path)
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?"
    url_params = {"origins": "|".join(origins), "mode": mode, "destinations": "|".join(destinations), "language": "en-EN", "units": "imperial"}
    url += urllib.urlencode(url_params)
    url_output = urllib.urlopen(url)
    json_result = json.load(url_output)

    # TODO: Check status of each output -> result.rows[i].elements[i].status
    origin_addresses = json_result['origin_addresses']
    destination_addresses = json_result['destination_addresses']
    origin_stats = zip(origin_addresses, json_result['rows'])
    duration_results = {}
    log = []
    for base, base_info in origin_stats:
        duration_results[base] = []
        log.append("base: {0}".format(str(base)))
        destinations = zip(destination_addresses, base_info['elements'])
        for dest, dest_stats in destinations:
            log.append("duration to {0}: {1}".format(
                dest, dest_stats['duration']['value']))
            duration_results[base].append(dest_stats['duration']['value'])
        total_duration = sum([destination['duration']['value'] 
            for destination in base_info['elements']])
        log.append("total duration from {0}: {1}\n".format(base, total_duration))
        duration_results[base].append(total_duration)
    # TODO: find min duration
    #min_duration = 
    log_string = "\n".join(log)
    with open(log_path,'w') as f:
        f.write(log_string)
    destination_addresses.append('TOTAL')
    results_table = DataFrame(duration_results, index=destination_addresses)
    results_table.to_csv(csv_path)

    print("results_table_path = " + csv_path)
    print("log_text_path = " + log_path)

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
            type=str, metavar='PATH', default='driving', choices=['driving', 'walking', 'cycling'])
    args = parser.parse_args()
    run(
        args.target_folder,
        args.origins_text_path,
        args.destinations_text_path,
        args.mode_text_path)

import json
import urllib
from argparse import ArgumentParser
from invisibleroads_macros.disk import make_folder
from os.path import join
from pandas import DataFrame


def run(target_folder, origins_path, destinations_path, mode):
    csv_path = join(target_folder, 'results.csv')
    log_path = join(target_folder, 'log_results.txt')

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
    duration_results = []
    log = []
    for lodging_name, lodging_info in origin_to_destination_stats:
        # get duration to each destination from current lodging
        curr_time = [destination['duration']['value']
            for destination in lodging_info['elements']]
        total_duration = sum(curr_time)
        curr_time.append(total_duration)
        # Log information
        capture_output(log, lodging_name, zip(destination_addresses, curr_time))

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
    log_output = "\n".join(log)
    print(log_output)
    with open(log_path, 'w') as f:
        f.write(log_output)
    destination_addresses.append('TOTAL')
    results_table = DataFrame.from_items(duration_results)
    results_table.index = destination_addresses
    results_table.to_csv(csv_path)

    # Required print statement for crosscompute
    print("results_table_path = {0}".format(csv_path))
    print("results_text_path = {0}".format(log_path))

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

def capture_output(log, lodging_name, zip_list):
    log.append("\nLodging: {0}".format(lodging_name))
    log.append("{:50} | {:5}".format("Destination", "Time(s)"))
    log.append("-"*50)
    for destination, time in zip_list:
        log.append("{:50} | {:5}".format(destination, time))

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

import argparse
import json
from os.path import exists

import requests

vm_ip = "192.168.101.115"
broker_port = "9090"

# sample url: ngsi-ld/v1/entities
link_nav = "/"
req_url = "http://" + vm_ip + ":" + broker_port + link_nav

parser = argparse.ArgumentParser(
    description="Scorpio Broker JSON-LD REST API Tester Application"
)
parser.add_argument(
    "rest_method",
    type=int,
    help="REST Method Type: [1] POST [2] GET [3] DELETE [4] PUT",
)
parser.add_argument(
    "file_number",
    type=int,
    help="File number of JSON file as input for body and URL file as URL for request",
)
cmd_args = parser.parse_args()


def check_file_exists(fileName):
    status = exists(fileName)
    return status


def url_reader(fileName):
    url_line = ""
    with open(fileName) as f:
        for read_line in f:
            url_line += read_line
            url_line = url_line.rstrip()
    f.close()
    if "\n" in url_line:
        print("\nERROR: Possible Malformed URL !")
    print("\nREST Method to URL : " + url_line)
    return url_line


def main():
    if cmd_args.rest_method == 1:
        print("Working with REST POST method...")
        json_file = str(cmd_args.file_number) + ".json"
        url_file = str(cmd_args.file_number) + ".txt"
        post_data = {}
        post_req_headers =  {"Content-Type":"application/json"}
        if check_file_exists(json_file):
            if check_file_exists(url_file):
                with open(json_file, "r") as f:
                    post_data = json.load(f)
                    print("\nPOSTing Data Content:\n")
                    print(post_data)
                post_req_url = url_reader(url_file)
                post_response = requests.post(post_req_url, data = post_data, headers = post_req_headers)
                post_response_data = post_response.content.decode("ascii")
                post_response_code = str(post_response.status_code)
                print("\nResponse POST Status Code: " + post_response_code)
                print("\nResponse POST: " + post_response_data)
            else:
                print("ERROR: URL input file: " + url_file + " missing!")
        else:
            print("ERROR: JSON input file: " + json_file + " not found!")

    elif cmd_args.rest_method == 2:
        print("Working with REST GET method...")
        url_file = str(cmd_args.file_number) + ".txt"
        if check_file_exists(url_file):
            get_req = url_reader(url_file)
            response_get = requests.get(get_req)
            response_json = response_get.content.decode("ascii")
            print("Response GET: " + response_json)
            response_output = open("response.json", "w")
            response_output.writelines(response_json)
            response_output.close()

        else:
            print("ERROR: URL input file: " + url_file + " missing!")

    elif cmd_args.rest_method == 3:
        print("Functionality DELETE not yet Ready!")
        # response_delete = requests.delete(req_url)
        # print("Response DELETE: " + response_delete.content)

    elif cmd_args.rest_method == 4:
        print("Functionality PUT not yet Ready!")
        # response_put = requests.put(req_url)
        # print("Response PUT: " + response_put.content)

    else:
        print("ERROR: Invalid REST Method Request")
        print("Allowed REST Method Type: [1] POST [2] GET [3] DELETE [4] PUT")


if __name__ == "__main__":
    main()

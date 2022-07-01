import argparse
import json
from os.path import exists

parser = argparse.ArgumentParser(description="Scorpio Broker JSON-LD Tester")
parser.add_argument(
    "rest_method",
    type=int,
    help="REST Method Type: [1] POST [2] GET [3] DELETE [4] PUT",
)
parser.add_argument("file_number", type=int, help="File number of JSON file as input")
cmd_args = parser.parse_args()


def check_file_exists(fileName):
    status = exists(fileName)
    return status


def main():
    if cmd_args.rest_method == 1:
        print("Working with REST POST method...")
        json_file = str(cmd_args.file_number) + ".JSON"
        if check_file_exists(json_file):
            with open(json_file, "r") as f:
                post_data = json.load(f)
                print(post_data)
                # response_post = requests.post(req_url)
                # print("Response POST: " + response_post.content)
        else:
            print("ERROR: JSON input file: " + json_file + " not found!")
    else:
        print("ERROR: Invalid REST Method Request")
        print("Allowed REST Method Type: [1] POST [2] GET [3] DELETE [4] PUT")


if __name__ == "__main__":
    main()

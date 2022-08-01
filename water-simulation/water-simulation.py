#!/usr/bin/env python

import argparse
import json

from kbscenariotools.argparse import add_default_args
from kbscenariotools.endpoint import ScenarioManagerEndpoint
from tqdm import tqdm

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter,
    description="""
Import helper for water management simulation data.

The script takes the json file with a structure like this and calls the scenario manager API to create the NGSI-LD entities:

{
    "version": "wntr-0.4.1",
    "name": "networks/some-network.inp",
    "options": { ... },
    "curves": [ ... ],
    "patterns": [ ... ],
    "nodes": [
        {
            "name": "12345",
            "node_type": "junction",
            ...
        },{
            ...
        }
    ],
    "links": [
        {
            "name": "Pipe1",
            "link_type": "Pipe",
            ...
        }, {
            ...
        }
    ]
}

Currently, only the nodes and links are converted, and a network grouping all the data is created using the --network-name parameter.

""",
)
add_default_args(parser, scenario_id=True)
parser.add_argument(
    "input_json",
    help="Input file from the simulation (JSON)",
    type=str,
    action="store",
    metavar="INPUT_JSON",
)
parser.add_argument(
    "--network-name",
    help="Name of the WaterNetwork to create (default: WaterNetwork1)",
    type=str,
    action="store",
    default="WaterNetwork1",
)
parser.add_argument(
    "--prefix",
    help='Prefix for NGSI identifies (Prefix "Test" makes "urn:ngsi:Pipe:TestPipe42" from "Pipe42", default: None)',
    type=str,
    action="store",
    default="",
)
args = parser.parse_args()
scenario_id = args.scenario

endpoint = ScenarioManagerEndpoint.from_args(args)

# Parse the input file
with open(args.input_json, "r") as f:
    data = json.load(f)
junctions = list(filter(lambda node: node["node_type"] == "Junction", data["nodes"]))
tanks = list(filter(lambda node: node["node_type"] == "Tank", data["nodes"]))
reservoirs = list(filter(lambda node: node["node_type"] == "Reservoir", data["nodes"]))
pipes = list(filter(lambda link: link["link_type"] == "Pipe", data["links"]))
pumps = list(filter(lambda link: link["link_type"] == "Pump", data["links"]))
curves = list(data["curves"])
patterns = list(data["patterns"])
options = data["options"]
node_id_type_map = {node["name"]: node["node_type"] for node in data["nodes"]}
link_id_type_map = {link["name"]: link["link_type"] for link in data["links"]}
curve_id_type_map = {curve["name"]: curve["curve_type"] for curve in data["curves"]}

print("-[ Import Results ]-----------------")
print(f"{len(junctions):6} junctions")
print(f"{len(tanks):6} tanks")
print(f"{len(reservoirs):6} reservoirs")
print(f"{len(pipes):6} pipes")
print(f"{len(pumps):6} pumps")
print(f"{len(curves):6} curves")
print(f"{len(patterns):6} patterns")
print("     1 network")
total = (
    len(junctions)
    + len(tanks)
    + len(reservoirs)
    + len(pipes)
    + len(pumps)
    + len(curves)
    + len(patterns)
    + 1
)
print("------------------------------------")
print(f"{total:6} models total\n")
if any(link["link_type"] == "Valve" for link in data["links"]):
    print("WARNING: Data contains valves, but this script does not support them (yet)!")

# Check the scenario exists:
# status, res = endpoint.get(f"/scenarios/{scenario_id}")
# assert status == 200, f"Scenario does not exist: {scenario_id}"
#print(f"Using scenario {scenario_id}: {res['name']}\n")


def make_urn(id, type_=None, id_type_map=None):
    if type_ is None:
        if id_type_map is None:
            raise ValueError("id_type_map cannot be None.")
        type_ = id_type_map[id]
    return f"urn:ngsi:{type_}:{args.prefix}{id}"


def set_urn(data_in, data_out, id_in, id_out=None, id_type_map=None):
    if id_in in data_in and data_in[id_in] is not None:
        urn = make_urn(data_in[id_in], id_type_map=id_type_map)
        data_out[id_out if id_out is not None else id_in] = urn


def set_if_not_null(data_in, data_out, id_in, id_out=None, conv=lambda x: x):
    if id_in in data_in and data_in[id_in] is not None:
        data_out[id_out if id_out is not None else id_in] = conv(data_in[id_in])


def set_data_series(data_in, data_out, id_in, index, id_out=None):
    if (
        id_in in data_in
        and type(data_in[id_in]) == list
        and all((isinstance(l, list) and len(l) == 2) for l in data_in[id_in])
    ):
        data_out[id_out if id_out is not None else id_in] = [
            l[index] for l in data_in[id_in]
        ]


def set_curveType(data_in, data_out, id_in, id_out=None):
    if id_in in data_in and data_in[id_in] is not None:
        curveType_dict = {
            "HEAD": "FLOW-HEAD",
            "EFFICIENCY": "FLOW-EFFICIENCY",
            "HEADLOSS": "FLOW-HEADLOSS",
            "VOLUME": "LEVEL-VOLUME",
        }
        if data_in[id_in] in curveType_dict.keys():
            data_out[id_out if id_out is not None else id_in] = curveType_dict[
                data_in[id_in]
            ]
    else:
        raise ValueError("Wrong curve type for curve {}".format(data_in["name"]))


def set_geojson_point(data_in, data_out, id_in, id_out=None):
    if id_in in data_in and type(data_in[id_in]) == list and len(data_in[id_in]) == 2:
        data_out[id_out if id_out is not None else id_in] = {
            "type": "Point",
            "coordinates": data_in[id_in],
        }


def observe(data):
    return {"value": data}


def set_node_data(data_in, data_out):
    set_geojson_point(data_in, data_out, "coordinates", "location")
    set_if_not_null(data_in, data_out, "initial_quality", "initialQuality", observe)
    set_if_not_null(data_in, data_out, "name")
    set_if_not_null(data_in, data_out, "tag")


def set_link_data(data_in, data_out):
    set_urn(data_in, data_out, "start_node_name", "startsAt", node_id_type_map)
    set_urn(data_in, data_out, "end_node_name", "endsAt", node_id_type_map)
    data_out["initialStatus"] = data_in["initial_status"].upper()  # required
    set_if_not_null(data_in, data_out, "name")
    set_if_not_null(data_in, data_out, "tag")
    # Fields which should go to simulation metadata
    #   - initial_setting


def set_curve_data(data_in, data_out):
    if "curve_type" in data_in and data_in["curve_type"] is not None:
        curve_type_dict = {
            "HEAD": "FLOW-HEAD",
            "EFFICIENCY": "FLOW-EFFICIENCY",
            "HEADLOSS": "FLOW-HEADLOSS",
            "VOLUME": "LEVEL-VOLUME",
        }
        data_out["curveType"] = curve_type_dict[data_in["curve_type"]]
    else:
        raise ValueError(
            "curve_type {ct} not valid. Must be one HEAD, EFFICIENCY, HEADLOSS of VOLUME".format(
                ct=str(data_in["curve_type"])
            )
        )
    set_if_not_null(data_in, data_out, "dataProvider")
    set_if_not_null(data_in, data_out, "dateCreated")
    set_if_not_null(data_in, data_out, "dateModified")
    set_if_not_null(data_in, data_out, "description")
    set_if_not_null(data_in, data_out, "source")
    set_data_series(data_in, data_out, "points", 0, "xData")
    set_data_series(data_in, data_out, "points", 1, "yData")


def set_pattern_data(data_in, data_out, options):
    set_if_not_null(data_in, data_out, "multipliers")
    set_if_not_null(options["time"], data_out, "pattern_timestep", "timeStep")
    set_if_not_null(
        options["time"], data_out, "pattern_start", "startTime"
    )  # TODO: choose a suitable time format
    set_if_not_null(data_in, data_out, "dataProvider")
    set_if_not_null(data_in, data_out, "dateCreated")
    set_if_not_null(data_in, data_out, "dateModified")
    set_if_not_null(data_in, data_out, "description")
    set_if_not_null(data_in, data_out, "source")

def dump_response(data):
    dump_file = open("request_data.json", "a")
    dump_file.write("\n------------------ RESPONSE START ----------------------\n")
    binary_data = data.encode('ascii')
    decoded_data = binary_data.decode("ascii")
    #json_formatted_response_data = json.dumps(decoded_data, indent = 4) 
    dump_file.write(str(decoded_data))
    dump_file.write("\n------------------ RESPONSE END ----------------------\n")
    dump_file.close()

def dump_request(data):
    dump_file = open("request_data.json", "a")
    dump_file.write("\n------------------ REQUEST START ----------------------\n")
    json_formatted_request_data = json.dumps(data, indent = 4) 
    dump_file.write(str(json_formatted_request_data))
    dump_file.write("\n------------------ REQUEST END ----------------------\n")
    dump_file.close()

def upload_model(data):
    # context_entry = {"@context": [
    #     "https://raw.githubusercontent.com/smart-data-models/dataModel.WaterDistributionManagementEPANET/master/context.jsonld"
    # ]}
    # data_json = json.dumps(data)
    # data_json.dumps(context_entry)
    data["@context"] = "https://raw.githubusercontent.com/smart-data-models/dataModel.WaterDistributionManagementEPANET/master/context.jsonld"
    path = f"/ngsi-ld/v1/entities/"
    dump_request(data)
    status, res = endpoint.post(path, data, "application/ld+json")
    if not (200 <= status <= 299):
        print(f"POST {path} failed for {data['id']}")
        print("Request Body:")
        print(json.dumps(data, indent=2))
        print("Response Body:")
        print(res)
        dump_response(res)
        raise RuntimeError(f"Got status code {status} while posting {data['id']}.")


print("Creating models:")
with tqdm(total=total, unit="models") as pbar:
    composed_of = []

    for junction in junctions:
        jdata = {"id": make_urn(junction["name"], "Junction"), "type": "Junction"}
        set_node_data(junction, jdata)
        set_if_not_null(junction, jdata, "elevation")
        set_if_not_null(junction, jdata, "emitter_coefficient", "emitterCoefficient")
        # Fields which should go to simulation metadata
        #   - minimum_pressure
        #   - pressure_exponent
        #   - required_pressure
        composed_of.append(jdata["id"])
        upload_model(jdata)
        pbar.update(1)

    for reservoir in reservoirs:
        rdata = {"id": make_urn(reservoir["name"], "Reservoir"), "type": "Reservoir"}
        set_node_data(reservoir, rdata)
        set_if_not_null(reservoir, rdata, "base_head", "reservoirHead")
        # To be added once we have patterns and curves:
        #   - head_pattern_name
        composed_of.append(rdata["id"])
        upload_model(rdata)
        pbar.update(1)

    for tank in tanks:
        tdata = {"id": make_urn(tank["name"], "Tank"), "type": "Tank"}
        set_node_data(tank, tdata)
        set_if_not_null(tank, tdata, "bulk_coeff", "bulkReactionCoefficient")
        set_if_not_null(tank, tdata, "diameter", "nominalDiameter")
        set_if_not_null(tank, tdata, "elevation")
        set_if_not_null(tank, tdata, "init_level", "initial_level")
        set_if_not_null(tank, tdata, "initial_quality", "initialQuality")
        set_if_not_null(tank, tdata, "max_level", "maxLevel")
        set_if_not_null(tank, tdata, "min_level", "minLevel")
        set_if_not_null(tank, tdata, "min_vol", "minVolume")
        set_if_not_null(tank, tdata, "mixing_fraction", "mixingFraction")
        # Fields which should go to simulation metadata
        #   - overflow (boolean)
        # To be added once we have patterns and curves:
        #   - vol_curve_name
        # Ignored fields:
        #   - mixing_model (quality related, irrelevant for us)
        composed_of.append(tdata["id"])
        upload_model(tdata)
        pbar.update(1)

    for pipe in pipes:
        pdata = {
            "id": make_urn(pipe["name"], "Pipe"),
            "type": "Pipe",
        }
        set_link_data(pipe, pdata)
        set_if_not_null(pipe, pdata, "bulk_coeff", "bulkCoeff")
        set_if_not_null(pipe, pdata, "diameter")
        set_if_not_null(pipe, pdata, "length")
        set_if_not_null(pipe, pdata, "minor_loss", "minorLoss")
        set_if_not_null(pipe, pdata, "roughness")
        set_if_not_null(pipe, pdata, "wall_coeff", "wallCoeff")
        # Ignored Fields:
        #   - check_valve (missing equivalent in the SMD)
        composed_of.append(pdata["id"])
        upload_model(pdata)
        pbar.update(1)

    for pump in pumps:
        pdata = {
            "id": make_urn(pump["name"], "Pump"),
            "type": "Pump",
        }
        set_link_data(pump, pdata)
        set_if_not_null(pump, pdata, "base_speed", "speed")
        set_if_not_null(pump, pdata, "energy_price", "energyPrice")
        # Ignored Fields:
        #   - efficiency (can be computed using effiCurve)
        #   - pump_type (distinction between HeadPump and PowerPump. We only use HeadPump, as PowerPumps are a simplification)
        #   - power (parameter related to PowerPumps, so we can ignore it when assuming HeadPumps)
        # To be added once we have patterns and curves:
        #   - energy_pattern
        #   - pump_curve_name
        #   - speed_pattern_name
        composed_of.append(pdata["id"])
        upload_model(pdata)
        pbar.update(1)

    for curve in curves:
        cdata = {"id": make_urn(curve["name"], "Curve"), "type": "Curve"}
        set_curve_data(curve, cdata)
        composed_of.append(cdata["id"])
        upload_model(cdata)
        pbar.update(1)

    for pattern in patterns:
        pattern_data = {"id": make_urn(pattern["name"], "Pattern"), "type": "Pattern"}
        set_pattern_data(pattern, pattern_data, options)
        composed_of.append(pattern_data["id"])
        upload_model(pattern_data)
        pbar.update(1)

    network = {
        "id": make_urn(args.network_name, "WaterNetwork"),
        "type": "WaterNetwork",
        "isComposedOf": composed_of,
        "description": data["name"] + "\n\n" + data["comment"],
        "name": args.network_name,
    }
    upload_model(network)
    pbar.update(1)

print("Done.")

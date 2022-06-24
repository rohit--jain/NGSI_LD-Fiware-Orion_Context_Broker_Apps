import json

import requests

vm_ip = "192.168.101.115"
broker_port = "9090"
link_nav = "/ngsi-ld/v1/entities"
req_url = "http://" + vm_ip + ":" + broker_port + link_nav

response = requests.get(req_url)

print(response.content)
